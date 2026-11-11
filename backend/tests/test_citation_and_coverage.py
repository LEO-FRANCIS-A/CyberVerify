import pytest
from backend.app.models.schemas import ExtractedEntities, SourceItem, Subclaim
from backend.app.services.claim_decomposition_service import (
    decompose_claim_heuristics, answer_eight_investigative_questions
)
from backend.app.services.citation_validation_service import (
    verify_passage_in_content, build_validated_evidence_record
)
from backend.app.services.coverage_service import compute_investigation_coverage

def test_claim_decomposition():
    """Verify claim decomposition extracts atomic subclaims."""
    claim = "Snowflake was breached by Russian hackers using a zero-day vulnerability to steal customer records."
    entities = ExtractedEntities(
        subject="Snowflake Database",
        organisation="Snowflake",
        incident_type="Data Breach",
        allegation="Snowflake customer databases were accessed via zero-day exploit by threat actors",
        affected_products=["Snowflake Data Cloud"],
        search_keywords=["Snowflake breach", "Snowflake zero-day"]
    )
    subclaims = decompose_claim_heuristics(claim, entities)
    assert len(subclaims) >= 1
    assert subclaims[0].target_org == "Snowflake"
    assert "breach" in subclaims[0].incident_type.lower() or "data" in subclaims[0].incident_type.lower()

def test_eight_investigative_questions():
    """Verify that all 8 investigative questions are populated."""
    subclaim = Subclaim(
        subclaim_id="sc_1",
        subclaim_text="Snowflake customer accounts were compromised via infostealer credentials",
        allegation="Compromised credentials accessed Snowflake environments",
        target_org="Snowflake"
    )
    answers = answer_eight_investigative_questions(
        subclaim=subclaim,
        supporting_passages=["Mandiant observed UNC5537 using infostealer malware credentials."],
        contradicting_passages=["Snowflake confirmed no flaw or breach of Snowflake enterprise networks."],
        official_status="Snowflake joint bulletin with Mandiant published.",
        verdict="MISLEADING"
    )
    expected_keys = [
        "what_happened", "who_affected", "component_affected", "when_happened",
        "who_disclosed", "technical_evidence", "exploitation_confirmed", "compromise_confirmed"
    ]
    for key in expected_keys:
        assert key in answers
        assert len(answers[key]) > 0

def test_passage_verification_in_raw_text():
    """Verify exact and token overlap verification against crawled text."""
    raw_text = (
        "On May 31, 2024, Snowflake and Mandiant released a joint advisory indicating "
        "that compromised customer credentials originating from infostealer infections "
        "were used to target customer environments lacking multi-factor authentication."
    )
    # Exact snippet
    passage_exact = "compromised customer credentials originating from infostealer infections"
    found, score, _ = verify_passage_in_content(passage_exact, raw_text)
    assert found
    assert score >= 0.99

    # Partial snippet with minor difference
    passage_partial = "compromised customer credentials originating from infostealer infections were used to target customer environments"
    found_p, score_p, _ = verify_passage_in_content(passage_partial, raw_text)
    assert found_p
    assert score_p >= 0.70

    # Fabricated quote
    passage_fake = "Russian military intelligence GRU launched a cyber attack using a zero-day kernel exploit."
    found_f, score_f, _ = verify_passage_in_content(passage_fake, raw_text)
    assert not found_f
    assert score_f < 0.50

def test_evidence_record_citation_status():
    """Verify build_validated_evidence_record assigns correct verification status."""
    source_item = SourceItem(
        source_id="src_1",
        investigation_id="inv_test",
        title="Joint Advisory on Threat Campaign",
        publisher="Mandiant",
        url="https://mandiant.com/threat-campaign",
        source_category="Established Cybersecurity Publication",
        reliability_score=0.90,
        evidence_classification="SUPPORTING",
        extracted_passages=["Infostealer malware was the primary root cause."],
        source_group_id="grp_1"
    )

    # Validated case
    raw_text_valid = "Infostealer malware was the primary root cause of account compromise."
    ev_record = build_validated_evidence_record(
        investigation_id="inv_test",
        source_item=source_item,
        raw_content=raw_text_valid,
        claim="Accounts compromised by infostealers"
    )
    assert ev_record.citation_validation_status == "VALIDATED"

    # URL inaccessible / empty text case
    ev_record_empty = build_validated_evidence_record(
        investigation_id="inv_test",
        source_item=source_item,
        raw_content="",
        claim="Accounts compromised by infostealers"
    )
    assert ev_record_empty.citation_validation_status == "URL_INACCESSIBLE"

def test_investigation_coverage_calculation():
    """Verify computation of coverage metrics across channels."""
    sources = [
        SourceItem(
            source_id="s1", investigation_id="inv", title="Vendor Statement", publisher="Snowflake",
            url="http://snowflake.com", source_category="Official Company Announcement",
            reliability_score=1.0, evidence_classification="CONTRADICTING", source_group_id="g1", is_official=True
        ),
        SourceItem(
            source_id="s2", investigation_id="inv", title="Press Report", publisher="BleepingComputer",
            url="http://bleepingcomputer.com", source_category="Established Cybersecurity Publication",
            reliability_score=0.85, evidence_classification="SUPPORTING", source_group_id="g2"
        )
    ]
    coverage = compute_investigation_coverage(
        queries_executed=["Snowflake breach", "Snowflake advisory"],
        providers_queried=["DuckDuckGo Search", "Tavily"],
        official_queries=["site:snowflake.com advisory"],
        sources=sources,
        failed_retrievals=[],
        target_org="Snowflake"
    )
    assert coverage.coverage_percentage > 50.0
    assert "OFFICIAL_VENDOR" in coverage.channel_statuses
    assert coverage.channel_statuses["OFFICIAL_VENDOR"] == "CHECKED_FOUND"
