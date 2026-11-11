import pytest
from backend.app.models.schemas import SourceItem
from backend.app.services.mathematical_engine import compute_mathematical_results
from backend.app.services.verdict_engine import determine_verdict

def test_incident_snowflake_zero_day_rumor():
    """
    REAL-WORLD CASE 1: Snowflake 'Zero-Day' Rumor
    Historical Context:
      Rumors circulated online that Snowflake's core database infrastructure suffered
      a zero-day vulnerability allowing mass unauthorized data exfiltration.
    Ground Truth:
      Mandiant, CrowdStrike, and Snowflake joint investigations confirmed there was
      NO zero-day vulnerability in Snowflake's product. The breach occurred via
      credential stuffing using historical infostealer malware logs against accounts
      lacking Multi-Factor Authentication (MFA).
    Expected Determination:
      Weighted evidence score is negative; official denial of zero-day is registered;
      verdict must be MISLEADING or FALSE.
    """
    sources = [
        # Official Company Announcement
        SourceItem(
            source_id="src_snow_1",
            investigation_id="inv_snowflake",
            title="Snowflake Joint Security Advisory with Mandiant and CrowdStrike",
            publisher="Snowflake Security Portal",
            url="https://snowflake.com/security/advisory-2024-05",
            source_category="Official Company Announcement",
            reliability_score=1.0,
            evidence_classification="CONTRADICTING",
            extracted_passages=[
                "We have not identified evidence suggesting this activity was caused by a vulnerability, "
                "misconfiguration, or breach of Snowflake's product."
            ],
            source_group_id="grp_snowflake_official",
            is_official=True
        ),
        # Established Threat Intelligence / Press
        SourceItem(
            source_id="src_snow_2",
            investigation_id="inv_snowflake",
            title="Mandiant Findings on UNC5537 Snowflake Customer Targeting",
            publisher="Mandiant Threat Intelligence",
            url="https://mandiant.com/resources/unc5537-snowflake",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.90,
            evidence_classification="CONTRADICTING",
            extracted_passages=[
                "Mandiant found no evidence of enterprise network penetration or zero-day exploitation; "
                "compromised credentials originating from infostealer malware were used."
            ],
            source_group_id="grp_mandiant"
        ),
        # Tech press reporting
        SourceItem(
            source_id="src_snow_3",
            investigation_id="inv_snowflake",
            title="CISA Issues Alert on Snowflake Customer Targeted Extortion",
            publisher="CISA Alerts",
            url="https://cisa.gov/news-events/alerts/snowflake-campaign",
            source_category="Government Security Advisory",
            reliability_score=0.95,
            evidence_classification="CONTRADICTING",
            extracted_passages=[
                "Organizations are urged to enable MFA to mitigate infostealer credential reuse campaigns."
            ],
            source_group_id="grp_cisa",
            is_official=True
        ),
        # Social media unverified rumor alleging zero day
        SourceItem(
            source_id="src_snow_4",
            investigation_id="inv_snowflake",
            title="Dark Web Forum Post Claims Snowflake 0-Day Exploit",
            publisher="DarkWeb Forum Leak",
            url="https://forum-leak.example/post/123",
            source_category="Social Media / Community Claim",
            reliability_score=0.35,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "Hacker claims to have dumped data using a private Snowflake zero day."
            ],
            source_group_id="grp_darkweb"
        )
    ]

    math_res = compute_mathematical_results(sources)
    verdict, explanation = determine_verdict(
        math_results=math_res,
        sources=sources,
        has_official_denial=True,
        has_official_confirmation=False
    )

    # Mathematical assertions
    assert math_res.weighted_evidence_score < -0.5, "Evidence should heavily contradict zero-day claim"
    assert math_res.bayesian_analysis.posterior_probability < 0.20
    assert verdict in ["MISLEADING", "FALSE"], f"Expected MISLEADING/FALSE, got {verdict}"
    assert "authoritative" in explanation.lower() or "refuted" in explanation.lower() or "official" in explanation.lower()

