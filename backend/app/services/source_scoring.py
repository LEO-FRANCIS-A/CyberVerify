import re
from urllib.parse import urlparse
from typing import Tuple, Dict, Any

# Heuristic base weights defined in project specifications
BASE_SOURCE_WEIGHTS = {
    "Official Company Announcement": 1.00,
    "Government Security Advisory": 0.95,
    "Established Cybersecurity Publication": 0.85,
    "Independent Security Researcher": 0.80,
    "General News Publication": 0.65,
    "Community Discussion": 0.35,
    "General Web Source": 0.50
}

# Domain mapping for accurate categorization
GOVERNMENT_DOMAINS = [
    "cisa.gov", "nvd.nist.gov", "cert.org", "ncsc.gov.uk", "bsi.bund.de",
    "cyber.gc.ca", "cert-in.org.in", "fbi.gov", "us-cert.cisa.gov", "enisa.europa.eu"
]

CYBERSECURITY_PUBLICATIONS = [
    "bleepingcomputer.com", "krebsonsecurity.com", "thehackernews.com", 
    "darkreading.com", "securityweek.com", "theregister.com", "threatpost.com", 
    "scmagazine.com", "cyberscoop.com", "infosecurity-magazine.com",
    "arstechnica.com", "zdnet.com", "securityboulevard.com"
]

GENERAL_NEWS_PUBLICATIONS = [
    "reuters.com", "bloomberg.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "wsj.com", "nytimes.com", "washingtonpost.com", "ft.com", "techcrunch.com",
    "theverge.com", "forbes.com", "cnbc.com", "theguardian.com", "axios.com"
]

COMMUNITY_PLATFORMS = [
    "reddit.com", "twitter.com", "x.com", "news.ycombinator.com", "medium.com",
    "substack.com", "quora.com", "linkedin.com", "t.me", "telegram.org"
]

RESEARCH_PLATFORMS = [
    "googleprojectzero.blogspot.com", "mandiant.com", "crowdstrike.com/blog",
    "redcanary.com", "unit42.paloaltonetworks.com", "troyhunt.com",
    "github.com/advisories", "citizenlab.ca", "sentinelone.com/blog",
    "trendmicro.com/vinfo", "qualys.com/research"
]

def classify_and_score_source(url: str, publisher: str, organisation: str, content: str = "") -> Tuple[str, float, bool, bool]:
    """
    Classifies a source into one of the 6 standard categories and computes its reliability score.
    Returns: (category, reliability_score, is_official, is_primary)
    """
    parsed = urlparse(url)
    domain = parsed.hostname.lower() if parsed.hostname else ""
    # Strip leading www.
    clean_domain = re.sub(r"^www\.", "", domain)
    
    clean_org = organisation.lower().replace(" ", "").replace("-", "") if organisation else ""
    is_official = False
    is_primary = False
    
    # 1. Check if it's an Official Company Domain
    # Checks either primary or secondary target organisation (e.g. openai.com or huggingface.co)
    org_list = [o.strip() for o in re.split(r"[,;+/&]|and", organisation)] if organisation else []
    for org_name in org_list:
        clean_org = org_name.lower().replace(" ", "").replace("-", "")
        if clean_org and len(clean_org) > 2:
            if clean_org in clean_domain or clean_domain.startswith(clean_org):
                is_official = True
                is_primary = True
                category = "Official Company Announcement"
                weight = BASE_SOURCE_WEIGHTS[category]
                return category, weight, is_official, is_primary

    # 2. Check Government Sources
    if any(clean_domain.endswith(gov) or clean_domain == gov for gov in GOVERNMENT_DOMAINS) or clean_domain.endswith(".gov"):
        category = "Government Security Advisory"
        weight = BASE_SOURCE_WEIGHTS[category]
        return category, weight, False, True

    # 3. Check Research Labs
    if any(clean_domain.endswith(res) or clean_domain == res for res in RESEARCH_PLATFORMS):
        category = "Independent Security Researcher"
        weight = BASE_SOURCE_WEIGHTS[category]
        return category, weight, False, True

    # 4. Check Established Cybersecurity Publications
    if any(clean_domain.endswith(pub) or clean_domain == pub for pub in CYBERSECURITY_PUBLICATIONS):
        category = "Established Cybersecurity Publication"
        weight = BASE_SOURCE_WEIGHTS[category]
        # Primary if quoting direct statement or CVE proof
        if "statement" in content.lower() or "confirmed" in content.lower() or "cve-" in content.lower():
            is_primary = True
        return category, weight, False, is_primary

    # 5. Check Community Platforms
    if any(clean_domain.endswith(comm) or clean_domain == comm for comm in COMMUNITY_PLATFORMS):
        category = "Community Discussion"
        weight = BASE_SOURCE_WEIGHTS[category]
        return category, weight, False, False

    # 6. Check General News Publications
    if any(clean_domain.endswith(news) or clean_domain == news for news in GENERAL_NEWS_PUBLICATIONS):
        category = "General News Publication"
        weight = BASE_SOURCE_WEIGHTS[category]
        return category, weight, False, False

    # Default fallback
    category = "General Web Source"
    weight = BASE_SOURCE_WEIGHTS[category]
    return category, weight, False, False

def extract_publisher_from_url(url: str) -> str:
    """Extracts a readable publisher brand name from a URL."""
    parsed = urlparse(url)
    domain = parsed.hostname.lower() if parsed.hostname else ""
    domain = re.sub(r"^www\.", "", domain)
    
    parts = domain.split(".")
    if len(parts) >= 2:
        brand = parts[-2]
        return brand.capitalize()
    return domain or "Web Source"
