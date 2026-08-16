"""BGP Route and ASN Peering Intelligence Transform."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class BGPRouteTransform(BaseTransform):
    """BGP Route, Prefix, Origin ASN, and Peering Intelligence."""

    id = "builtin.bgp_route"
    name = "BGP Route & Peering Intelligence"
    description = "Query BGP routing tables, netblock prefixes, origin ASNs, and upstream transit providers via BGPView and RIPEstat."
    category = "Cloud & ASN Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "BGPView API / RIPEstat"
    documentation_url = "https://bgpview.docs.apiary.io/"
    license = "MIT"

    input_entity_types = ["ip_address", "asn", "netblock"]
    output_entity_types = ["asn", "company", "netblock", "country"]
    relationships_created = ["routed_via_prefix", "originated_by_asn", "managed_by_org"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
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
        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_info: dict[str, Any] = {}

        # 1. ASN Input (e.g. AS15169 or 15169)
        if entity.entity_type == "asn" or val.upper().startswith("AS"):
            asn_num = val.upper().replace("AS", "")
            async with httpx.AsyncClient(timeout=8.0) as client:
                try:
                    resp = await client.get(f"https://api.bgpview.io/asn/{asn_num}")
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        raw_info = data
                        name = data.get("name", f"AS{asn_num}")
                        org = data.get("owner_address", [name])[0] if data.get("owner_address") else name

                        # Org Entity
                        org_ent = Entity(
                            entity_type="organization",
                            value=name,
                            label=f"ASN Owner: {name}",
                            confidence=1.0,
                            source="BGPView",
                            properties={"asn": asn_num, "rir": data.get("rir_name", "")},
                        )
                        entities.append(org_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=org_ent.id,
                                relationship_type="managed_by_org",
                                confidence=1.0,
                                source="BGPView",
                                label="asn_owner",
                            )
                        )
                except Exception as e:
                    logger.debug("BGPView ASN error: %s", e)

        # 2. IP Input (e.g. 8.8.8.8)
        else:
            async with httpx.AsyncClient(timeout=8.0) as client:
                try:
                    resp = await client.get(f"https://api.bgpview.io/ip/{val}")
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        raw_info = data
                        prefixes = data.get("prefixes", [])
                        if prefixes:
                            pref = prefixes[0]
                            prefix_str = pref.get("prefix", "")
                            asn_info = pref.get("asn", {})
                            asn_num = str(asn_info.get("asn", ""))
                            asn_name = asn_info.get("name", "")
                            country_code = asn_info.get("country_code", "")

                            # Netblock Entity
                            if prefix_str:
                                netblock_ent = Entity(
                                    entity_type="netblock",
                                    value=prefix_str,
                                    label=f"Prefix: {prefix_str}",
                                    confidence=1.0,
                                    source="BGPView",
                                    properties={"prefix": prefix_str, "ip": val},
                                )
                                entities.append(netblock_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=netblock_ent.id,
                                        relationship_type="routed_via_prefix",
                                        confidence=1.0,
                                        source="BGPView",
                                        label="bgp_prefix",
                                    )
                                )

                            # ASN Entity
                            if asn_num:
                                asn_ent = Entity(
                                    entity_type="asn",
                                    value=f"AS{asn_num}",
                                    label=f"AS{asn_num} ({asn_name})",
                                    confidence=1.0,
                                    source="BGPView",
                                    properties={"asn_number": asn_num, "asn_name": asn_name, "country_code": country_code},
                                )
                                entities.append(asn_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=netblock_ent.id if prefix_str else entity.id,
                                        target_entity_id=asn_ent.id,
                                        relationship_type="originated_by_asn",
                                        confidence=1.0,
                                        source="BGPView",
                                        label="origin_asn",
                                    )
                                )

                                # Organization Entity
                                if asn_name:
                                    org_ent = Entity(
                                        entity_type="organization",
                                        value=asn_name,
                                        label=f"ISP: {asn_name}",
                                        confidence=1.0,
                                        source="BGPView",
                                        properties={"asn": f"AS{asn_num}", "organization": asn_name},
                                    )
                                    entities.append(org_ent)
                                    relationships.append(
                                        EntityRelationship(
                                            source_entity_id=asn_ent.id,
                                            target_entity_id=org_ent.id,
                                            relationship_type="managed_by_org",
                                            confidence=1.0,
                                            source="BGPView",
                                            label="autonomous_system_operator",
                                        )
                                    )
                except Exception as e:
                    logger.debug("BGPView IP query error: %s", e)

        return entities, relationships, raw_info
