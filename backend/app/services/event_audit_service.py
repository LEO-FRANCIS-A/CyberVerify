import uuid
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timezone
from sklearn.cluster import HDBSCAN

from backend.app.models.schemas import EventAuditLog
from backend.app.database.mongo import (
    get_events_collection, get_articles_collection, get_event_audit_logs_collection
)
from backend.app.services.retrieval_service import compute_text_embedding

logger = logging.getLogger(__name__)

async def run_hdbscan_audit() -> EventAuditLog:
    """
    Executes a comprehensive HDBSCAN diagnostic audit across all ingested articles and events.
    Identifies cluster fragmentation, potential merges, splits, and outliers.
    """
    audit_id = f"aud_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)
    
    articles_col = get_articles_collection()
    events_col = get_events_collection()
    
    articles = await articles_col.find({"assigned_event_id": {"$ne": None}}).to_list(length=500)
    events = await events_col.find({"event_status": "ACTIVE"}).to_list(length=100)

    if len(articles) < 4:
        logger.info(f"Insufficient articles for HDBSCAN audit ({len(articles)} < 4).")
        log = EventAuditLog(
            audit_id=audit_id,
            timestamp=now,
            total_events_audited=len(events),
            total_articles_audited=len(articles),
            clusters_identified=0,
            outliers_detected=0,
            recommendations=["Insufficient article density for unsupervised HDBSCAN clustering."]
        )
        return log

    # Generate embeddings matrix
    embeddings = []
    valid_articles = []
    for art in articles:
        emb = compute_text_embedding(f"{art.get('title', '')}. {art.get('content', '')[:300]}")
        embeddings.append(emb)
        valid_articles.append(art)

    x = np.array(embeddings)
    # Normalize rows for cosine metric
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    x_norm = x / norms

    # Run HDBSCAN with cosine metric
    min_size = max(2, min(5, len(valid_articles) // 3))
    clusterer = HDBSCAN(min_cluster_size=min_size, metric="euclidean", copy=True)
    labels = clusterer.fit_predict(x_norm)

    unique_clusters = set(labels) - {-1}
    outlier_count = int(np.sum(labels == -1))

    # Map articles by cluster
    cluster_to_articles: Dict[int, List[Dict[str, Any]]] = {}
    for idx, label in enumerate(labels):
        cluster_to_articles.setdefault(int(label), []).append(valid_articles[idx])

    potential_merges = []
    potential_splits = []
    recommendations = []

    # 1. Detect Potential Merges (Multiple distinct event IDs in the same cluster)
    for c_id, arts in cluster_to_articles.items():
        if c_id == -1:
            continue
        event_ids = set(a.get("assigned_event_id") for a in arts if a.get("assigned_event_id"))
        if len(event_ids) > 1:
            # Check CVE consistency before recommending merge
            all_cves = set()
            disjoint_conflict = False
            for a in arts:
                a_cves = set(a.get("cves", []))
                if all_cves and a_cves and all_cves.isdisjoint(a_cves):
                    disjoint_conflict = True
                    break
                all_cves.update(a_cves)

            merge_item = {
                "hdbscan_cluster_id": c_id,
                "event_ids": list(event_ids),
                "article_count": len(arts),
                "is_cve_consistent": not disjoint_conflict,
                "note": "Events co-occur in dense semantic cluster." if not disjoint_conflict else "Merge blocked by disjoint CVE consistency rules."
            }
            potential_merges.append(merge_item)
            if not disjoint_conflict:
                recommendations.append(f"Consider evaluating merge for Events {list(event_ids)} (Cluster {c_id}).")

    # 2. Detect Potential Splits (Single event fractured across multiple non-noise clusters)
    event_to_clusters: Dict[str, Set[int]] = {}
    for idx, label in enumerate(labels):
        if label != -1:
            eid = valid_articles[idx].get("assigned_event_id")
            if eid:
                event_to_clusters.setdefault(eid, set()).add(int(label))

    for eid, c_set in event_to_clusters.items():
        if len(c_set) > 1:
            split_item = {
                "event_id": eid,
                "fractured_clusters": list(c_set),
                "note": f"Articles of Event {eid} fractured across {len(c_set)} distinct semantic clusters."
            }
            potential_splits.append(split_item)
            recommendations.append(f"Event {eid} exhibits multi-topic divergence across clusters {list(c_set)}.")

    audit_log = EventAuditLog(
        audit_id=audit_id,
        timestamp=now,
        total_events_audited=len(events),
        total_articles_audited=len(valid_articles),
        clusters_identified=len(unique_clusters),
        outliers_detected=outlier_count,
        potential_merges=potential_merges,
        potential_splits=potential_splits,
        recommendations=recommendations or ["Clustering alignment is optimal; no urgent merges/splits required."]
    )

    audit_col = get_event_audit_logs_collection()
    await audit_col.insert_one(audit_log.model_dump())
    logger.info(f"HDBSCAN Audit {audit_id} completed: {len(unique_clusters)} clusters, {outlier_count} outliers, {len(potential_merges)} potential merges.")
    return audit_log
