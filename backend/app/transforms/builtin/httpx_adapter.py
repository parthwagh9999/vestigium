"""HTTPX transform adapter for fast HTTP probing and web asset discovery."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class HttpxTransform(BaseTransform):
    """Fast HTTP service probe extracting Title, Web Server, Status code, and Tech stack."""

    id = "builtin.httpx"
    name = "HTTPX Web Service Probe"
    description = "Probe HTTP/HTTPS web endpoints, extract titles, status codes, server headers, and response metadata."
    category = "Internet Asset Discovery"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "ProjectDiscovery / httpx"
    documentation_url = "https://github.com/projectdiscovery/httpx"
    license = "MIT"

    input_entity_types = ["domain", "subdomain", "ip_address", "website", "url"]
    output_entity_types = ["website", "server", "url"]
    relationships_created = ["hosts_website", "runs_server", "redirects_to"]

    execution_type = "api"
    passive_or_active = "LOW_IMPACT"
    is_passive = False
    authorization_required = False
    api_key_required = False
    installation_required = False  # Pure python httpx fallback
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 15
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        target = entity.value.strip()
        if not target.startswith("http://") and not target.startswith("https://"):
            urls_to_try = [f"https://{target}", f"http://{target}"]
        else:
            urls_to_try = [target]

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_probe: dict[str, Any] = {}

        async with httpx.AsyncClient(
            timeout=8.0,
            verify=False,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Vestigium-Intel/1.0"},
        ) as client:
            for url in urls_to_try:
                try:
                    resp = await client.get(url)
                    status_code = resp.status_code
                    headers = dict(resp.headers)
                    server = headers.get("server", "")
                    content_type = headers.get("content-type", "")

                    # Extract title
                    title = ""
                    if "<title>" in resp.text.lower():
                        try:
                            title_part = resp.text.lower().split("<title>")[1].split("</title>")[0]
                            title = title_part.strip()[:150]
                        except Exception:
                            pass

                    raw_probe = {
                        "url": str(resp.url),
                        "status_code": status_code,
                        "title": title,
                        "server": server,
                        "content_length": len(resp.content),
                        "content_type": content_type,
                    }

                    # 1. Create Website entity
                    website_ent = Entity(
                        entity_type="website",
                        value=str(resp.url),
                        label=f"{title or target} [{status_code}]",
                        confidence=1.0,
                        source="HTTPX Probe",
                        properties=raw_probe,
                    )
                    entities.append(website_ent)

                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=website_ent.id,
                            relationship_type="hosts_website",
                            confidence=1.0,
                            source="HTTPX Probe",
                            label="hosts",
                        )
                    )

                    # 2. Create Server entity if detected
                    if server:
                        server_ent = Entity(
                            entity_type="server",
                            value=server,
                            label=f"Server: {server}",
                            confidence=0.9,
                            source="HTTPX Probe",
                            properties={"server_header": server, "url": str(resp.url)},
                        )
                        entities.append(server_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=website_ent.id,
                                target_entity_id=server_ent.id,
                                relationship_type="runs_server",
                                confidence=0.9,
                                source="HTTPX Probe",
                                label="powered_by",
                            )
                        )
                    break
                except Exception as e:
                    logger.debug("HTTPX probe failed for %s: %s", url, e)

        return entities, relationships, raw_probe
