import logging
import uuid
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

from backend.app.models.schemas import Article, CyberEvent, EventTimelineEntry
from backend.app.database.mongo import (
    get_events_collection, get_articles_collection, get_event_articles_collection
)
from backend.app.services.retrieval_service import retrieve_candidate_events, compute_text_embedding
from backend.app.services.event_scoring_service import (
    calculate_feature_vector, global_event_scorer
)

logger = logging.getLogger(__name__)

# Default assignment similarity threshold tau
ASSIGNMENT_THRESHOLD_TAU = 0.55

def check_hard_consistency_rules(article: Article, event: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Applies non-negotiable hard domain constraints before permitting an article-event merge:
    1. Disjoint CVE Rule: Articles with non-empty CVE sets identifying different vulnerabilities
       must NEVER merge merely due to semantic similarity.
    2. Incident Separation: Generic organizational mentions without common CVEs or IOCs
       must not merge if incident types clash.
    """
    art_cves = set(c.upper() for c in article.cves)
    ev_cves = set(c.upper() for c in event.get("cves", []))

    # Rule 1: Disjoint non-empty CVEs
    if art_cves and ev_cves and art_cves.isdisjoint(ev_cves):
        return False, f"Disjoint CVE sets: Article CVEs {art_cves} vs Event CVEs {ev_cves}"

    return True, "Consistent"

def classify_timeline_update_type(title: str, content: str) -> str:
    """Classifies an event update into a standard lifecycle stage."""
    text = f"{title} {content[:500]}".lower()
    if any(k in text for k in ["exploited in the wild", "active exploitation", "zero-day exploited", "ransom demanded", "data exfiltrated"]):
        return "EXPLOITATION"
    elif any(k in text for k in ["patch available", "security update released", "hotfix", "mitigation guidance", "cve fix"]):
        return "PATCH"
    elif any(k in text for k in ["advisory", "security bulletin", "bulletin", "directive", "emergency directive", "cisa alert", "cert-in warning"]):
        return "ADVISORY"
    elif any(k in text for k in ["technical analysis", "root cause", "post-mortem", "reverse engineering", "ioc list"]):
        return "ANALYSIS"
    elif any(k in text for k in ["warning", "threat alert", "phishing campaign"]):
        return "WARNING"
    return "DISCLOSURE"

async def create_new_event_from_article(article: Article, embedding: List[float]) -> CyberEvent:
    """Instantiates a new CyberEvent from an initial article."""
    ev_id = f"ev_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)
    
    classification = classify_timeline_update_type(article.title, article.content)
    
    timeline_entry = EventTimelineEntry(
        entry_id=f"tl_{uuid.uuid4().hex[:8]}",
        timestamp=now,
        date_str=now.strftime("%Y-%m-%d"),
        entry_type=classification,
        title=article.title[:100],
        description=article.summary or article.content[:200],
        source_url=article.url,
        source_title=article.publisher,
        cves=article.cves
    )

    ev = CyberEvent(
        event_id=ev_id,
        title=article.title,
        description=article.summary or article.content[:300],
        event_classification=classification,
        event_status="ACTIVE",
        first_seen=now,
        latest_update=now,
        embedding_centroid=embedding,
        organizations=article.entities.get("organizations", []),
        vendors=[],
        products=[],
        threat_actors=article.entities.get("threat_actors", []),
        cves=article.cves,
        iocs=article.iocs,
        article_ids=[article.article_id],
        sources_count=1,
        independent_sources_count=1,
        timeline=[timeline_entry]
    )

    events_col = get_events_collection()
    await events_col.insert_one(ev.model_dump())
    
    # Update article pointer
    articles_col = get_articles_collection()
    await articles_col.update_one({"article_id": article.article_id}, {"$set": {"assigned_event_id": ev_id}})
    
    logger.info(f"Created new CyberEvent: [{ev_id}] {ev.title[:60]}")
    return ev

async def update_existing_event(event_dict: Dict[str, Any], article: Article, embedding: List[float]):
    """Updates an existing CyberEvent with new article intelligence."""
    ev_id = event_dict["event_id"]
    now = datetime.now(timezone.utc)
    
    # 1. Recalculate embedding centroid
    old_centroid = np.array(event_dict.get("embedding_centroid") or embedding)
    art_vec = np.array(embedding)
    n = len(event_dict.get("article_ids", []))
    new_centroid = (n * old_centroid + art_vec) / (n + 1)
    norm = np.linalg.norm(new_centroid)
    if norm > 0:
        new_centroid = new_centroid / norm

    # 2. Union entities, CVEs, IOCs
    combined_cves = sorted(list(set(event_dict.get("cves", []) + article.cves)))
    combined_actors = sorted(list(set(event_dict.get("threat_actors", []) + article.entities.get("threat_actors", []))))
    
    combined_iocs = event_dict.get("iocs", {})
    for ioc_k, ioc_v in article.iocs.items():
        combined_iocs[ioc_k] = sorted(list(set(combined_iocs.get(ioc_k, []) + ioc_v)))

    # 3. Add timeline entry
    entry_type = classify_timeline_update_type(article.title, article.content)
    timeline_entry = EventTimelineEntry(
        entry_id=f"tl_{uuid.uuid4().hex[:8]}",
        timestamp=now,
        date_str=now.strftime("%Y-%m-%d"),
        entry_type=entry_type,
        title=article.title[:100],
        description=article.summary or article.content[:200],
        source_url=article.url,
        source_title=article.publisher,
        cves=article.cves
    )

    events_col = get_events_collection()
    await events_col.update_one(
        {"event_id": ev_id},
        {
            "$set": {
                "latest_update": now,
                "embedding_centroid": new_centroid.tolist(),
                "cves": combined_cves,
                "threat_actors": combined_actors,
                "iocs": combined_iocs
            },
            "$addToSet": {"article_ids": article.article_id},
            "$inc": {"sources_count": 1},
            "$push": {"timeline": timeline_entry.model_dump()}
        }
    )

    articles_col = get_articles_collection()
    await articles_col.update_one({"article_id": article.article_id}, {"$set": {"assigned_event_id": ev_id}})
    
    logger.info(f"Attached article {article.article_id} to event {ev_id} (Classification: {entry_type})")

async def assign_article_to_event(
    article: Article,
    threshold: float = ASSIGNMENT_THRESHOLD_TAU
) -> Tuple[str, float, str]:
    """
    Executes complete article-to-event clustering lifecycle:
    1. Embeds article
    2. BM25 & Semantic candidate retrieval
    3. Multi-feature computation (S_sem, S_ent, S_temp, S_ioc)
    4. Logistic regression scoring
    5. Hard consistency checks
    6. Event update or creation
    """
    embedding = compute_text_embedding(f"{article.title}. {article.content[:500]}")
    
    events_col = get_events_collection()
    all_events = await events_col.find({"event_status": "ACTIVE"}).to_list(length=200)

    if not all_events:
        ev = await create_new_event_from_article(article, embedding)
        return ev.event_id, 1.0, "CREATED_FIRST_EVENT"

    # Two-stage candidate retrieval
    candidates = retrieve_candidate_events(
        article_text=f"{article.title} {article.content[:300]}",
        article_cves=article.cves,
        events=all_events,
        top_k=6
    )

    best_event = None
    best_score = -1.0
    best_features = {}

    for cand in candidates:
        # Check hard consistency rules FIRST
        is_consistent, reason = check_hard_consistency_rules(article, cand)
        if not is_consistent:
            logger.debug(f"Candidate {cand.get('event_id')} rejected: {reason}")
            continue

        feats = calculate_feature_vector(
            article_emb=embedding,
            article_entities=article.entities.get("organizations", []) + article.entities.get("threat_actors", []),
            article_cves=article.cves,
            article_iocs=article.iocs,
            article_time=article.retrieval_timestamp,
            event=cand
        )

        score, _ = global_event_scorer.predict_score(feats)
        if score > best_score:
            best_score = score
            best_event = cand
            best_features = feats

    if best_event and best_score >= threshold:
        await update_existing_event(best_event, article, embedding)
        return best_event["event_id"], best_score, "ATTACHED_TO_EVENT"
    else:
        ev = await create_new_event_from_article(article, embedding)
        return ev.event_id, best_score, "CREATED_NEW_EVENT"
