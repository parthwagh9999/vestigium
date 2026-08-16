"""WhatWeb transform adapter for deep web technology fingerprinting."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)

# Built-in lightweight WhatWeb signatures for fallback
WEB_SIGNATURES = [
    {"name": "WordPress", "type": "CMS", "pattern": r"/wp-(content|includes)/|name=[\"']generator[\"'] content=[\"']WordPress", "category": "CMS"},
    {"name": "Drupal", "type": "CMS", "pattern": r"Drupal\.settings|name=[\"']Generator[\"'] content=[\"']Drupal", "category": "CMS"},
    {"name": "Joomla", "type": "CMS", "pattern": r"/media/jui/|name=[\"']generator[\"'] content=[\"']Joomla", "category": "CMS"},
    {"name": "Shopify", "type": "E-Commerce", "pattern": r"cdn\.shopify\.com|Shopify\.theme", "category": "E-Commerce"},
    {"name": "React", "type": "Framework", "pattern": r"data-reactroot|react-dom|_reactRoot", "category": "Frontend Framework"},
    {"name": "Vue.js", "type": "Framework", "pattern": r"data-v-[a-f0-9]+|vue\.js|__VUE__", "category": "Frontend Framework"},
    {"name": "Next.js", "type": "Framework", "pattern": r"/_next/static/|__NEXT_DATA__", "category": "Fullstack Framework"},
    {"name": "Tailwind CSS", "type": "CSS Framework", "pattern": r"tailwindcss|class=[\"'][^\"']*\b(flex|grid|hidden|bg-|text-)", "category": "CSS"},
    {"name": "Bootstrap", "type": "CSS Framework", "pattern": r"bootstrap(\.min)?\.(css|js)", "category": "CSS"},
    {"name": "Google Analytics", "type": "Analytics", "pattern": r"googletagmanager\.com/gtag/js|google-analytics\.com/analytics\.js|UA-[0-9]+-[0-9]+", "category": "Analytics"},
    {"name": "Cloudflare", "type": "CDN / Security", "pattern": r"cf-ray|cloudflare", "category": "CDN"},
]


class WhatWebTransform(BaseTransform):
    """Deep Web Technology & CMS Fingerprinter."""

    id = "builtin.whatweb"
    name = "WhatWeb Technology Fingerprinter"
    description = "Identify content management systems (CMS), blogging platforms, JavaScript libraries, web servers, and embedded technologies."
    category = "Website & Web Technology"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "WhatWeb / Vestigium Fingerprint"
    documentation_url = "https://github.com/urbanadventurer/WhatWeb"
    license = "GPL-2.0"

    input_entity_types = ["domain", "website", "url", "subdomain"]
    output_entity_types = ["company", "service", "cve"]
    relationships_created = ["uses_technology", "built_with"]

    execution_type = "binary"
    passive_or_active = "LOW_IMPACT"
    is_passive = False
    authorization_required = False
    api_key_required = False
    installation_required = False  # Built-in regex signature fallback
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 20
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        target = entity.value.strip()
        if not target.startswith("http://") and not target.startswith("https://"):
            target_url = f"https://{target}"
        else:
            target_url = target

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        detected_techs: list[dict[str, str]] = []

        # 1. Check if whatweb binary exists
        bin_path = shutil.which("whatweb")
        if bin_path:
            try:
                proc = await asyncio.create_subprocess_exec(
                    bin_path,
                    "--log-json=-",
                    "-q",
                    target_url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                if proc.returncode == 0 and stdout:
                    import json
                    data = json.loads(stdout.decode("utf-8", errors="ignore"))
                    for entry in data:
                        plugins = entry.get("plugins", {})
                        for tech_name, tech_data in plugins.items():
                            detected_techs.append({
                                "name": tech_name,
                                "category": "Technology",
                                "version": str(tech_data.get("version", [""])[0] if tech_data.get("version") else ""),
                            })
            except Exception as e:
                logger.debug("WhatWeb binary failed: %s, using signature engine", e)

        # 2. Python-based signature engine fallback
        if not detected_techs:
            async with httpx.AsyncClient(timeout=10.0, verify=False, follow_redirects=True) as client:
                try:
                    resp = await client.get(target_url)
                    body = resp.text
                    headers_str = " ".join([f"{k}:{v}" for k, v in resp.headers.items()])

                    # Check headers
                    server = resp.headers.get("server")
                    if server:
                        detected_techs.append({"name": f"Server: {server}", "category": "Web Server", "version": ""})
                    powered_by = resp.headers.get("x-powered-by")
                    if powered_by:
                        detected_techs.append({"name": f"Powered-By: {powered_by}", "category": "Backend Runtime", "version": ""})

                    # Check signatures
                    for sig in WEB_SIGNATURES:
                        if re.search(sig["pattern"], body, re.IGNORECASE) or re.search(sig["pattern"], headers_str, re.IGNORECASE):
                            detected_techs.append({
                                "name": sig["name"],
                                "category": sig["category"],
                                "version": "",
                            })
                except Exception as e:
                    logger.debug("WhatWeb signature probe failed: %s", e)

        # Create entities
        for tech in detected_techs:
            tech_name = tech["name"]
            tech_ent = Entity(
                entity_type="company",  # Vendor / Tech node
                value=tech_name,
                label=f"Tech: {tech_name}",
                confidence=0.9,
                source="WhatWeb",
                properties={"category": tech["category"], "version": tech["version"], "target": target_url},
            )
            entities.append(tech_ent)

            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=tech_ent.id,
                    relationship_type="uses_technology",
                    confidence=0.9,
                    source="WhatWeb",
                    label=tech["category"].lower().replace(" ", "_"),
                )
            )

        return entities, relationships, {
            "target": target_url,
            "detected_technologies": detected_techs,
            "total_technologies": len(detected_techs),
        }
