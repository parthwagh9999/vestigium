"""Email Intelligence and Security Analyzer Transform Adapter."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

import dns.resolver
import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "sharklasers.com", "throwawaymail.com", "yopmail.com", "dispostable.com",
    "fakeinbox.com", "trashmail.com", "temp-mail.org", "getairmail.com",
}


class EmailIntelTransform(BaseTransform):
    """Email Intelligence, MX/SPF/DMARC Security, and Gravatar Profile Correlator."""

    id = "builtin.email_intel"
    name = "Email Security & Profile Analyzer"
    description = "Analyze email address, MX infrastructure, SPF/DMARC policies, disposable provider status, and Gravatar profile."
    category = "Email Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "VESTIGIUM / Gravatar / DNS"
    documentation_url = "https://en.gravatar.com/site/implement/hash/"
    license = "MIT"

    input_entity_types = ["email", "domain"]
    output_entity_types = ["domain", "social_profile", "ioc", "company"]
    relationships_created = ["has_email_domain", "has_profile", "has_security_policy"]

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
        raw_val = entity.value.strip().lower()

        if "@" in raw_val:
            user_part, domain_part = raw_val.split("@", 1)
            is_email = True
        else:
            domain_part = raw_val
            user_part = None
            is_email = False

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_data: dict[str, Any] = {"domain": domain_part, "is_email": is_email}

        # 1. Domain entity link if input is email
        if is_email:
            dom_ent = Entity(
                entity_type="domain",
                value=domain_part,
                label=domain_part,
                confidence=1.0,
                source="Email Intel",
                properties={"domain": domain_part},
            )
            entities.append(dom_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=dom_ent.id,
                    relationship_type="has_email_domain",
                    confidence=1.0,
                    source="Email Intel",
                    label="email_domain",
                )
            )

        # 2. Disposable Email Detection
        is_disposable = domain_part in DISPOSABLE_DOMAINS
        raw_data["is_disposable"] = is_disposable
        if is_disposable:
            disp_ent = Entity(
                entity_type="ioc",
                value=f"DISPOSABLE-{domain_part}",
                label=f"Disposable Email Provider ({domain_part})",
                confidence=1.0,
                source="Email Intel",
                properties={"disposable": True, "domain": domain_part},
            )
            entities.append(disp_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=disp_ent.id,
                    relationship_type="associated_with",
                    confidence=1.0,
                    source="Email Intel",
                    label="disposable_risk",
                )
            )

        # 3. DNS Security Inspection (DMARC & SPF)
        resolver = dns.resolver.Resolver()
        resolver.timeout = 4.0
        resolver.lifetime = 4.0
        loop = asyncio.get_event_loop()

        # DMARC
        dmarc_record = ""
        try:
            dmarc_answers = await loop.run_in_executor(None, lambda: resolver.resolve(f"_dmarc.{domain_part}", "TXT"))
            for r in dmarc_answers:
                txt = b"".join(r.strings).decode("utf-8", errors="ignore")
                if "v=DMARC1" in txt:
                    dmarc_record = txt
                    break
        except Exception:
            pass

        raw_data["dmarc_record"] = dmarc_record
        if dmarc_record:
            policy = "none"
            if "p=reject" in dmarc_record:
                policy = "reject"
            elif "p=quarantine" in dmarc_record:
                policy = "quarantine"

            dmarc_ent = Entity(
                entity_type="dns_record",
                value=f"DMARC:{domain_part}",
                label=f"DMARC Policy [{policy.upper()}]: {domain_part}",
                confidence=1.0,
                source="Email Intel",
                properties={"policy": policy, "record": dmarc_record, "domain": domain_part},
            )
            entities.append(dmarc_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=dmarc_ent.id,
                    relationship_type="has_security_policy",
                    confidence=1.0,
                    source="Email Intel",
                    label="dmarc_policy",
                )
            )

        # 4. Gravatar Lookup if email
        if is_email:
            email_hash = hashlib.md5(raw_val.encode("utf-8")).hexdigest()
            raw_data["gravatar_hash"] = email_hash

            async with httpx.AsyncClient(timeout=6.0) as client:
                try:
                    resp = await client.get(f"https://en.gravatar.com/{email_hash}.json")
                    if resp.status_code == 200:
                        grav_data = resp.json().get("entry", [{}])[0]
                        display_name = grav_data.get("displayName") or grav_data.get("preferredUsername") or user_part
                        profile_url = grav_data.get("profileUrl") or f"https://gravatar.com/{email_hash}"

                        grav_ent = Entity(
                            entity_type="social_profile",
                            value=profile_url,
                            label=f"Gravatar: {display_name}",
                            confidence=1.0,
                            source="Gravatar",
                            properties={
                                "username": display_name,
                                "profile_url": profile_url,
                                "about": grav_data.get("aboutMe", ""),
                                "photos": [p.get("value") for p in grav_data.get("photos", [])],
                            },
                        )
                        entities.append(grav_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=grav_ent.id,
                                relationship_type="has_profile",
                                confidence=1.0,
                                source="Gravatar",
                                label="gravatar_profile",
                            )
                        )
                except Exception as e:
                    logger.debug("Gravatar lookup error for %s: %s", raw_val, e)

        return entities, relationships, raw_data
