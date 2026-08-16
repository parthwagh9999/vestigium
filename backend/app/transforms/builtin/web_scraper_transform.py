"""Web Scraper and Technology Stack Identification transform."""
from __future__ import annotations
import re
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

TECH_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
    "React": [r"react", r"_react", r"react-dom"],
    "Next.js": [r"_next/static", r"__NEXT_DATA__"],
    "Vue.js": [r"vue\.js", r"v-attr", r"data-v-"],
    "Tailwind CSS": [r"tailwindcss", r"tailwind"],
    "Cloudflare": [r"cloudflare", r"cf-ray"],
    "Nginx": [r"nginx"],
    "Apache": [r"apache"],
    "Bootstrap": [r"bootstrap"],
    "jQuery": [r"jquery"],
    "Shopify": [r"cdn\.shopify\.com"],
    "Webflow": [r"webflow"],
    "PHP": [r"\.php"],
}

class WebTechStackTransform(BaseTransform):
    """Transform to scrape website metadata, title, security headers, and identify web technology stack."""
    id = "builtin.web_tech_stack"
    name = "Web Tech Stack & Metadata Scraper"
    description = "Scrapes title, meta tags, HTTP security headers, and identifies web technology stack"
    category = "Web OSINT"
    
    input_entity_types = ["domain", "subdomain", "url", "website"]
    output_entity_types = ["service", "organization", "email", "social_profile"]
    
    is_passive = True
    requires_api_key = False

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        raw_val = entity.value.strip()
        target_url = raw_val if raw_val.startswith("http") else f"https://{raw_val}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        entities = []
        relationships = []

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(target_url, headers=headers)
                html = resp.text

            raw_headers = dict(resp.headers)

            server = raw_headers.get("server") or raw_headers.get("Server")
            if server:
                e = Entity(entity_type="service", value=f"Server: {server}", label=f"Server: {server}", confidence=1.0, source="Headers")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="runs_server", confidence=1.0, source="Headers"))

            powered_by = raw_headers.get("x-powered-by") or raw_headers.get("X-Powered-By")
            if powered_by:
                e = Entity(entity_type="service", value=f"Powered By: {powered_by}", label=f"Tech: {powered_by}", confidence=1.0, source="Headers")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="built_with", confidence=1.0, source="Headers"))

            combined = html + " " + str(raw_headers)
            detected_tech: set[str] = set()
            for tech_name, patterns in TECH_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, combined, re.IGNORECASE):
                        detected_tech.add(tech_name)
                        break

            for tech in detected_tech:
                e = Entity(entity_type="service", value=tech, label=tech, confidence=0.8, source="HTML Scrape")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_technology", confidence=0.8, source="HTML Scrape"))

            emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html))
            for email in list(emails)[:10]:
                if not email.endswith(".png") and not email.endswith(".svg"):
                    e = Entity(entity_type="email", value=email.lower(), label=email.lower(), confidence=0.8, source="HTML Scrape")
                    entities.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="contact_email", confidence=0.8, source="HTML Scrape"))

            return entities, relationships, {
                "status_code": resp.status_code,
                "url": str(resp.url),
                "server": server,
                "detected_tech": list(detected_tech),
                "headers": raw_headers,
            }
        except Exception as e:
            return [], [], {"warning": f"Web scraping request could not connect: {e}"}
