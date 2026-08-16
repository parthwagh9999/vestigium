"""AlienVault OTX Threat Intelligence transform adapter."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class AlienVaultOTXTransform(BaseTransform):
    """AlienVault OTX Indicator & Pulse Intelligence."""

    id = "builtin.alienvault_otx"
    name = "AlienVault OTX Threat Intelligence"
    description = "Query AlienVault Open Threat Exchange (OTX) for threat pulses, adversary tags, malware families, and related IOCs."
    category = "Threat Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "AlienVault OTX API"
    documentation_url = "https://otx.alienvault.com/api"
    license = "Community / Commercial"

    input_entity_types = ["domain", "ip_address", "hash", "url", "subdomain"]
    output_entity_types = ["ioc", "threat_actor", "malware", "cve"]
    relationships_created = ["associated_with_threat", "attributed_to", "infected_by"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False  # Public general indicator endpoint works without key, enhanced with key
    api_key_service = "alienvault_otx"
    installation_required = False
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
        val = entity.value.strip()
        e_type = entity.entity_type
        api_key = params.get("api_key")

        # Map type to OTX section
        if e_type in ("ip_address", "ipv6_address"):
            section = "IPv4" if ":" not in val else "IPv6"
        elif e_type in ("domain", "subdomain"):
            section = "domain"
        elif e_type == "hash":
            section = "file"
        elif e_type == "url":
            section = "url"
        else:
            section = "domain"

        url = f"https://otx.alienvault.com/api/v1/indicators/{section}/{val}/general"
        headers = {"User-Agent": "Vestigium-Intel-OSINT/1.0"}
        if api_key:
            headers["X-OTX-API-KEY"] = api_key

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_info: dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_info = data
                    pulse_info = data.get("pulse_info", {})
                    pulse_count = pulse_info.get("count", 0)
                    pulses = pulse_info.get("pulses", [])

                    if pulse_count > 0:
                        # 1. Add Threat Summary IOC node
                        ioc_ent = Entity(
                            entity_type="ioc",
                            value=f"OTX-{val}",
                            label=f"OTX Threat ({pulse_count} Pulses)",
                            confidence=0.9,
                            source="AlienVault OTX",
                            properties={
                                "pulse_count": pulse_count,
                                "indicator": val,
                                "section": section,
                            },
                        )
                        entities.append(ioc_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=ioc_ent.id,
                                relationship_type="associated_with_threat",
                                confidence=0.9,
                                source="AlienVault OTX",
                                label="otx_pulses",
                            )
                        )

                        # 2. Add top pulse tags & malware families
                        tags_seen: set[str] = set()
                        for p in pulses[:5]:
                            for tag in p.get("tags", []):
                                if tag and tag.lower() not in tags_seen:
                                    tags_seen.add(tag.lower())
                                    tag_ent = Entity(
                                        entity_type="malware" if any(w in tag.lower() for w in ("trojan", "ransom", "stealer", "bot", "c2")) else "ioc",
                                        value=tag,
                                        label=f"Threat Tag: {tag}",
                                        confidence=0.85,
                                        source="AlienVault OTX",
                                        properties={"pulse_name": p.get("name"), "tag": tag},
                                    )
                                    entities.append(tag_ent)
                                    relationships.append(
                                        EntityRelationship(
                                            source_entity_id=ioc_ent.id,
                                            target_entity_id=tag_ent.id,
                                            relationship_type="attributed_to",
                                            confidence=0.85,
                                            source="AlienVault OTX",
                                            label="pulse_tag",
                                        )
                                    )
            except Exception as e:
                logger.debug("AlienVault OTX request error: %s", e)
                raw_info["error"] = str(e)

        return entities, relationships, raw_info
