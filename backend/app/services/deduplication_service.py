import re
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Set

def normalize_canonical_url(raw_url: str) -> str:
    """Removes tracking query params, normalizes schemes, and strips trailing slashes."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        query_dict = parse_qs(parsed.query)
        # Filter tracking parameters
        clean_query = {
            k: v for k, v in query_dict.items()
            if not k.lower().startswith(('utm_', 'ref', 'fbclid', 'gclid', 'mc_', 'feedly'))
        }
        new_query = urlencode(clean_query, doseq=True)
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip('/')
        return urlunparse((scheme, netloc, path, parsed.params, new_query, ''))
    except Exception:
        return raw_url.strip()

def compute_content_hash(text: str) -> str:
    """Computes SHA-256 hash of normalized text for exact duplicate detection."""
    clean_text = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

def compute_headline_fingerprint(title: str) -> str:
    """Computes an 8-char MD5 fingerprint of canonicalized headline tokens."""
    clean_title = re.sub(r"[^\w\s]", "", title.lower())
    words = [w for w in clean_title.split() if len(w) > 3][:6]
    fingerprint = "-".join(sorted(words)) if words else clean_title[:20]
    return hashlib.md5(fingerprint.encode("utf-8")).hexdigest()[:8]

def compute_simhash(text: str) -> str:
    """
    Computes a 64-bit SimHash fingerprint for near-duplicate text detection.
    Returns 16-character hexadecimal string.
    """
    words = re.findall(r"\b\w{3,}\b", text.lower())
    if not words:
        return "0000000000000000"
        
    v = [0] * 64
    for word in words:
        # Compute 64-bit hash of word
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:16], 16)
        for i in range(64):
            bit = (h >> i) & 1
            if bit == 1:
                v[i] += 1
            else:
                v[i] -= 1
                
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)
            
    return f"{fingerprint:016x}"

def hamming_distance(simhash1: str, simhash2: str) -> int:
    """Calculates the bitwise Hamming distance between two 64-bit SimHashes."""
    try:
        val1 = int(simhash1, 16)
        val2 = int(simhash2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count('1')
    except (ValueError, TypeError):
        return 64

def is_near_duplicate(simhash1: str, simhash2: str, max_distance: int = 3) -> bool:
    """Determines whether two articles are near-duplicates (Hamming distance <= 3)."""
    return hamming_distance(simhash1, simhash2) <= max_distance
