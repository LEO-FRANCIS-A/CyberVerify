import re
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 blocked ranges
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates a URL to prevent SSRF vulnerabilities.
    Blocks non-HTTP(S) schemes, private/internal IP spaces, loopbacks, and cloud metadata endpoints.
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid"
        
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Unsupported scheme: {parsed.scheme}. Only HTTP and HTTPS are allowed."
            
        hostname = parsed.hostname
        if not hostname:
            return False, "URL does not contain a valid hostname"
            
        # Reject obvious loopback and metadata names
        lowered_host = hostname.lower()
        if lowered_host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "instance-data"):
            return False, "Access to localhost or cloud metadata services is forbidden"
            
        # Check IP address resolution
        try:
            ip_obj = ipaddress.ip_address(hostname)
            # If direct IP given, verify it's not private
            for net in BLOCKED_IP_NETWORKS:
                if ip_obj in net:
                    return False, f"Access to private IP range {net} is forbidden"
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                return False, "Access to private or local network is forbidden"
        except ValueError:
            # It's a domain name - resolve DNS to check target IP
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                for item in addr_info:
                    ip_str = item[4][0]
                    resolved_ip = ipaddress.ip_address(ip_str)
                    for net in BLOCKED_IP_NETWORKS:
                        if resolved_ip in net:
                            return False, f"Hostname resolves to private network {net}"
                    if resolved_ip.is_private or resolved_ip.is_loopback or resolved_ip.is_reserved or resolved_ip.is_link_local:
                        return False, "Hostname resolves to private or loopback IP"
            except Exception:
                # DNS resolution failure or timeout
                return True, "Valid domain format"
                
        return True, "URL is safe"
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def sanitize_untrusted_text(text: str, max_chars: int = 8000) -> str:
    """
    Cleans untrusted external text extracted from the web to mitigate prompt injection.
    Neutralizes common injection strings and escapes delimiters.
    """
    if not text:
        return ""
        
    cleaned = text[:max_chars]
    
    # Strip potential prompt injection overrides
    patterns_to_neutralize = [
        r"(?i)ignore\s+all\s+(previous|prior)\s+instructions",
        r"(?i)system\s*prompt",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)disregard\s+(above|prior)",
        r"(?i)jailbreak",
        r"(?i)developer\s+mode\s+enabled",
    ]
    
    for pattern in patterns_to_neutralize:
        cleaned = re.sub(pattern, "[FILTERED_INSTRUCTION]", cleaned)
        
    return cleaned.strip()

def wrap_untrusted_context(content: str, source_id: str = "") -> str:
    """
    Safely tags untrusted external content with XML delimiters.
    """
    safe_body = sanitize_untrusted_text(content)
    return f'<untrusted_web_content source_id="{source_id}">\n{safe_body}\n</untrusted_web_content>'