def test_incident_huggingface_secret_disclosure():
    """
    REAL-WORLD CASE 2: Hugging Face Token & Secret Exposure
    Historical Context:
      In June 2024, Hugging Face detected unauthorized access to its Spaces platform,
      suspected authentication secret compromise, and revoked affected user tokens.
    Ground Truth:
      Officially confirmed by Hugging Face security team and widely corroborated
      by threat intelligence publications.
    Expected Determination:
      Weighted evidence score is strongly positive; official confirmation present;
      deterministic verdict must be VERIFIED.
    """
    sources = [
        # Official Security Bulletin
        SourceItem(
            source_id="src_hf_1",
            investigation_id="inv_hf",
            title="Hugging Face Security Update on Spaces Platform Secrets",
            publisher="Hugging Face Blog",
            url="https://huggingface.co/blog/security-update",
            source_category="Official Company Announcement",
            reliability_score=1.0,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "We identified unauthorized access to our Spaces platform and invalidated compromised tokens."
            ],
            source_group_id="grp_hf_official",
            is_official=True
        ),
        # Established Cyber Press
        SourceItem(
            source_id="src_hf_2",
            investigation_id="inv_hf",
            title="Hugging Face Revokes Authentication Tokens Following Security Breach",
            publisher="BleepingComputer",
            url="https://bleepingcomputer.com/news/security/hugging-face-tokens",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "Hugging Face confirmed unauthorized access and recommended users rotate their API tokens."
            ],
            source_group_id="grp_bc"
        ),
        SourceItem(
            source_id="src_hf_3",
            investigation_id="inv_hf",
            title="Security Alert: Hugging Face Spaces Secret Exposure",
            publisher="The Hacker News",
            url="https://thehackernews.com/2024/06/huggingface-breach.html",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "The AI platform is working with external cybersecurity researchers following the incident."
            ],
            source_group_id="grp_thn"
        )
    ]

    math_res = compute_mathematical_results(sources)
    verdict, explanation = determine_verdict(
        math_results=math_res,
        sources=sources,
        has_official_confirmation=True,
        has_official_denial=False
    )

    assert math_res.weighted_evidence_score > 0.85
    assert math_res.bayesian_analysis.posterior_probability > 0.90
    assert verdict == "VERIFIED"
    assert math_res.confidence_score >= 0.70

def test_incident_log4shell_cisa_advisory():
    """
    REAL-WORLD CASE 3: Log4Shell (CVE-2021-44228) Active Exploitation
    Historical Context:
      Apache Log4j zero-day remote code execution vulnerability actively exploited.
    Ground Truth:
      CISA Emergency Directive 22-02, Apache Foundation advisory, and NVD CVE-2021-44228.
    Expected Determination:
      Deterministic verdict must be VERIFIED with confidence > 85%.
    """
    sources = [
        SourceItem(
            source_id="src_log_1",
            investigation_id="inv_log4j",
            title="CISA Emergency Directive 22-02: Mitigate Apache Log4j Vulnerability",
            publisher="CISA",
            url="https://cisa.gov/directives/ed-22-02",
            source_category="Government Security Advisory",
            reliability_score=0.95,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "CISA has issued Emergency Directive 22-02 directing federal agencies to patch CVE-2021-44228."
            ],
            source_group_id="grp_cisa_ed",
            is_official=True
        ),
        SourceItem(
            source_id="src_log_2",
            investigation_id="inv_log4j",
            title="Apache Log4j Security Bulletin CVE-2021-44228",
            publisher="Apache Foundation",
            url="https://logging.apache.org/security/cve-2021-44228",
            source_category="Official Company Announcement",
            reliability_score=1.0,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "Apache Log4j2 versions 2.0-beta9 through 2.15.0 JNDI features do not protect against attacker-controlled LDAP."
            ],
            source_group_id="grp_apache",
            is_official=True
        ),
        SourceItem(
            source_id="src_log_3",
            investigation_id="inv_log4j",
            title="Widespread Scanning and Exploitation of Log4j Flaw Observed",
            publisher="Dark Reading",
            url="https://darkreading.com/vulnerabilities-threats/log4j-scans",
            source_category="Established Cybersecurity Publication",
            reliability_score=0.85,
            evidence_classification="SUPPORTING",
            extracted_passages=[
                "Global honeypots record unprecedented waves of Log4j exploitation payloads."
            ],
            source_group_id="grp_dr"
        )
    ]

    math_res = compute_mathematical_results(sources)
    verdict, explanation = determine_verdict(
        math_results=math_res,
        sources=sources,
        has_official_confirmation=True,
        has_official_denial=False
    )

    assert math_res.weighted_evidence_score > 0.90
    assert math_res.bayesian_analysis.posterior_probability > 0.95
    assert verdict == "VERIFIED"
    assert math_res.confidence_score >= 0.75
