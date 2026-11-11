import pytest
from backend.app.services.entity_extraction_service import (
    extract_cves, extract_iocs, extract_actors_and_malware,
    calculate_cyber_relevance, extract_full_entities
)
from backend.app.services.deduplication_service import (
    normalize_canonical_url, compute_content_hash,
    compute_headline_fingerprint, compute_simhash,
    hamming_distance, is_near_duplicate
)

def test_cve_extraction_and_alias_normalization():
    """Verify regex CVE extraction and vulnerability alias normalization."""
    text1 = "A zero-day vulnerability in Apache Log4j known as Log4Shell allows remote code execution."
    cves1 = extract_cves(text1)
    assert "CVE-2021-44228" in cves1

    text2 = "Researchers observed exploit activity using Heartbleed and EternalBlue against unpatched servers."
    cves2 = extract_cves(text2)
    assert "CVE-2014-0160" in cves2  # Heartbleed
    assert "CVE-2017-0144" in cves2  # EternalBlue

    text3 = "Disclosed under CVE-2024-3094 backdoor in XZ Utils."
    cves3 = extract_cves(text3)
    assert "CVE-2024-3094" in cves3

def test_ioc_extraction():
    """Verify extraction of hashes and public IPv4 while filtering private IPs."""
    text = (
        "Malware dropped binary with SHA256 "
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. "
        "C2 server contacted at 93.184.216.34, internal test at 192.168.1.10."
    )
    iocs = extract_iocs(text)
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in iocs["sha256"]
    assert "93.184.216.34" in iocs["ipv4"]
    # Private IP 192.168.1.10 should be rejected by IOC extractor
    assert "192.168.1.10" not in iocs["ipv4"]

def test_threat_actors_and_malware_extraction():
    """Verify identification of curated threat actors and malware families."""
    text = "LockBit ransomware operators leveraged Cobalt Strike beacons and Mimikatz for lateral movement."
    actors, malware = extract_actors_and_malware(text)
    
    assert any("lockbit" in a.lower() for a in actors)
    assert any("cobalt strike" in m.lower() for m in malware)
    assert any("mimikatz" in m.lower() for m in malware)

def test_cyber_relevance_scoring():
    """Verify that cybersecurity text scores higher than generic news text."""
    cyber_text = "Critical zero-day vulnerability in firewall firmware allows remote unauthorized exfiltration."
    generic_text = "The local football team secured victory in the weekend tournament with a final score of 3-1."
    
    is_rel_cyber, score_cyber = calculate_cyber_relevance(cyber_text)
    is_rel_generic, score_generic = calculate_cyber_relevance(generic_text)
    
    assert is_rel_cyber is True
    assert score_cyber > 0.3
    assert is_rel_generic is False
    assert score_generic < 0.2

def test_canonical_url_normalization():
    """Verify removal of UTM parameters, lowercase schemes, and trailing slashes."""
    raw1 = "https://www.bleepingcomputer.com/news/security/article-123/?utm_source=twitter&utm_medium=social"
    canonical1 = normalize_canonical_url(raw1)
    assert canonical1 == "https://bleepingcomputer.com/news/security/article-123"

    raw2 = "HTTP://CISA.GOV/news-events/advisories///?ref=feedly"
    canonical2 = normalize_canonical_url(raw2)
    assert canonical2 == "http://cisa.gov/news-events/advisories"

def test_content_hashing_exact_dedup():
    """Verify exact content hashing collapses multiple whitespace variations."""
    t1 = "Critical vulnerability discovered in Microsoft Exchange Server."
    t2 = "critical  vulnerability   discovered in microsoft exchange  server.  "
    
    hash1 = compute_content_hash(t1)
    hash2 = compute_content_hash(t2)
    assert hash1 == hash2

def test_simhash_near_duplicate_detection():
    """Verify SimHash catches republished syndications with minor edits."""
    base_article = (
        "The Apache Software Foundation has released security updates to address a remote code execution vulnerability "
        "CVE-2021-44228 affecting Log4j versions 2.0-beta9 to 2.14.1. An unauthenticated remote attacker could exploit this "
        "vulnerability to take control of an affected system. Log4j is an open-source, Java-based logging utility widely used "
        "by enterprise applications and cloud services. CISA strongly urges organizations to apply the recommended mitigations "
        "immediately. Attackers have begun widespread scanning for vulnerable servers across the globe."
    )
    syndicated_reprint = base_article + " Syndicated by Cybersecurity Wire."
    unrelated_article = (
        "Astronomers using the James Webb Space Telescope have observed a distant galaxy formed only 300 million years after "
        "the Big Bang. The discovery challenges existing cosmological models of early star formation and galactic evolution "
        "in the primordial universe."
    )

    sh_base = compute_simhash(base_article)
    sh_syndicated = compute_simhash(syndicated_reprint)
    sh_unrelated = compute_simhash(unrelated_article)

    # Near duplicate should have small Hamming distance
    d_near = hamming_distance(sh_base, sh_syndicated)
    assert d_near <= 6
    assert is_near_duplicate(sh_base, sh_syndicated, max_distance=6)

    # Unrelated article should have large Hamming distance
    d_far = hamming_distance(sh_base, sh_unrelated)
    assert d_far > 15
    assert not is_near_duplicate(sh_base, sh_unrelated, max_distance=6)
