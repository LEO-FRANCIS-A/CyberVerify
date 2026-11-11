import pytest
from backend.app.models.schemas import SourceItem
from backend.app.services.mathematical_engine import (
    compute_mathematical_results,
    calculate_evidence_distribution, perform_bayesian_update
)
from backend.app.services.verdict_engine import determine_verdict

def test_weighted_evidence_scoring_all_supporting():
    """Verify WES reaches near +1.0 when authoritative sources support the claim."""
    sources = [
        SourceItem(
            source_id="s1",
            investigation_id="inv1",
            title="CISA Advisory on Active Zero-Day",
            publisher="CISA",
            url="https://cisa.gov/advisory",
            source_category="Government Security Advisory",
            reliability_score=0.95,
            evidence_classification="SUPPORTING",
            source_group_id="grp_cisa",
            is_official=True
        ),
        SourceItem(
            source_id="s2",
            investigation_id="inv1",
            title="BleepingComputer: Threat Actors Exploit Flaw",
            publisher="BleepingComputer",
            url="https://bleepingcomputer.com/news/1",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            source_group_id="grp_bc"
        )
    ]
    math_res = compute_mathematical_results(sources)
    assert math_res.weighted_evidence_score > 0.8
    assert math_res.evidence_distribution.supporting_percentage == 100.0

def test_weighted_evidence_scoring_contradicting():
    """Verify WES becomes negative when sources refute the rumor."""
    sources = [
        SourceItem(
            source_id="s1",
            investigation_id="inv2",
            title="Official Statement Refuting Zero-Day Allegation",
            publisher="Snowflake",
            url="https://snowflake.com/security",
            source_category="Official Company Announcement",
            reliability_score=1.0,
            evidence_classification="CONTRADICTING",
            source_group_id="grp_official",
            is_official=True
        ),
        SourceItem(
            source_id="s2",
            investigation_id="inv2",
            title="Mandiant Confirms Credential Stuffing, No Zero-Day",
            publisher="Mandiant",
            url="https://mandiant.com/report",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.90,
            evidence_classification="CONTRADICTING",
            source_group_id="grp_mandiant"
        )
    ]
    math_res = compute_mathematical_results(sources)
    assert math_res.weighted_evidence_score < -0.8
    assert math_res.evidence_distribution.contradicting_percentage == 100.0

def test_syndication_discounting():
    """
    Verify syndicated reprints sharing the same source_group_id are decayed
    and do not double-count weight compared to an independent source.
    """
    reprint_sources = [
        SourceItem(
            source_id="s1",
            investigation_id="inv3",
            title="Original Press Release",
            publisher="Reuters",
            url="https://reuters.com/article",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            source_group_id="reprint_group_1"
        ),
        SourceItem(
            source_id="s2",
            investigation_id="inv3",
            title="Syndicated Copy 1",
            publisher="Aggregator A",
            url="https://aggregatorA.com/article",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            source_group_id="reprint_group_1"
        ),
        SourceItem(
            source_id="s3",
            investigation_id="inv3",
            title="Syndicated Copy 2",
            publisher="Aggregator B",
            url="https://aggregatorB.com/article",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            source_group_id="reprint_group_1"
        )
    ]
    math_res = compute_mathematical_results(reprint_sources)
    assert math_res.independent_source_count == 1
    # Effective weight should be significantly less than 3 * 0.85 (2.55)
    breakdown = math_res.reliability_weights_breakdown
    assert len(breakdown) == 3
    assert breakdown[1]["effective_weight"] < breakdown[0]["effective_weight"]

def test_bayesian_probability_updating():
    """Verify Bayesian log-odds update increases posterior with corroboration."""
    groups = {
        "grp1": [
            SourceItem(
                source_id="s1", investigation_id="inv", title="A", publisher="Gov",
                url="http://gov.org", source_category="Government Security Advisory",
                reliability_score=0.95, evidence_classification="SUPPORTING", source_group_id="grp1"
            )
        ],
        "grp2": [
            SourceItem(
                source_id="s2", investigation_id="inv", title="B", publisher="News",
                url="http://news.com", source_category="Established Cybersecurity Publication",
                reliability_score=0.85, evidence_classification="SUPPORTING", source_group_id="grp2"
            )
        ]
    }
    bayes = perform_bayesian_update(groups, prior_prob=0.25)
    # Posterior probability should rise from 0.25 to > 0.80
    assert bayes.posterior_probability > 0.80
    assert bayes.bayes_factor > 1.0

def test_deterministic_verdict_rules():
    """Verify strict deterministic verdict selection."""
    # 1. Official confirmation with multiple independent clusters -> VERIFIED
    sources_confirmed = [
        SourceItem(
            source_id="s1", investigation_id="inv", title="CISA Advisory", publisher="CISA",
            url="http://cisa.gov", source_category="Government Security Advisory",
            reliability_score=0.95, evidence_classification="SUPPORTING", source_group_id="g1", is_official=True
        ),
        SourceItem(
            source_id="s2", investigation_id="inv", title="Press Corroboration", publisher="BleepingComputer",
            url="http://bleepingcomputer.com", source_category="Established Cybersecurity Publication",
            reliability_score=0.85, evidence_classification="SUPPORTING", source_group_id="g2"
        )
    ]
    math_confirmed = compute_mathematical_results(sources_confirmed)
    verdict, _ = determine_verdict(math_confirmed, sources_confirmed, has_official_confirmation=True)
    assert verdict == "VERIFIED"

    # 2. Official denial -> FALSE or MISLEADING
    sources_denied = [
        SourceItem(
            source_id="s3", investigation_id="inv", title="Vendor Statement", publisher="Vendor",
            url="http://vendor.com", source_category="Official Company Announcement",
            reliability_score=1.0, evidence_classification="CONTRADICTING", source_group_id="g3", is_official=True
        ),
        SourceItem(
            source_id="s4", investigation_id="inv", title="Mandiant Debunk", publisher="Mandiant",
            url="http://mandiant.com", source_category="Established Cybersecurity Publication",
            reliability_score=0.90, evidence_classification="CONTRADICTING", source_group_id="g4"
        )
    ]
    math_denied = compute_mathematical_results(sources_denied)
    verdict_denied, _ = determine_verdict(math_denied, sources_denied, has_official_denial=True)
    assert verdict_denied in ["FALSE", "MISLEADING"]
