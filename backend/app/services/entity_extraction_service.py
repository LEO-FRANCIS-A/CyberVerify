import re
import ipaddress
from typing import Dict, List, Any, Tuple, Set

# Curated alias dictionary mapping famous vulnerability / attack names to canonical CVEs
VULNERABILITY_ALIASES = {
    "log4shell": "CVE-2021-44228",
    "log4j": "CVE-2021-44228",
    "heartbleed": "CVE-2014-0160",
    "eternalblue": "CVE-2017-0144",
    "proxylogon": "CVE-2021-26855",
    "proxyshell": "CVE-2021-34473",
    "follina": "CVE-2022-30190",
    "printnightmare": "CVE-2021-34527",
    "spring4shell": "CVE-2022-22965",
    "zerologon": "CVE-2020-1472",
    "bluekeep": "CVE-2019-0708",
    "shellshock": "CVE-2014-6271",
    "spectre": "CVE-2017-5753",
    "meltdown": "CVE-2017-5754",
    "dirty cow": "CVE-2016-5195",
    "wannacry": "CVE-2017-0144"
}

KNOWN_THREAT_ACTORS = [
    "lockbit", "blackcat", "alphv", "clop", "lazarus", "lazarus group",
    "apt28", "fancy bear", "apt29", "cozy bear", "sandworm", "volt typhoon",
    "scattered spider", "fin7", "fin8", "darkside", "revil", "conti",
    "black basta", "akira", "bianlian", "rhysida", "play ransomware"
]

KNOWN_MALWARE_FAMILIES = [
    "cobalt strike", "mimikatz", "qakbot", "qbot", "trickbot", "emotet",
    "agent tesla", "redline", "formbook", "asyncrat", "icedid", "vidar",
    "raccoon stealer", "lumma", "lummac2", "darkgate", "plugx"
]

CYBER_KEYWORDS = {
    "breach": 2.0, "ransomware": 2.5, "zero-day": 3.0, "0-day": 3.0, "cve": 2.5,
    "vulnerability": 2.0, "exploit": 2.0, "phishing": 1.5, "exfiltration": 2.0,
    "credential stuffing": 2.5, "supply chain": 2.0, "backdoor": 2.0, "malware": 2.0,
    "ddos": 1.5, "compromise": 1.5, "threat actor": 2.0, "apt": 1.5, "intrusion": 1.5,
    "data leak": 2.0, "advisory": 1.5, "patch": 1.0, "poc": 2.0, "privilege escalation": 2.0
}

CVE_REGEX = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
IPV4_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MD5_REGEX = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA1_REGEX = re.compile(r"\b[a-fA-F0-9]{40}\b")
SHA256_REGEX = re.compile(r"\b[a-fA-F0-9]{64}\b")
DOMAIN_REGEX = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|io|co|gov|edu|mil|ai|dev|app|info)\b", re.IGNORECASE)

def extract_cves(text: str) -> List[str]:
    """Extracts explicit CVEs and maps normalized vulnerability aliases."""
    cves = set()
    for match in CVE_REGEX.findall(text):
        cves.add(match.upper())
        
    lower_text = text.lower()
    for alias, canonical_cve in VULNERABILITY_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", lower_text):
            cves.add(canonical_cve)
            
    return sorted(list(cves))

def extract_iocs(text: str) -> Dict[str, List[str]]:
    """Extracts valid public IPv4 addresses and cryptographic hashes."""
    iocs: Dict[str, List[str]] = {
        "ipv4": [],
        "md5": [],
        "sha1": [],
        "sha256": []
    }
    
    # 1. IP Addresses (filter out private/local IPs)
    for raw_ip in IPV4_REGEX.findall(text):
        try:
            ip_obj = ipaddress.ip_address(raw_ip)
            if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_multicast):
                iocs["ipv4"].append(raw_ip)
        except ValueError:
            pass
            
    # 2. Hashes
    # Find SHA-256 first
    sha256_matches = set(SHA256_REGEX.findall(text))
    iocs["sha256"] = sorted(list(sha256_matches))
    
    # SHA-1
    sha1_matches = set(SHA1_REGEX.findall(text)) - sha256_matches
    iocs["sha1"] = sorted(list(sha1_matches))
    
    # MD5
    md5_matches = set(MD5_REGEX.findall(text)) - sha256_matches - sha1_matches
    iocs["md5"] = sorted(list(md5_matches))
    
    iocs["ipv4"] = sorted(list(set(iocs["ipv4"])))
    return iocs

def extract_actors_and_malware(text: str) -> Tuple[List[str], List[str]]:
    """Extracts threat actors and malware families using curated dictionaries."""
    lower_text = text.lower()
    actors = set()
    malware = set()
    
    for actor in KNOWN_THREAT_ACTORS:
        if re.search(r"\b" + re.escape(actor) + r"\b", lower_text):
            actors.add(actor.title())
            
    for m in KNOWN_MALWARE_FAMILIES:
        if re.search(r"\b" + re.escape(m) + r"\b", lower_text):
            malware.add(m.title())
            
    return sorted(list(actors)), sorted(list(malware))

def calculate_cyber_relevance(text: str) -> Tuple[bool, float]:
    """Calculates cybersecurity relevance score and binary decision."""
    lower_text = text.lower()
    score = 0.0
    
    for keyword, weight in CYBER_KEYWORDS.items():
        count = len(re.findall(r"\b" + re.escape(keyword) + r"\b", lower_text))
        if count > 0:
            score += min(3.0, count) * weight
            
    cves = CVE_REGEX.findall(text)
    if cves:
        score += len(cves) * 3.0
        
    is_relevant = score >= 3.0
    normalized_score = round(min(1.0, score / 15.0), 3)
    return is_relevant, normalized_score

def extract_full_entities(text: str, title: str = "") -> Dict[str, Any]:
    """Full entity extraction combining CVEs, IOCs, actors, malware, and relevance."""
    combined_text = f"{title}\n{text}"
    cves = extract_cves(combined_text)
    iocs = extract_iocs(combined_text)
    actors, malware = extract_actors_and_malware(combined_text)
    is_relevant, rel_score = calculate_cyber_relevance(combined_text)
    
    return {
        "cves": cves,
        "iocs": iocs,
        "threat_actors": actors,
        "malware_families": malware,
        "is_cyber_relevant": is_relevant,
        "relevance_score": rel_score
    }
