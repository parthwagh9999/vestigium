"""RDAP (Registration Data Access Protocol) Intelligence Transform."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class RDAPTransform(BaseTransform):
    """RDAP Protocol Domain & IP Registration Intelligence."""

    id = "builtin.rdap"
    name = "RDAP Domain & IP Registration Intel"
    description = "Query official RDAP protocol endpoints for structured domain, IP, and ASN registration data, status codes, and entity roles."
    category = "Domain & DNS"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "ICANN RDAP / OpenRDAP"
    documentation_url = "https://www.icann.org/rdap"
    license = "MIT"

    input_entity_types = ["domain", "ip_address", "asn", "website"]
    output_entity_types = ["company", "nameserver", "person", "country"]
    relationships_created = ["registered_by", "managed_by_registrar", "delegated_to"]

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
        target = entity.value.strip().lower()
        if target.startswith("http://") or target.startswith("https://"):
            target = target.split("://")[1].split("/")[0]
        if target.startswith("www."):
            target = target[4:]

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_rdap: dict[str, Any] = {}

        # Construct RDAP query URL (using ICANN RDAP bootstrap / rdap.org)
        if entity.entity_type in ("ip_address", "ipv6_address"):
            rdap_url = f"https://rdap.org/ip/{target}"
        elif entity.entity_type == "asn" or target.startswith("as"):
            asn_num = target.replace("as", "")
            rdap_url = f"https://rdap.org/autnum/{asn_num}"
        else:
            rdap_url = f"https://rdap.org/domain/{target}"

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(rdap_url, headers={"Accept": "application/rdap+json, application/json"})
                if resp.status_code == 200:
                    data = resp.json()
                    raw_rdap = data

                    # Extract Status
                    statuses = data.get("status", [])

                    # Extract Events (Registration, Expiration, Last Changed)
                    events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}
                    created_at = events.get("registration")
                    expires_at = events.get("expiration")
                    updated_at = events.get("last changed") or events.get("last update")

                    # Extract Entities (Registrar, Registrant)
                    registrar_name = ""
                    entities_list = data.get("entities", [])
                    for ent_obj in entities_list:
                        roles = ent_obj.get("roles", [])
                        vcard = ent_obj.get("vcardArray", [[], []])[1]
                        fn_name = ""
                        for v in vcard:
                            if v[0] == "fn":
                                fn_name = v[3]
                                break

                        if "registrar" in roles:
                            registrar_name = fn_name or ent_obj.get("handle", "")
                            if registrar_name:
                                reg_ent = Entity(
                                    entity_type="company",
                                    value=registrar_name,
                                    label=f"Registrar: {registrar_name}",
                                    confidence=1.0,
                                    source="RDAP",
                                    properties={
                                        "role": "Registrar",
                                        "handle": ent_obj.get("handle", ""),
                                        "target": target,
                                        "registered_at": created_at,
                                        "expires_at": expires_at,
                                    },
                                )
                                entities.append(reg_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=reg_ent.id,
                                        relationship_type="managed_by_registrar",
                                        confidence=1.0,
                                        source="RDAP",
                                        label="registrar",
                                    )
                                )

                    # Extract Nameservers
                    ns_list = data.get("nameservers", [])
                    for ns in ns_list:
                        ns_name = ns.get("ldhName", "").lower()
                        if ns_name:
                            ns_ent = Entity(
                                entity_type="domain",
                                value=ns_name,
                                label=f"NS: {ns_name}",
                                confidence=1.0,
                                source="RDAP",
                                properties={"role": "Authoritative Nameserver", "domain": target},
                            )
                            entities.append(ns_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=ns_ent.id,
                                    relationship_type="delegated_to",
                                    confidence=1.0,
                                    source="RDAP",
                                    label="nameserver_delegation",
                                )
                            )

            except Exception as e:
                logger.debug("RDAP query error: %s", e)
                raw_rdap["error"] = str(e)

        return entities, relationships, raw_rdap
