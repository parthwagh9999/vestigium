"""AbuseIPDB IP Threat Intelligence transform adapter."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class AbuseIPDBTransform(BaseTransform):
    """AbuseIPDB IP Reputation and Threat Intelligence."""

    id = "builtin.abuseipdb"
    name = "AbuseIPDB Threat Intelligence"
    description = "Check IP address abuse confidence score, total reports, ISP, usage type, and malicious activity history."
    category = "Threat Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "AbuseIPDB API v2"
    documentation_url = "https://docs.abuseipdb.com/"
    license = "Commercial / Free Tier"

    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["ioc", "company", "country"]
    relationships_created = ["has_threat_score", "allocated_to", "located_in"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = True
    requires_api_key = True
    api_key_service = "abuseipdb"
    installation_required = False
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE_WITH_API_KEY"
    configuration_status = "NOT_CONFIGURED"
    timeout = 15
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        api_key = params.get("api_key")

        if not api_key:
            return [], [], {"error": "AbuseIPDB API key not configured. Add your API key in Vault or tool settings.", "status": "CONFIGURATION_REQUIRED"}

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_data: dict[str, Any] = {}

        headers = {
            "Key": api_key,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            try:
                resp = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    raw_data = data

                    abuse_score = data.get("abuseConfidenceScore", 0)
                    total_reports = data.get("totalReports", 0)
                    isp = data.get("isp", "")
                    country_code = data.get("countryCode", "")
                    usage_type = data.get("usageType", "")

                    # 1. Threat Score IOC Entity
                    score_ent = Entity(
                        entity_type="ioc",
                        value=f"ABUSE-{ip}",
                        label=f"Abuse Score: {abuse_score}% ({total_reports} reports)",
                        confidence=1.0,
                        source="AbuseIPDB",
                        properties={
                            "abuse_confidence_score": abuse_score,
                            "total_reports": total_reports,
                            "usage_type": usage_type,
                            "last_reported_at": data.get("lastReportedAt", ""),
                            "is_whitelisted": data.get("isWhitelisted", False),
                        },
                    )
                    entities.append(score_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=score_ent.id,
                            relationship_type="has_threat_score",
                            confidence=1.0,
                            source="AbuseIPDB",
                            label=f"score_{abuse_score}pct",
                        )
                    )

                    # 2. ISP Entity
                    if isp:
                        isp_ent = Entity(
                            entity_type="company",
                            value=isp,
                            label=f"ISP: {isp}",
                            confidence=1.0,
                            source="AbuseIPDB",
                            properties={"isp": isp, "usage_type": usage_type},
                        )
                        entities.append(isp_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=isp_ent.id,
                                relationship_type="allocated_to",
                                confidence=1.0,
                                source="AbuseIPDB",
                                label="isp",
                            )
                        )
                else:
                    raw_data["status_code"] = resp.status_code
                    raw_data["error"] = resp.text
            except Exception as e:
                logger.warning("AbuseIPDB API request error for %s: %s", ip, e)
                raw_data["error"] = str(e)

        return entities, relationships, raw_data
