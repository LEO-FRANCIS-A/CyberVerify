import json
import re
import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.models.schemas import ExtractedEntities

logger = logging.getLogger(__name__)

# Known cybersecurity organizations and vendors for rule-based identification
KNOWN_ORGANIZATIONS = [
    "OpenAI", "Anthropic", "Microsoft", "Google", "Apple", "Hugging Face", 
    "CrowdStrike", "Okta", "Cisco", "Snowflake", "AT&T", "Ticketmaster", 
    "SolarWinds", "Palo Alto Networks", "Fortinet", "Cloudflare", "Amazon", 
    "AWS", "GitHub", "GitLab", "Meta", "Facebook", "Twitter", "X", 
    "Telegram", "LastPass", "1Password", "NVIDIA", "Intel", "AMD", 
    "Lockheed Martin", "T-Mobile", "Verizon", "Uber", "Sony", "FBI", "CISA",
    "Progress Software", "Progress", "Atlassian", "Ivanti", "ConnectWise",
    "Red Hat", "Debian", "Ubuntu", "Canonical", "Apache", "VMware", "Citrix",
    "F5", "Check Point", "Trend Micro", "Sophos", "Qualys", "Rapid7",
    "SentinelOne", "Splunk", "Oracle", "SAP", "Salesforce", "IBM", "Siemens"
]

KNOWN_THREAT_ACTORS = [
    "cl0p", "clop", "lockbit", "blackcat", "alphv", "lazarus", "apt28", "apt29", 
    "fancy bear", "cozy bear", "sandworm", "volt typhoon", "salt typhoon", 
    "scattered spider", "darkside", "revil", "conti", "fin7", "fin8", "ta505", 
    "muddywater", "kimsuky", "storm-0558", "midnight blizzard", "black basta", 
    "bianlian", "rhysida", "play ransomware", "akira", "qakbot", "emotet"
]

KNOWN_PRODUCTS = [
    "moveit transfer", "moveit", "xz utils", "xz", "log4j", "spring framework", "spring",
    "solarwinds orion", "fortios", "screenconnect", "connectwise", "anydesk", "ivanti connect secure",
    "confluence", "jira", "gitlab", "github", "active directory", "exchange server", "exchange",
    "citrix adc", "citrix gateway", "apache http server", "nginx", "openssl", "sudo",
    "linux kernel", "windows", "esxi", "vcenter", "chatgpt", "copilot", "azure", "aws",
    "kubernetes", "docker", "terramaster", "pan-os", "globalprotect", "curl", "glibc", "openssh"
]

NON_ENTITY_WORDS = {
    "malicious", "critical", "severe", "alleged", "suspected", "new", "zero-day", "zeroday", 
    "recent", "multiple", "major", "urgent", "massive", "high", "medium", "low", "warning", 
    "report", "backdoor", "exploit", "vulnerability", "vulnerabilities", "security", "ransomware", 
    "group", "attack", "attacker", "attackers", "hackers", "hacker", "threat", "phishing", 
    "breach", "leak", "leaked", "flaw", "flaws", "patch", "patched", "upstream", "downstream", 
    "cyber", "cybersecurity", "unpatched", "unauthorized", "bypass", "injection", "rce", "remote", 
    "code", "execution", "denial", "service", "ddos", "trojan", "malware", "spyware", "infostealer", 
    "actor", "actors", "campaign", "syndicate", "did", "was", "is", "has", "the", "a", "an", "what", 
    "how", "cyberverify", "unknown", "breaking", "confirmed", "active", "in-the-wild"
}

INCIDENT_KEYWORDS = {
    "Data Breach": ["breach", "leaked", "leak", "exposed", "compromised", "database dump", "user data stolen"],
    "Ransomware Attack": ["ransomware", "encrypted", "extortion", "lockbit", "blackcat", "ransom"],
    "Zero-Day Vulnerability": ["zero-day", "0-day", "cve", "vulnerability", "exploit", "unpatched"],
    "Supply Chain Attack": ["supply chain", "dependency confusion", "npm package", "pypi package", "backdoor"],
    "Account Takeover / Phishing": ["phishing", "credential stuffing", "session hijacking", "mfa bypass", "token theft"],
    "DDoS Attack": ["ddos", "denial of service", "outage", "botnet"],
    "Insider Threat / Source Code Leak": ["source code", "internal memo", "repo leak", "insider", "whistleblower"]
}

EXTRACTION_SYSTEM_PROMPT = """You are a senior cybersecurity intelligence analyst.
Extract structured factual claim components from the user's cybersecurity inquiry.
Respond strictly in valid JSON format matching this schema:
{
  "subject": "The primary entity or technical component involved",
  "organisation": "The company, institution, or vendor targeted or mentioned",
  "incident_type": "One of: Data Breach, Ransomware Attack, Zero-Day Vulnerability, Supply Chain Attack, Account Takeover, DDoS Attack, Source Code Leak, or General Security Incident",
  "allegation": "A concise summary of the core accusation or factual claim",
  "relevant_dates": ["Any dates, years, or time references mentioned"],
  "affected_products": ["Any specific software, API, or hardware products mentioned"],
  "search_keywords": ["5 to 7 specific search queries optimized for search engines to find official advisories and credible cybersecurity reporting"]
}"""

