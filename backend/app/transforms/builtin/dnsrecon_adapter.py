"""DNSRecon transform adapter for comprehensive DNS enumeration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dns.resolver

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class DNSReconTransform(BaseTransform):
    """DNS reconnaissance mapping nameservers, mail exchanges, SOA, SPF, and TXT records."""

    id = "builtin.dnsrecon"
    name = "DNSRecon Zone & Record Recon"
    description = "Comprehensive DNS record enumeration, mail server discovery, and nameserver mapping."
    category = "Domain & DNS"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "dnspython / DNSRecon"
    documentation_url = "https://github.com/darkoperator/dnsrecon"
    license = "GPL-2.0"

    input_entity_types = ["domain", "website", "subdomain"]
    output_entity_types = ["ip_address", "mx_record", "nameserver", "txt_record"]
    relationships_created = ["resolves_to", "has_mx", "has_nameserver", "has_txt_record"]

    execution_type = "local"
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
        domain = entity.value.strip().lower()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://")[1].split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_records: dict[str, list[str]] = {}

        resolver = dns.resolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0

        loop = asyncio.get_event_loop()

        # 1. Query NS
        try:
            ns_answers = await loop.run_in_executor(None, lambda: resolver.resolve(domain, "NS"))
            raw_records["NS"] = [str(r.target).rstrip(".") for r in ns_answers]
            for ns in raw_records["NS"]:
                ns_ent = Entity(
                    entity_type="domain",
                    value=ns,
                    label=f"NS: {ns}",
                    confidence=1.0,
                    source="DNSRecon",
                    properties={"record_type": "NS", "domain": domain},
                )
                entities.append(ns_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=ns_ent.id,
                        relationship_type="has_nameserver",
                        confidence=1.0,
                        source="DNSRecon",
                        label="nameserver",
                    )
                )
        except Exception as e:
            logger.debug("DNSRecon NS lookup failed: %s", e)

        # 2. Query MX
        try:
            mx_answers = await loop.run_in_executor(None, lambda: resolver.resolve(domain, "MX"))
            raw_records["MX"] = [f"{r.preference} {str(r.exchange).rstrip('.')}" for r in mx_answers]
            for mx_str in raw_records["MX"]:
                pref, host = mx_str.split(" ", 1)
                mx_ent = Entity(
                    entity_type="domain",
                    value=host,
                    label=f"MX (P:{pref}): {host}",
                    confidence=1.0,
                    source="DNSRecon",
                    properties={"preference": int(pref), "record_type": "MX", "domain": domain},
                )
                entities.append(mx_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=mx_ent.id,
                        relationship_type="has_mx",
                        confidence=1.0,
                        source="DNSRecon",
                        label="mail_exchange",
                    )
                )
        except Exception as e:
            logger.debug("DNSRecon MX lookup failed: %s", e)

        # 3. Query TXT / SPF
        try:
            txt_answers = await loop.run_in_executor(None, lambda: resolver.resolve(domain, "TXT"))
            raw_records["TXT"] = [b"".join(r.strings).decode("utf-8", errors="ignore") for r in txt_answers]
            for txt in raw_records["TXT"][:10]:
                is_spf = "v=spf" in txt.lower()
                txt_ent = Entity(
                    entity_type="dns_record",
                    value=txt[:200],
                    label=f"TXT: {txt[:60]}...",
                    confidence=1.0,
                    source="DNSRecon",
                    properties={"record_type": "SPF" if is_spf else "TXT", "full_text": txt, "domain": domain},
                )
                entities.append(txt_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=txt_ent.id,
                        relationship_type="has_txt_record",
                        confidence=1.0,
                        source="DNSRecon",
                        label="spf_record" if is_spf else "txt_record",
                    )
                )
        except Exception as e:
            logger.debug("DNSRecon TXT lookup failed: %s", e)

        return entities, relationships, {
            "domain": domain,
            "records": raw_records,
            "total_records": len(entities),
        }
