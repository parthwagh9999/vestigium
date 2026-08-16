"""Assetfinder transform adapter for subdomain discovery.

Supports assetfinder binary execution with automatic fallback to passive crt.sh/hackertarget.
"""

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


class AssetfinderAdapter(BaseTransform):
    """Subdomain discovery using Assetfinder CLI or passive multi-source intelligence."""

    id = "builtin.assetfinder"
    name = "Assetfinder Subdomain Recon"
    description = "Discover subdomains and related assets for a target domain using Assetfinder or passive OSINT."
    category = "Domain & DNS"
    author = "VESTIGIUM"
    version = "1.1.0"
    source = "Assetfinder / Passive"
    documentation_url = "https://github.com/tomnomnom/assetfinder"
    license = "MIT"

    input_entity_types = ["domain", "website", "subdomain"]
    output_entity_types = ["subdomain", "domain"]
    relationships_created = ["has_subdomain"]

    execution_type = "binary"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    installation_required = False  # Graceful fallback supported
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 25
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        domain = entity.value.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://")[1].split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]

        discovered_subdomains: set[str] = set()
        execution_method = "passive_fallback"

        # 1. Try local binary if installed
        bin_path = shutil.which("assetfinder")
        if bin_path:
            try:
                proc = await asyncio.create_subprocess_exec(
                    bin_path,
                    "--subs-only",
                    domain,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                if proc.returncode == 0 and stdout:
                    for line in stdout.decode("utf-8", errors="ignore").splitlines():
                        sub = line.strip().lower()
                        if sub and sub.endswith(domain) and sub != domain:
                            discovered_subdomains.add(sub)
                    execution_method = "assetfinder_binary"
            except Exception as e:
                logger.warning("Assetfinder binary execution failed: %s, falling back to passive", e)

        # 2. Passive Fallback if binary yielded no results or not installed
        if not discovered_subdomains:
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                try:
                    resp = await client.get(f"https://crt.sh/?q=%25.{domain}&output=json")
                    if resp.status_code == 200:
                        for entry in resp.json()[:60]:
                            name_val = entry.get("name_value", "")
                            for sub in name_val.split("\n"):
                                sub = sub.strip().lower().lstrip("*.")
                                if sub and sub.endswith(domain) and sub != domain:
                                    discovered_subdomains.add(sub)
                except Exception as e:
                    logger.debug("Passive crt.sh fallback error in assetfinder: %s", e)

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []

        for sub in sorted(list(discovered_subdomains))[:50]:
            sub_entity = Entity(
                entity_type="subdomain",
                value=sub,
                label=sub,
                confidence=0.95,
                source="Assetfinder",
                properties={"parent_domain": domain, "method": execution_method},
            )
            entities.append(sub_entity)

            rel = EntityRelationship(
                source_entity_id=entity.id,
                target_entity_id=sub_entity.id,
                relationship_type="has_subdomain",
                confidence=0.95,
                source="Assetfinder",
                label="subdomain",
            )
            relationships.append(rel)

        return entities, relationships, {
            "target": domain,
            "count": len(entities),
            "execution_method": execution_method,
            "subdomains": list(discovered_subdomains)[:50],
        }
