import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.schemas import Article, CyberEvent
from backend.app.services.event_scoring_service import (
    compute_semantic_similarity, compute_entity_overlap,
    compute_ioc_cve_overlap, compute_temporal_similarity,
    calculate_feature_vector, global_event_scorer
)
from backend.app.services.event_clustering_service import (
    check_hard_consistency_rules, classify_timeline_update_type
)
from backend.app.services.retrieval_service import BM25EventIndex, compute_text_embedding

def test_semantic_similarity():
    """Verify cosine similarity calculation between article embedding and centroid."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]

    assert compute_semantic_similarity(vec1, vec2) == pytest.approx(1.0, 0.001)
    assert compute_semantic_similarity(vec1, vec3) == pytest.approx(0.0, 0.001)
    # Zero vector safety
    assert compute_semantic_similarity([], [1.0, 0.5]) == 0.0

def test_entity_and_ioc_jaccard_overlap():
    """Verify Jaccard overlap computation for entities and IOCs/CVEs."""
    entities_a = ["Microsoft", "Exchange", "Volt Typhoon"]
    entities_b = ["Microsoft", "Exchange", "Fancy Bear"]
    
    # 2 common, 4 union -> 0.5
    jaccard_ent = compute_entity_overlap(entities_a, entities_b)
    assert jaccard_ent == 0.5

    cves_a = ["CVE-2021-44228"]
    iocs_a = {"ipv4": ["1.1.1.1"], "sha256": []}
    cves_b = ["CVE-2021-44228"]
    iocs_b = {"ipv4": ["1.1.1.1"], "sha256": ["deadbeef" * 8]}

    # a has 2 items, b has 3 items, intersection = 2, union = 3 -> 2/3 = 0.6667
    jaccard_ioc = compute_ioc_cve_overlap(cves_a, iocs_a, cves_b, iocs_b)
    assert round(jaccard_ioc, 2) == 0.67

def test_temporal_similarity_decay():
    """Verify exponential temporal decay exp(-lambda * delta_t)."""
    t_now = datetime.now(timezone.utc)
    t_same = t_now
    t_14d_ago = t_now - timedelta(days=14)
    t_60d_ago = t_now - timedelta(days=60)

    # Same timestamp -> score = 1.0
    assert compute_temporal_similarity(t_now, t_same) == 1.0

    # 14 days ago (approx half-life) -> around 0.45 - 0.55
    score_14d = compute_temporal_similarity(t_now, t_14d_ago)
    assert 0.45 <= score_14d <= 0.55

    # 60 days ago -> significantly lower
    score_60d = compute_temporal_similarity(t_now, t_60d_ago)
    assert score_60d < 0.15

def test_logistic_event_scoring_inference():
    """Verify event similarity score S_event falls in [0, 1]."""
    feat = {
        "s_sem": 0.85,
        "s_ent": 0.70,
        "s_temp": 0.90,
        "s_ioc": 0.50
    }
    score, weights = global_event_scorer.predict_score(feat)
    assert 0.0 <= score <= 1.0
    assert score > 0.6  # High multi-feature alignment should produce high probability

def test_disjoint_cve_hard_consistency_rule():
    """
    NON-NEGOTIABLE RULE: Articles with disjoint non-empty CVE sets identifying different
    vulnerabilities must NEVER merge merely due to semantic similarity.
    """
    article_log4j = Article(
        article_id="art_1",
        url="https://cisa.gov/log4j",
        canonical_url="https://cisa.gov/log4j",
        domain="cisa.gov",
        publisher="CISA",
        content_hash="hash_log4j_test",
        title="Apache Log4j RCE",
        content="Apache Log4j Log4Shell vulnerability CVE-2021-44228",
        cves=["CVE-2021-44228"]
    )
    event_spring4shell = {
        "event_id": "ev_spring",
        "title": "Spring Framework RCE",
        "cves": ["CVE-2022-22965"]
    }
    
    # Must reject merge even if semantic text looks similar
    consistent, reason = check_hard_consistency_rules(article_log4j, event_spring4shell)
    assert not consistent
    assert "Disjoint CVE sets" in reason

    # Shared CVE should pass consistency
    event_log4j = {
        "event_id": "ev_log4j",
        "title": "Log4j Emergency Patch",
        "cves": ["CVE-2021-44228", "CVE-2021-45046"]
    }
    consistent_ok, _ = check_hard_consistency_rules(article_log4j, event_log4j)
    assert consistent_ok

def test_bm25_retrieval_index():
    """Verify BM25 index correctly indexes cybersecurity events and retrieves top hits."""
    events = [
        {
            "event_id": "ev_snowflake",
            "title": "Snowflake Credential Stuffing Campaign",
            "description": "Infostealer credentials compromised customer accounts without MFA",
            "cves": [],
            "organizations": ["Snowflake", "Mandiant"],
            "threat_actors": ["UNC5537"]
        },
        {
            "event_id": "ev_log4j",
            "title": "Apache Log4j Remote Code Execution",
            "description": "Log4Shell CVE-2021-44228 zero-day exploited across enterprise Java applications",
            "cves": ["CVE-2021-44228"],
            "organizations": ["Apache", "CISA"],
            "threat_actors": ["Log4j"]
        }
    ]
    index = BM25EventIndex(events)
    
    # Query for Snowflake
    results = index.query("Snowflake credential breach without MFA", top_k=2)
    assert len(results) > 0
    assert results[0][0] == "ev_snowflake"

    # Query for Log4j CVE
    results_cve = index.query("CVE-2021-44228 Java logging vulnerability", top_k=2)
    assert len(results_cve) > 0
    assert results_cve[0][0] == "ev_log4j"

def test_timeline_update_classification():
    """Verify lifecycle update classification based on phrasing."""
    assert classify_timeline_update_type("CISA issues emergency directive", "bulletin") == "ADVISORY"
    assert classify_timeline_update_type("Vendor publishes patch available for download", "security update") == "PATCH"
    assert classify_timeline_update_type("Zero-day actively exploited in the wild", "ransomware attack") == "EXPLOITATION"
    assert classify_timeline_update_type("Post-mortem root cause analysis and IOC list", "investigation") == "ANALYSIS"
