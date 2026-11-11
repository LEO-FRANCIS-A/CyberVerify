import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi, BM25Plus
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Global model cache to avoid repeated reloading
_SBERT_MODEL = None
_SBERT_LOAD_ATTEMPTED = False

def get_sbert_model():
    """Lazily loads SentenceTransformer model with fallback indicator."""
    global _SBERT_MODEL, _SBERT_LOAD_ATTEMPTED
    if _SBERT_LOAD_ATTEMPTED:
        return _SBERT_MODEL
        
    _SBERT_LOAD_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SBERT model: all-MiniLM-L6-v2 (CPU optimized)...")
        _SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        logger.info("SBERT model successfully initialized.")
    except Exception as e:
        logger.warning(f"SBERT model loading failed ({e}). Utilizing TF-IDF fallback.")
        _SBERT_MODEL = None
    return _SBERT_MODEL

def compute_text_embedding(text: str, fallback_corpus: Optional[List[str]] = None) -> List[float]:
    """
    Computes dense vector embedding for text.
    Uses SBERT if available; falls back to TF-IDF vectorization.
    """
    model = get_sbert_model()
    if model is not None:
        try:
            emb = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return emb.tolist()
        except Exception as e:
            logger.debug(f"SBERT encoding exception: {e}")

    # TF-IDF Fallback
    corpus = fallback_corpus if fallback_corpus else [text, "cybersecurity vulnerability data breach incident patch"]
    if text not in corpus:
        corpus = [text] + corpus
    vec = TfidfVectorizer(max_features=384)
    matrix = vec.fit_transform(corpus)
    emb = matrix[0].toarray()[0]
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb.tolist()

class BM25EventIndex:
    """Fast BM25 Candidate Retrieval Index for Events."""
    def __init__(self, events: List[Dict[str, Any]]):
        self.events = events
        self.doc_ids = []
        tokenized_corpus = []
        
        for ev in events:
            # Index title, description, entities, and CVEs
            text = f"{ev.get('title', '')} {ev.get('description', '')} "
            text += " ".join(ev.get('cves', [])) + " "
            text += " ".join(ev.get('organizations', [])) + " "
            text += " ".join(ev.get('threat_actors', []))
            
            tokens = text.lower().split()
            tokenized_corpus.append(tokens if tokens else ["incident"])
            self.doc_ids.append(ev.get("event_id"))
            
        self.bm25 = BM25Plus(tokenized_corpus) if tokenized_corpus else None

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        if not self.bm25 or not self.doc_ids:
            return []
        tokens = query_text.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0.0:
                results.append((self.doc_ids[idx], float(scores[idx])))
        return results

def retrieve_candidate_events(
    article_text: str,
    article_cves: List[str],
    events: List[Dict[str, Any]],
    top_k: int = 8
) -> List[Dict[str, Any]]:
    """
    Two-stage candidate retrieval combining BM25 and semantic search.
    Ensures scalability by avoiding comparing new articles against every historical event.
    """
    if not events:
        return []

    # 1. Direct CVE Matching Candidates (Instant high priority)
    cve_matched_ids = set()
    if article_cves:
        cve_set = set(article_cves)
        for ev in events:
            ev_cves = set(ev.get("cves", []))
            if not cve_set.isdisjoint(ev_cves):
                cve_matched_ids.add(ev.get("event_id"))

    # 2. BM25 Retrieval
    bm25_index = BM25EventIndex(events)
    bm25_hits = bm25_index.query(article_text, top_k=top_k)
    bm25_ids = {hit[0] for hit in bm25_hits}

    # 3. Dense Semantic Centroid Retrieval
    art_emb = compute_text_embedding(article_text)
    dense_scores = []
    for ev in events:
        centroid = ev.get("embedding_centroid")
        if centroid:
            sim = float(np.dot(art_emb, centroid) / (np.linalg.norm(art_emb) * np.linalg.norm(centroid) + 1e-9))
            dense_scores.append((ev.get("event_id"), sim))

    dense_scores.sort(key=lambda x: x[1], reverse=True)
    dense_ids = {item[0] for item in dense_scores[:top_k] if item[1] > 0.25}

    # Merge and deduplicate candidates
    all_candidate_ids = cve_matched_ids.union(bm25_ids).union(dense_ids)
    
    event_map = {ev.get("event_id"): ev for ev in events}
    selected_events = [event_map[eid] for eid in all_candidate_ids if eid in event_map]
    return selected_events[:top_k]
