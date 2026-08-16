"""TLS Certificate and SAN Inspector Transform Adapter."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import socket
import ssl
from typing import Any

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class TLSInspectorTransform(BaseTransform):
    """Direct TLS Handshake & Certificate Chain SAN Inspector."""

    id = "builtin.tls_inspector"
    name = "TLS Certificate & SAN Inspector"
    description = "Perform direct TLS handshake on port 443, parse x509 Subject Alternative Names (SANs), Issuer, Validity, and SHA-256 fingerprint."
    category = "Certificate & TLS"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "Python SSL / x509"
    documentation_url = "https://docs.python.org/3/library/ssl.html"
    license = "MIT"

    input_entity_types = ["domain", "website", "subdomain", "ip_address"]
    output_entity_types = ["certificate", "domain", "company"]
    relationships_created = ["has_certificate", "issued_by", "covers_san"]

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
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        target = entity.value.strip().lower()
        if target.startswith("https://") or target.startswith("http://"):
            target = target.split("://")[1].split("/")[0]

        loop = asyncio.get_event_loop()
        cert_data: dict[str, Any] = {}

        def _fetch_cert() -> dict[str, Any]:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((target, 443), timeout=5.0) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
                    parsed_cert = ssock.getpeercert()
                    sha256_fp = hashlib.sha256(der_cert).hexdigest()
                    return {"parsed": parsed_cert, "sha256": sha256_fp}

        try:
            cert_result = await loop.run_in_executor(None, _fetch_cert)
        except Exception as e:
            logger.debug("TLS handshake failed for %s: %s", target, e)
            return [], [], {"error": str(e), "target": target}

        parsed = cert_result.get("parsed", {})
        sha256_fp = cert_result.get("sha256", "")

        # Extract Subject
        subject_dict = dict(x[0] for x in parsed.get("subject", ()))
        common_name = subject_dict.get("commonName", target)
        org = subject_dict.get("organizationName", "")

        # Extract Issuer
        issuer_dict = dict(x[0] for x in parsed.get("issuer", ()))
        issuer_cn = issuer_dict.get("commonName", "")
        issuer_org = issuer_dict.get("organizationName", "") or issuer_cn

        # Extract SANs
        sans = [san[1] for san in parsed.get("subjectAltName", ()) if san[0] == "DNS"]

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []

        # 1. Certificate Entity (Unique by SHA256 Fingerprint)
        cert_ent = Entity(
            entity_type="certificate",
            value=sha256_fp,
            label=f"Cert: {common_name} ({sha256_fp[:8]}...)",
            confidence=1.0,
            source="TLS Inspector",
            properties={
                "common_name": common_name,
                "sha256_fingerprint": sha256_fp,
                "issuer": issuer_org or issuer_cn,
                "valid_from": parsed.get("notBefore", ""),
                "valid_to": parsed.get("notAfter", ""),
                "serial_number": parsed.get("serialNumber", ""),
                "san_count": len(sans),
            },
        )
        entities.append(cert_ent)

        relationships.append(
            EntityRelationship(
                source_entity_id=entity.id,
                target_entity_id=cert_ent.id,
                relationship_type="has_certificate",
                confidence=1.0,
                source="TLS Inspector",
                label="tls_certificate",
            )
        )

        # 2. Issuer Organization Entity
        if issuer_org:
            issuer_ent = Entity(
                entity_type="company",
                value=issuer_org,
                label=f"Issuer: {issuer_org}",
                confidence=1.0,
                source="TLS Inspector",
                properties={"role": "Certificate Authority", "issuer_for": common_name},
            )
            entities.append(issuer_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=cert_ent.id,
                    target_entity_id=issuer_ent.id,
                    relationship_type="issued_by",
                    confidence=1.0,
                    source="TLS Inspector",
                    label="ca_issuer",
                )
            )

        # 3. Discovered SAN Domains
        for san in sans[:30]:
            san_clean = san.lstrip("*.").lower()
            if san_clean and san_clean != target:
                san_ent = Entity(
                    entity_type="domain" if san_clean.count(".") == 1 else "subdomain",
                    value=san_clean,
                    label=san_clean,
                    confidence=0.95,
                    source="TLS Inspector",
                    properties={"discovered_via_san": True, "certificate": sha256_fp},
                )
                entities.append(san_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=cert_ent.id,
                        target_entity_id=san_ent.id,
                        relationship_type="covers_san",
                        confidence=0.95,
                        source="TLS Inspector",
                        label="san_domain",
                    )
                )

        return entities, relationships, {
            "target": target,
            "sha256": sha256_fp,
            "subject": subject_dict,
            "issuer": issuer_dict,
            "sans": sans[:30],
        }
