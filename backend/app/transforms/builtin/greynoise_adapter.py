"""GreyNoise Internet Scanner and Threat Intelligence Transform."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class GreyNoiseTransform(BaseTransform):
    """GreyNoise Internet Noise & Benign vs Malicious Scanner Intelligence."""

    id = "builtin.greynoise"
    name = "GreyNoise Scanner Intelligence"
    description = "Determine if an IP address is a known benign scanner, malicious exploit probe, or internet background noise."
    category = "Threat Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "GreyNoise Community API"
    documentation_url = "https://docs.greynoise.io/"
    license = "Community / Commercial"

    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["ioc", "company", "malware"]
    relationships_created = ["classified_as_noise", "operated_by"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False  # Community API operates without mandatory key, enriched with key
    api_key_service = "greynoise"
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
        ip = entity.value.strip()
        api_key = params.get("api_key")

        headers = {"Accept": "application/json", "User-Agent": "Vestigium-Intel-OSINT/1.0"}
        if api_key:
            headers["key"] = api_key

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_result: dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            try:
                resp = await client.get(f"https://api.greynoise.io/v3/community/{ip}")
                if resp.status_code == 200:
                    data = resp.json()
                    raw_result = data

                    noise = data.get("noise", False)
                    riot = data.get("riot", False)  # Rule It Out (Common business service)
                    classification = data.get("classification", "unknown")
                    actor = data.get("actor") or "Unknown Actor"
                    name = data.get("name") or "Internet Scanner"

                    # 1. Scanner Classification Entity
                    label = f"GreyNoise: {classification.upper()} ({actor})" if noise else f"GreyNoise: Not Seen ({ip})"
                    score_confidence = 1.0 if (noise or riot) else 0.5

                    ioc_ent = Entity(
                        entity_type="ioc",
                        value=f"GREYNOISE-{ip}",
                        label=label,
                        confidence=score_confidence,
                        source="GreyNoise",
                        properties={
                            "noise": noise,
                            "riot": riot,
                            "classification": classification,
                            "actor": actor,
                            "name": name,
                            "last_seen": data.get("last_seen", ""),
                        },
                    )
                    entities.append(ioc_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=ioc_ent.id,
                            relationship_type="classified_as_noise",
                            confidence=score_confidence,
                            source="GreyNoise",
                            label=f"scanner_{classification}",
                        )
                    )

                    # 2. Add Actor Organization Entity if identified
                    if actor and actor != "Unknown Actor":
                        actor_ent = Entity(
                            entity_type="threat_actor" if classification == "malicious" else "company",
                            value=actor,
                            label=f"Scanner Org: {actor}",
                            confidence=0.9,
                            source="GreyNoise",
                            properties={"classification": classification, "actor": actor},
                        )
                        entities.append(actor_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=ioc_ent.id,
                                target_entity_id=actor_ent.id,
                                relationship_type="operated_by",
                                confidence=0.9,
                                source="GreyNoise",
                                label="operator",
                            )
                        )
            except Exception as e:
                logger.debug("GreyNoise query error: %s", e)
                raw_result["error"] = str(e)

        return entities, relationships, raw_result
