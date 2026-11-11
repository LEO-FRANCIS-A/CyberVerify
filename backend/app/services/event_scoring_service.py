import math
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix, brier_score_loss
from sklearn.model_selection import train_test_split

from backend.app.models.schemas import ModelMetadata
from backend.app.database.mongo import get_model_metadata_collection

logger = logging.getLogger(__name__)

# Explicit fallback weights used until adequate labelled data exists
FALLBACK_WEIGHTS = {
    "w_sem": 0.40,
    "w_ent": 0.25,
    "w_temp": 0.15,
    "w_ioc": 0.20,
    "intercept": -0.10
}

# Decay constant lambda for temporal similarity: exp(-lambda * delta_days)
# Half-life of approximately 14 days (lambda ≈ 0.05)
LAMBDA_TEMPORAL = 0.05

def compute_semantic_similarity(article_emb: List[float], centroid: List[float]) -> float:
    """Computes cosine similarity between article embedding and event centroid."""
    if not article_emb or not centroid:
        return 0.0
    vec_a = np.array(article_emb)
    vec_c = np.array(centroid)
    norm_a = np.linalg.norm(vec_a)
    norm_c = np.linalg.norm(vec_c)
    if norm_a == 0 or norm_c == 0:
        return 0.0
    sim = float(np.dot(vec_a, vec_c) / (norm_a * norm_c))
    return max(0.0, min(1.0, sim))

def compute_entity_overlap(article_entities: List[str], event_entities: List[str]) -> float:
    """Computes Jaccard similarity: |A ∩ E| / |A ∪ E|."""
    set_a = {e.lower().strip() for e in article_entities if e}
    set_e = {e.lower().strip() for e in event_entities if e}
    if not set_a or not set_e:
        return 0.0
    intersection = len(set_a.intersection(set_e))
    union = len(set_a.union(set_e))
    return round(intersection / union, 4) if union > 0 else 0.0

def compute_ioc_cve_overlap(
    art_cves: List[str], art_iocs: Dict[str, List[str]],
    ev_cves: List[str], ev_iocs: Dict[str, List[str]]
) -> float:
    """Computes Jaccard overlap across combined IOCs and CVEs."""
    items_a = set(c.upper() for c in art_cves)
    items_e = set(c.upper() for c in ev_cves)
    
    for ioc_type in ["ipv4", "sha256", "md5", "sha1"]:
        items_a.update(art_iocs.get(ioc_type, []))
        items_e.update(ev_iocs.get(ioc_type, []))
        
    if not items_a or not items_e:
        return 0.0
    intersection = len(items_a.intersection(items_e))
    union = len(items_a.union(items_e))
    return round(intersection / union, 4) if union > 0 else 0.0

def compute_temporal_similarity(art_time: Optional[datetime], ev_time: Optional[datetime]) -> float:
    """Computes temporal proximity score S_temp = exp(-lambda * delta_days)."""
    if not art_time or not ev_time:
        return 0.50  # Neutral fallback if timestamp missing
    # Ensure timezone compatibility
    if art_time.tzinfo is None:
        art_time = art_time.replace(tzinfo=timezone.utc)
    if ev_time.tzinfo is None:
        ev_time = ev_time.replace(tzinfo=timezone.utc)
    delta_days = abs((art_time - ev_time).total_seconds()) / 86400.0
    s_temp = math.exp(-LAMBDA_TEMPORAL * delta_days)
    return round(max(0.0, min(1.0, s_temp)), 4)

def calculate_feature_vector(
    article_emb: List[float],
    article_entities: List[str],
    article_cves: List[str],
    article_iocs: Dict[str, List[str]],
    article_time: Optional[datetime],
    event: Dict[str, Any]
) -> Dict[str, float]:
    """Calculates all four core similarity features for an article-event pair."""
    centroid = event.get("embedding_centroid", [])
    ev_entities = event.get("organizations", []) + event.get("threat_actors", []) + event.get("products", [])
    ev_cves = event.get("cves", [])
    ev_iocs = event.get("iocs", {})
    ev_time = event.get("latest_update") or event.get("first_seen")

    s_sem = compute_semantic_similarity(article_emb, centroid)
    s_ent = compute_entity_overlap(article_entities, ev_entities)
    s_ioc = compute_ioc_cve_overlap(article_cves, article_iocs, ev_cves, ev_iocs)
    s_temp = compute_temporal_similarity(article_time, ev_time)

    return {
        "s_sem": s_sem,
        "s_ent": s_ent,
        "s_temp": s_temp,
        "s_ioc": s_ioc
    }

class LogisticRegressionEventScorer:
    """Logistic Regression Event Scoring & Training Pipeline."""
    def __init__(self):
        self.model = LogisticRegression(C=1.0, class_weight="balanced")
        self.is_trained = False
        self.weights = FALLBACK_WEIGHTS.copy()
        self.metrics = {}
        self.confusion_matrix = None

    def predict_score(self, features: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Computes composite event similarity score S_event.
        Uses trained model if available; otherwise uses calibrated fallback configuration.
        """
        if self.is_trained:
            x = np.array([[features["s_sem"], features["s_ent"], features["s_temp"], features["s_ioc"]]])
            prob = float(self.model.predict_proba(x)[0][1])
            return round(prob, 4), self.weights
        else:
            # Fallback linear combination mapped through sigmoid
            w = self.weights
            z = (w["w_sem"] * features["s_sem"] +
                 w["w_ent"] * features["s_ent"] +
                 w["w_temp"] * features["s_temp"] +
                 w["w_ioc"] * features["s_ioc"] +
                 w["intercept"])
            prob = 1.0 / (1.0 + math.exp(-z))
            return round(prob, 4), w

    def train_on_pairs(
        self,
        pairs: List[Dict[str, Any]],
        test_size: float = 0.20
    ) -> Dict[str, Any]:
        """Trains logistic regression model on article-event feature pairs."""
        if len(pairs) < 10:
            logger.warning(f"Insufficient training pairs ({len(pairs)} < 10). Retaining fallback.")
            return {"status": "INSUFFICIENT_DATA", "samples": len(pairs)}

        x = []
        y = []
        for p in pairs:
            x.append([p["s_sem"], p["s_ent"], p["s_temp"], p["s_ioc"]])
            y.append(p["label"])

        x_arr = np.array(x)
        y_arr = np.array(y)

        x_train, x_test, y_train, y_test = train_test_split(
            x_arr, y_arr, test_size=test_size, random_state=42, stratify=y_arr if len(set(y_arr)) > 1 else None
        )

        self.model.fit(x_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(x_test)
        y_prob = self.model.predict_proba(x_test)[:, 1]

        coefs = self.model.coef_[0]
        self.weights = {
            "w_sem": round(float(coefs[0]), 4),
            "w_ent": round(float(coefs[1]), 4),
            "w_temp": round(float(coefs[2]), 4),
            "w_ioc": round(float(coefs[3]), 4),
            "intercept": round(float(self.model.intercept_[0]), 4)
        }

        self.metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "brier_score": round(float(brier_score_loss(y_test, y_prob)), 4)
        }
        self.confusion_matrix = confusion_matrix(y_test, y_pred).tolist()

        logger.info(f"Logistic Regression trained on {len(pairs)} pairs. F1: {self.metrics['f1']}, Weights: {self.weights}")
        return {
            "status": "SUCCESS",
            "samples": len(pairs),
            "weights": self.weights,
            "metrics": self.metrics,
            "confusion_matrix": self.confusion_matrix
        }

# Global singleton scorer instance
global_event_scorer = LogisticRegressionEventScorer()
