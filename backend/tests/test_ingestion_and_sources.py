import pytest
from backend.app.core.security import is_safe_url
from backend.app.services.source_registry_service import DEFAULT_SOURCES
from backend.app.services.ingestion_service import fetch_feed_entries

def test_ssrf_protection_loopback():
    """Verify loopback addresses and hostnames are rejected."""
    bad_urls = [
        "http://127.0.0.1/admin",
        "http://localhost:8000/api",
        "http://127.0.0.2:8080",
        "http://[::1]/status",
        "https://127.127.127.127"
    ]
    for url in bad_urls:
        safe, reason = is_safe_url(url)
        assert not safe, f"Expected {url} to be rejected, but passed: {reason}"

def test_ssrf_protection_private_subnets():
    """Verify RFC 1918 private subnets are rejected."""
    private_urls = [
        "http://10.0.0.1/secret",
        "http://192.168.1.100/router",
        "http://172.16.0.5:5000",
        "http://172.31.255.255/internal"
    ]
    for url in private_urls:
        safe, reason = is_safe_url(url)
        assert not safe, f"Expected private IP {url} to be rejected"

def test_ssrf_protection_cloud_metadata():
    """Verify AWS/GCP cloud metadata endpoints are strictly blocked."""
    metadata_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://instance-data/latest/meta-data/"
    ]
    for url in metadata_urls:
        safe, reason = is_safe_url(url)
        assert not safe, f"Expected metadata URL {url} to be rejected"

def test_ssrf_protection_unsupported_schemes():
    """Verify file://, ftp://, gopher:// schemes are blocked."""
    schemes = [
        "file:///etc/passwd",
        "ftp://ftp.example.com/file",
        "gopher://gopher.example.com",
        "javascript:alert(1)"
    ]
    for url in schemes:
        safe, reason = is_safe_url(url)
        assert not safe, f"Expected non-http scheme {url} to be rejected"

def test_ssrf_allows_safe_external_urls():
    """Verify legitimate cybersecurity domains are approved."""
    safe_urls = [
        "https://www.cisa.gov/news-events/cybersecurity-advisories",
        "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
        "https://www.bleepingcomputer.com/news/security/",
        "https://thehackernews.com/feed.xml"
    ]
    for url in safe_urls:
        safe, reason = is_safe_url(url)
        assert safe, f"Expected {url} to be allowed, got error: {reason}"

def test_source_registry_seed_configuration():
    """Verify pre-seeded source registry has authoritative cyber sources."""
    assert len(DEFAULT_SOURCES) >= 9
    domains = [s["domain"] for s in DEFAULT_SOURCES]
    assert "cisa.gov" in domains
    assert "nvd.nist.gov" in domains
    assert "bleepingcomputer.com" in domains
    assert "thehackernews.com" in domains
    assert "krebsonsecurity.com" in domains

    for src in DEFAULT_SOURCES:
        assert 0.0 <= src["base_reliability"] <= 1.0
        assert "source_type" in src
        assert "feed_url" in src

@pytest.mark.asyncio
async def test_fetch_feed_entries_rejects_unsafe_urls():
    """Ensure fetch_feed_entries safely drops SSRF attempts without network requests."""
    res = await fetch_feed_entries("http://127.0.0.1:9090/feed.xml")
    assert res == []
    
    res_meta = await fetch_feed_entries("http://169.254.169.254/feed")
    assert res_meta == []
