"""Entity normalizer for the OSINT Pipeline.

Responsible for canonicalizing inputs before they reach the Entity Resolver or the Database.
"""
from typing import Any

def normalize_domain(domain: str) -> str:
    """Normalize a domain by removing schemes, www, and trailing slashes."""
    if not domain:
        return domain
    d = domain.lower().strip()
    if d.startswith("http://"):
        d = d[7:]
    elif d.startswith("https://"):
        d = d[8:]
    if d.startswith("www."):
        d = d[4:]
    d = d.split('/')[0].split('?')[0].split('#')[0]
    return d

def normalize_email(email: str) -> str:
    """Normalize an email address."""
    if not email:
        return email
    return email.lower().strip()

def normalize_username(username: str) -> str:
    """Normalize a username."""
    if not username:
        return username
    # Usernames are often case-sensitive on platforms, but generally lowercased for searching
    return username.strip()

def normalize_ip(ip: str) -> str:
    """Normalize an IP address."""
    if not ip:
        return ip
    return ip.strip()

def normalize_entity_value(entity_type: str, value: str) -> str:
    """Route value to the appropriate normalizer based on entity type."""
    if not value:
        return value
        
    t = entity_type.lower()
    if t in ("domain", "subdomain", "website", "url"):
        return normalize_domain(value)
    elif t == "email":
        return normalize_email(value)
    elif t == "username":
        return normalize_username(value)
    elif t in ("ip_address", "ipv4_address", "ipv6_address"):
        return normalize_ip(value)
    
    # Default fallback
    return value.strip()
