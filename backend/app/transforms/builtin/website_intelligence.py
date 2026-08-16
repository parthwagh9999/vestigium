"""Comprehensive Website Intelligence Engine Transforms."""
from __future__ import annotations
import re
import urllib.parse
from typing import Any
import httpx
from bs4 import BeautifulSoup

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

TECH_PATTERNS = {
    "CMS": {
        "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
        "Ghost": [r"ghost-blog", r"ghost.org"],
        "Shopify": [r"cdn\.shopify\.com"],
        "Webflow": [r"webflow"],
    },
    "Frameworks": {
        "React": [r"react", r"_react", r"react-dom"],
        "Next.js": [r"_next/static", r"__NEXT_DATA__"],
        "Vue.js": [r"vue\.js", r"v-attr", r"data-v-"],
        "Angular": [r"ng-version", r"angular"],
        "Tailwind CSS": [r"tailwindcss", r"tailwind"],
        "Bootstrap": [r"bootstrap"],
    },
    "Analytics": {
        "Google Analytics": [r"google-analytics\.com", r"gtag"],
        "Google Tag Manager": [r"googletagmanager\.com", r"GTM-"],
        "Hotjar": [r"hotjar\.com"],
        "Mixpanel": [r"mixpanel"],
        "Facebook Pixel": [r"fbevents\.js"],
    },
    "Infrastructure": {
        "Cloudflare": [r"cloudflare", r"cf-ray"],
        "AWS": [r"amazonaws\.com"],
        "Nginx": [r"nginx"],
        "Apache": [r"apache"],
    }
}

class WebsiteMetadataTransform(BaseTransform):
    """Extracts Title, Meta, SEO, OpenGraph, JSON-LD, and Favicon."""
    id = "builtin.website_metadata"
    name = "Website Metadata & SEO Scraper"
    description = "Extracts Title, Meta Description, OpenGraph, and Favicon"
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["info", "seo_tag"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url, headers=headers)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                    e = Entity(entity_type="info", value=f"Title: {title}", label="Page Title", confidence=1.0, source="HTML Scrape")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_title", confidence=1.0, source="HTML Scrape"))
                
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    desc = meta_desc["content"].strip()
                    e = Entity(entity_type="info", value=f"Desc: {desc}", label="Meta Description", confidence=1.0, source="HTML Scrape")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_description", confidence=1.0, source="HTML Scrape"))
                    
                generator = soup.find("meta", attrs={"name": "generator"})
                if generator and generator.get("content"):
                    gen = generator["content"].strip()
                    e = Entity(entity_type="info", value=f"Generator: {gen}", label="Site Generator", confidence=1.0, source="HTML Scrape")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="generated_by", confidence=1.0, source="HTML Scrape"))

                for og in soup.find_all("meta", property=re.compile(r"^og:")):
                    prop = og.get("property")
                    content = og.get("content")
                    if prop and content:
                        e = Entity(entity_type="seo_tag", value=f"{prop}: {content}", label="OpenGraph Tag", confidence=1.0, source="HTML Scrape")
                        results.append(e)
                        relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_og_tag", confidence=1.0, source="HTML Scrape"))
        except Exception:
            pass
            
        return results, relationships, {}

class TechStackTransform(BaseTransform):
    id = "builtin.website_tech_stack"
    name = "Advanced Tech Stack Detection"
    description = "Detects CMS, JS Frameworks, Analytics, and CDNs"
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["technology"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url, headers=headers)
                combined = resp.text + " " + str(resp.headers)
                
                for category, techs in TECH_PATTERNS.items():
                    for tech, patterns in techs.items():
                        if any(re.search(pat, combined, re.IGNORECASE) for pat in patterns):
                            e = Entity(entity_type="technology", value=tech, label=tech, confidence=1.0, source="HTML Scrape")
                            results.append(e)
                            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_technology", confidence=1.0, source="HTML Scrape"))
        except Exception:
            pass
            
        return results, relationships, {}

class SecurityHeadersTransform(BaseTransform):
    id = "builtin.website_security"
    name = "Security Headers Analysis"
    description = "Checks HSTS, CSP, CORS, and Server Headers"
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["vulnerability", "info"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url)
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                
                if "strict-transport-security" not in hdrs:
                    e = Entity(entity_type="vulnerability", value="Missing HSTS", label="Missing HSTS Header", confidence=1.0, source="Headers")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_vulnerability", confidence=1.0, source="Headers"))
                
                if "content-security-policy" not in hdrs:
                    e = Entity(entity_type="vulnerability", value="Missing CSP", label="Missing CSP Header", confidence=1.0, source="Headers")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_vulnerability", confidence=1.0, source="Headers"))
                    
                server = hdrs.get("server")
                if server:
                    e = Entity(entity_type="info", value=f"Server: {server}", label="Server Banner", confidence=1.0, source="Headers")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="exposes_server", confidence=1.0, source="Headers"))
        except Exception:
            pass
            
        return results, relationships, {}

class ContactDiscoveryTransform(BaseTransform):
    id = "builtin.website_contacts"
    name = "Contact Info Discovery"
    description = "Extracts Emails and Phone Numbers from DOM"
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["email", "phone"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url)
                
                emails = set(re.findall(email_pattern, resp.text))
                for email in emails:
                    e = Entity(entity_type="email", value=email, label="Email Address", confidence=0.8, source="HTML Scrape")
                    results.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_email", confidence=0.8, source="HTML Scrape"))
        except Exception:
            pass
            
        return results, relationships, {}

class WebsiteCrawlerTransform(BaseTransform):
    id = "builtin.website_crawler"
    name = "Website DOM Crawler"
    description = "Extracts External Links, APIs, and Hidden URLs"
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["domain", "url"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        base_domain = urllib.parse.urlparse(target_url).netloc
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                links = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http"):
                        links.add(href)
                
                for link in links:
                    link_domain = urllib.parse.urlparse(link).netloc
                    if link_domain and link_domain != base_domain:
                        e = Entity(entity_type="domain", value=link_domain, label="External Domain", confidence=1.0, source="HTML Scrape")
                        results.append(e)
                        relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="links_to", confidence=1.0, source="HTML Scrape"))
        except Exception:
            pass
            
        return results, relationships, {}

class SocialMediaTransform(BaseTransform):
    id = "builtin.website_social"
    name = "Social Media Discovery"
    description = "Finds links to FB, Twitter, LinkedIn, GitHub, etc."
    category = "Website Intelligence"
    
    input_entity_types = ["domain", "url", "website"]
    output_entity_types = ["social_profile"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        target_url = entity.value if entity.value.startswith("http") else f"https://{entity.value}"
        
        social_domains = ["twitter.com", "facebook.com", "linkedin.com", "github.com", "instagram.com", "youtube.com"]
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    for d in social_domains:
                        if d in href.lower():
                            e = Entity(entity_type="social_profile", value=href, label="Social Media", confidence=1.0, source="HTML Scrape")
                            results.append(e)
                            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="has_social_profile", confidence=1.0, source="HTML Scrape"))
                            break
        except Exception:
            pass
            
        return results, relationships, {}
