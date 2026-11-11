import re
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from backend.app.core.config import settings
from backend.app.core.security import is_safe_url
from backend.app.services.source_scoring import classify_and_score_source, extract_publisher_from_url

logger = logging.getLogger(__name__)

OFFICIAL_DOMAINS = {
    "openai": ["openai.com"],
    "anthropic": ["anthropic.com"],
    "microsoft": ["microsoft.com", "msrc.microsoft.com"],
    "google": ["google.com", "blog.google", "security.googleblog.com"],
    "apple": ["apple.com", "support.apple.com"],
    "huggingface": ["huggingface.co"],
    "crowdstrike": ["crowdstrike.com"],
    "okta": ["okta.com", "sec.okta.com"],
    "cisco": ["cisco.com", "sec.cloudapps.cisco.com"],
    "cloudflare": ["cloudflare.com", "blog.cloudflare.com"],
    "github": ["github.com", "github.blog"],
    "aws": ["aws.amazon.com", "amazon.com"],
    "snowflake": ["snowflake.com"],
    "t-mobile": ["t-mobile.com"],
    "att": ["att.com"],
    "ticketmaster": ["ticketmaster.com"],
    "progress software": ["progress.com", "community.progress.com"],
    "progress": ["progress.com", "community.progress.com"],
    "moveit": ["progress.com", "community.progress.com"],
    "moveit transfer": ["progress.com", "community.progress.com"],
    "xz": ["tukaani.org", "debian.org", "redhat.com"],
    "xz utils": ["tukaani.org", "debian.org", "redhat.com"],
    "red hat": ["redhat.com", "access.redhat.com"],
    "debian": ["debian.org", "security-tracker.debian.org"],
    "canonical": ["ubuntu.com"],
    "ubuntu": ["ubuntu.com"],
    "apache": ["apache.org"],
    "ivanti": ["ivanti.com"],
    "connectwise": ["connectwise.com"],
    "palo alto networks": ["paloaltonetworks.com", "security.paloaltonetworks.com"],
    "fortinet": ["fortiguard.com", "fortinet.com"],
    "cisa": ["cisa.gov"]
}

def clean_and_normalize_url(raw_url: str) -> str:
    """Removes marketing tracking query params (utm_*, ref, etc.) and normalizes URLs."""
    try:
        parsed = urlparse(raw_url)
        query_dict = parse_qs(parsed.query)
        # Strip tracking params
        clean_query = {k: v for k, v in query_dict.items() if not k.lower().startswith(('utm_', 'ref', 'fbclid', 'gclid'))}
        new_query = urlencode(clean_query, doseq=True)
        # Remove fragment
        normalized = urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip('/'), parsed.params, new_query, ''))
        return normalized
    except Exception:
        return raw_url

def compute_syndication_group(title: str, url: str) -> str:
    """
    Groups syndications and wire reprints.
    Articles with near-identical headlines get mapped to the same source group.
    """
    clean_title = re.sub(r"[^\w\s]", "", title.lower())
    words = [w for w in clean_title.split() if len(w) > 3][:6]
    fingerprint = "-".join(sorted(words)) if words else urlparse(url).netloc
    return hashlib.md5(fingerprint.encode()).hexdigest()[:8]

async def search_duckduckgo(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Performs real-time search using duckduckgo_search library."""
    results = []
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "publisher": extract_publisher_from_url(r.get("href", ""))
                })
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for query '{query}': {e}")
    return results

async def search_tavily(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Performs search using Tavily API if configured."""
    results = []
    if not settings.TAVILY_API_KEY:
        return results
    try:
        import httpx
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": False
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "publisher": extract_publisher_from_url(item.get("url", ""))
                    })
    except Exception as e:
        logger.warning(f"Tavily search failed for query '{query}': {e}")
    return results

async def conduct_targeted_search(
    organisation: str,
    incident_type: str,
    keywords: List[str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Executes a multi-phase targeted search:
    1. Official company and government advisory query
    2. Respected cybersecurity news query
    3. Broad incident query
    Returns: (deduplicated_results, official_queries_checked)
    """
    raw_results = []
    official_queries_checked = []

    clean_org = organisation.lower().strip()
    official_domains = OFFICIAL_DOMAINS.get(clean_org, [])

    # Phase 1: Official advisory query
    if official_domains:
        domain_query = " OR ".join([f"site:{d}" for d in official_domains])
        official_q = f"({domain_query}) {incident_type} statement advisory"
        official_queries_checked.append(official_q)
    else:
        official_q = f'"{organisation}" security advisory statement official'
        official_queries_checked.append(official_q)

    # Phase 2: Dedicated security press query
    press_q = f'"{organisation}" {incident_type} (site:bleepingcomputer.com OR site:thehackernews.com OR site:krebsonsecurity.com OR site:cisa.gov)'
    
    # Phase 3: Primary claim keywords and CVE queries
    queries = [official_q, press_q]

    # Detect if any CVE is present
    cve_match = None
    for kw in keywords:
        cve_found = re.search(r"CVE-\d{4}-\d{4,7}", kw, re.IGNORECASE)
        if cve_found:
            cve_match = cve_found.group(0).upper()
            break

    if cve_match:
        cve_q = f'"{cve_match}" vulnerability security advisory'
        queries.insert(0, cve_q)  # Prioritize CVE search as highest authority

    # Add top specific keywords
    if keywords:
        for kw in keywords[:2]:
            if kw not in queries:
                queries.append(kw)
    else:
        queries.append(f"{organisation} {incident_type}")

    for q in queries:
        # Prefer Tavily if API key exists, otherwise DDGS
        batch = []
        if settings.TAVILY_API_KEY:
            batch = await search_tavily(q, max_results=6)
        if not batch:
            batch = await search_duckduckgo(q, max_results=6)
        raw_results.extend(batch)

    # Deduplicate and validate results
    seen_urls = set()
    deduped_results = []

    for item in raw_results:
        url = clean_and_normalize_url(item.get("url", ""))
        if not url or url in seen_urls:
            continue
            
        safe, reason = is_safe_url(url)
        if not safe:
            continue
            
        seen_urls.add(url)
        group_id = compute_syndication_group(item.get("title", ""), url)
        
        category, weight, is_official, is_primary = classify_and_score_source(
            url=url,
            publisher=item.get("publisher", ""),
            organisation=organisation,
            content=item.get("snippet", "")
        )

        deduped_results.append({
            "title": item.get("title", "Untitled"),
            "url": url,
            "snippet": item.get("snippet", ""),
            "publisher": item.get("publisher", extract_publisher_from_url(url)),
            "source_category": category,
            "reliability_score": weight,
            "is_official": is_official,
            "is_primary_evidence": is_primary,
            "source_group_id": group_id
        })

    return deduped_results[:15], official_queries_checked