async def extract_claim_with_llm(claim: str) -> Optional[ExtractedEntities]:
    """Attempts claim extraction using configured LLM APIs (Gemini or OpenAI)."""
    # Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{EXTRACTION_SYSTEM_PROMPT}\n\nClaim to analyze:\n\"{claim}\"",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            if response.text:
                data = json.loads(response.text)
                return ExtractedEntities(**data)
        except Exception as e:
            logger.warning(f"Gemini claim extraction failed: {e}. Falling back...")

    # Try OpenAI
    if settings.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Claim to analyze:\n\"{claim}\""}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                return ExtractedEntities(**data)
        except Exception as e:
            logger.warning(f"OpenAI claim extraction failed: {e}. Falling back...")

    return None

def extract_claim_heuristics(claim: str) -> ExtractedEntities:
    """
    Robust rule-based and regex cybersecurity claim extractor.
    Guarantees reliable operation without relying on external LLM availability.
    Accurately isolates threat actors, CVEs, vendor organizations, and affected products.
    """
    claim_lower = claim.lower()

    # 1. Detect CVEs
    cves = [c.upper() for c in re.findall(r"CVE-\d{4}-\d{4,7}", claim, re.IGNORECASE)]

    # 2. Detect Threat Actors
    detected_threat_actor = None
    for actor in KNOWN_THREAT_ACTORS:
        if re.search(r"\b" + re.escape(actor) + r"\b", claim_lower):
            detected_threat_actor = actor.upper() if len(actor) <= 4 else actor.title()
            break

    # 3. Detect Known Organizations
    matched_orgs = []
    for org in KNOWN_ORGANIZATIONS:
        pattern = r"\b" + re.escape(org.lower()) + r"\b"
        if re.search(pattern, claim_lower):
            matched_orgs.append(org)

    # 4. Detect Known Products / Software
    matched_products = []
    # Sort known products by length descending to match longest phrases first
    for prod in sorted(KNOWN_PRODUCTS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(prod) + r"\b", claim_lower):
            title_prod = prod.title()
            if not any(title_prod.lower() in p.lower() for p in matched_products):
                matched_products.append(title_prod)

    # 5. Extract fallback proper nouns if neither org nor product was matched
    if not matched_orgs and not matched_products:
        words = re.findall(r"\b[A-Za-z0-9_-]+\b", claim)
        candidates = [
            w for w in words 
            if w[0].isupper() 
            and w.lower() not in NON_ENTITY_WORDS 
            and not w.upper().startswith("CVE-")
            and (not detected_threat_actor or w.lower() != detected_threat_actor.lower())
        ]
        if candidates:
            matched_products.append(" ".join(candidates[:2]))

    # 6. Determine Primary Organisation and Subject
    if matched_orgs:
        identified_org = matched_orgs[0]
    elif matched_products:
        identified_org = matched_products[0]
    else:
        identified_org = "Unknown Organisation"

    # Subject priority: product > org > CVE > generic
    if matched_products:
        subject = matched_products[0]
    elif identified_org != "Unknown Organisation":
        subject = identified_org
    elif cves:
        subject = cves[0]
    else:
        subject = "Cybersecurity Claim"

    # 7. Detect Incident Type
    identified_type = "Cybersecurity Incident"
    for inc_type, keywords in INCIDENT_KEYWORDS.items():
        if any(kw in claim_lower for kw in keywords):
            identified_type = inc_type
            break
            
    if "hack" in claim_lower or "hacked" in claim_lower:
        identified_type = "Unauthorized Intrusion / Breach"
    elif cves and identified_type == "Cybersecurity Incident":
        identified_type = "Zero-Day Vulnerability"

    # 8. Detect Years & Products list
    years = re.findall(r"\b(19\d\d|20\d\d)\b", claim)
    all_products = []
    if cves:
        all_products.extend(cves)
    if matched_products:
        all_products.extend(matched_products)
    if len(matched_orgs) > 1:
        all_products.extend(matched_orgs[1:])

    # 9. Formulate Highly Targeted Search Keywords
    keywords = []
    if cves:
        cve = cves[0]
        keywords.append(f"{cve} advisory")
        if matched_products:
            keywords.append(f"{cve} {matched_products[0]}")
        elif identified_org != "Unknown Organisation":
            keywords.append(f"{cve} {identified_org}")
        keywords.append(f"{cve} security vulnerability")

    if matched_products:
        keywords.append(f"{matched_products[0]} security advisory")
        keywords.append(f"{matched_products[0]} {identified_type}")

    if matched_orgs and matched_orgs[0] not in [p for p in matched_products]:
        keywords.append(f"{matched_orgs[0]} security advisory")
        keywords.append(f"{matched_orgs[0]} {identified_type}")

    if detected_threat_actor:
        target_name = matched_products[0] if matched_products else (identified_org if identified_org != "Unknown Organisation" else (cves[0] if cves else "attack"))
        keywords.append(f"{detected_threat_actor} {target_name}")

    # General fallback keywords from claim
    clean_claim = re.sub(r"[^\w\s]", "", claim)
    meaningful_words = [
        w for w in clean_claim.split() 
        if len(w) > 3 
        and w.lower() not in NON_ENTITY_WORDS 
        and not w.upper().startswith("CVE-")
    ]
    if meaningful_words:
        keywords.append(" ".join(meaningful_words[:4]))

    # Deduplicate while preserving order
    keywords = list(dict.fromkeys(keywords))

    return ExtractedEntities(
        subject=subject,
        organisation=identified_org,
        incident_type=identified_type,
        allegation=claim.strip(),
        relevant_dates=years,
        affected_products=all_products,
        search_keywords=keywords[:6]
    )

async def extract_claim(claim: str) -> ExtractedEntities:
    """Unified entry point for claim extraction."""
    extracted = await extract_claim_with_llm(claim)
    if extracted:
        return extracted
    return extract_claim_heuristics(claim)
