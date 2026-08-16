"""Subdomain Takeover and Dangling CNAME Detector."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dns.resolver
import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)

# Known cloud fingerprints for subdomain takeover
TAKEOVER_FINGERPRINTS = {
    "github.io": {"service": "GitHub Pages", "fingerprint": "There isn't a GitHub Pages site here"},
    "herokuapp.com": {"service": "Heroku", "fingerprint": "No such app"},
    "herokussl.com": {"service": "Heroku SSL", "fingerprint": "No such app"},
    "s3.amazonaws.com": {"service": "AWS S3 Bucket", "fingerprint": "The specified bucket does not exist"},
    "azurewebsites.net": {"service": "Azure App Service", "fingerprint": "404 Web Site not found"},
    "zendesk.com": {"service": "Zendesk", "fingerprint": "Help Center Closed"},
    "myshopify.com": {"service": "Shopify", "fingerprint": "Sorry, this shop is currently unavailable"},
    "pantheonsite.io": {"service": "Pantheon", "fingerprint": "The gods are wise, but do not know of the site which you seek"},
    "ghost.io": {"service": "Ghost", "fingerprint": "The thing you were looking for is no longer here"},
    "fastly.net": {"service": "Fastly", "fingerprint": "Fastly error: unknown domain"},
    "surge.sh": {"service": "Surge.sh", "fingerprint": "project not found"},
    "bitbucket.io": {"service": "Bitbucket", "fingerprint": "Repository not found"},
}


class DNSTakeoverTransform(BaseTransform):
    """Subdomain Takeover & Dangling DNS Indicator Detector."""

    id = "builtin.dns_takeover"
    name = "Subdomain Takeover Detector"
    description = "Detect dangling CNAME pointers and vulnerable cloud service takeovers."
    category = "Domain & DNS"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "VESTIGIUM / DNS"
    documentation_url = "https://github.com/EdOverflow/can-i-take-over-xyz"
    license = "MIT"

    input_entity_types = ["domain", "subdomain", "website"]
    output_entity_types = ["cve", "ioc", "domain", "cloud_asset"]
    relationships_created = ["vulnerable_to", "points_to"]

    execution_type = "local"
    passive_or_active = "LOW_IMPACT"
    is_passive = False
    authorization_required = False
    api_key_required = False
    installation_required = False
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 15
    supports_recursive_investigation = False

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        target = entity.value.strip().lower()
        if target.startswith("http://") or target.startswith("https://"):
            target = target.split("://")[1].split("/")[0]

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        cnames: list[str] = []
        vulnerabilities: list[dict[str, Any]] = []

        resolver = dns.resolver.Resolver()
        resolver.timeout = 4.0
        resolver.lifetime = 4.0
        loop = asyncio.get_event_loop()

        try:
            answers = await loop.run_in_executor(None, lambda: resolver.resolve(target, "CNAME"))
            cnames = [str(r.target).rstrip(".") for r in answers]
        except Exception as e:
            logger.debug("CNAME resolution for %s returned no records: %s", target, e)

        for cname in cnames:
            cname_lower = cname.lower()
            # 1. Add CNAME target entity
            cname_ent = Entity(
                entity_type="domain",
                value=cname,
                label=f"CNAME: {cname}",
                confidence=1.0,
                source="Subdomain Takeover Detector",
                properties={"cname_for": target},
            )
            entities.append(cname_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=cname_ent.id,
                    relationship_type="points_to",
                    confidence=1.0,
                    source="Subdomain Takeover Detector",
                    label="cname_target",
                )
            )

            # 2. Check for signature match
            matched_service = None
            expected_fingerprint = None
            for provider_domain, info in TAKEOVER_FINGERPRINTS.items():
                if cname_lower.endswith(provider_domain):
                    matched_service = info["service"]
                    expected_fingerprint = info["fingerprint"]
                    break

            if matched_service:
                is_vulnerable = False
                http_body = ""
                # Perform low-impact HTTP probe
                try:
                    async with httpx.AsyncClient(timeout=6.0, verify=False, follow_redirects=True) as client:
                        resp = await client.get(f"http://{target}")
                        http_body = resp.text
                        if expected_fingerprint and expected_fingerprint in http_body:
                            is_vulnerable = True
                except Exception:
                    pass

                vuln_desc = f"Potential Subdomain Takeover on {matched_service} via {cname}"
                vuln_ent = Entity(
                    entity_type="ioc",
                    value=f"TAKEOVER-{target}",
                    label=f"Takeover Risk: {matched_service}" if is_vulnerable else f"Cloud CNAME: {matched_service}",
                    confidence=0.9 if is_vulnerable else 0.5,
                    source="Subdomain Takeover Detector",
                    properties={
                        "target": target,
                        "cname": cname,
                        "service": matched_service,
                        "is_confirmed_vulnerable": is_vulnerable,
                        "fingerprint_matched": is_vulnerable,
                    },
                )
                entities.append(vuln_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=vuln_ent.id,
                        relationship_type="vulnerable_to" if is_vulnerable else "associated_with",
                        confidence=0.9 if is_vulnerable else 0.5,
                        source="Subdomain Takeover Detector",
                        label="takeover_risk" if is_vulnerable else "cloud_pointer",
                    )
                )
                vulnerabilities.append({
                    "cname": cname,
                    "service": matched_service,
                    "vulnerable": is_vulnerable,
                })

        return entities, relationships, {
            "target": target,
            "cnames": cnames,
            "takeover_checks": vulnerabilities,
        }
