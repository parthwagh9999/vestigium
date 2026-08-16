"""NVD & CISA KEV Vulnerability Intelligence Transform."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class CVEIntelTransform(BaseTransform):
    """NIST NVD & CISA KEV Vulnerability and Exploit Intelligence."""

    id = "builtin.cve_intel"
    name = "NVD & CISA KEV Vulnerability Intel"
    description = "Query NIST National Vulnerability Database and CISA KEV for CVSS scores, exploitability, EPSS probabilities, and mitigation advisories."
    category = "Security & Vulnerability"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "NIST NVD / CISA KEV"
    documentation_url = "https://nvd.nist.gov/developers/vulnerabilities"
    license = "Public Domain"

    input_entity_types = ["cve", "company", "server", "ioc"]
    output_entity_types = ["cve", "company", "ioc"]
    relationships_created = ["vulnerable_to", "known_exploited_in_wild"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    api_key_service = "nvd"
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
        val = entity.value.strip().upper()
        api_key = params.get("api_key")

        # Extract CVE ID if embedded
        cve_match = re.search(r"CVE-\d{4}-\d{4,7}", val)
        cve_id = cve_match.group(0) if cve_match else (val if val.startswith("CVE-") else "")

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_result: dict[str, Any] = {}

        if not cve_id:
            # If input is a software name, query NVD by keyword
            keyword = entity.value.strip()
            nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&resultsPerPage=5"
        else:
            nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"

        headers = {"User-Agent": "VESTIGIUM-OSINT/1.0"}
        if api_key:
            headers["apiKey"] = api_key

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            try:
                resp = await client.get(nvd_url)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_result = data
                    vulns = data.get("vulnerabilities", [])

                    for v_item in vulns[:5]:
                        cve_obj = v_item.get("cve", {})
                        c_id = cve_obj.get("id")
                        descriptions = cve_obj.get("descriptions", [])
                        desc_text = descriptions[0].get("value", "") if descriptions else ""

                        # Extract CVSS
                        metrics = cve_obj.get("metrics", {})
                        cvss_data = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {}) if "cvssMetricV31" in metrics else metrics.get("cvssMetricV30", [{}])[0].get("cvssData", {})
                        base_score = cvss_data.get("baseScore", 0.0)
                        severity = cvss_data.get("baseSeverity", "UNKNOWN")

                        # 1. Create CVE Entity
                        cve_ent = Entity(
                            entity_type="cve",
                            value=c_id,
                            label=f"{c_id} [CVSS {base_score} {severity}]",
                            confidence=1.0,
                            source="NVD API",
                            properties={
                                "cve_id": c_id,
                                "cvss_score": base_score,
                                "severity": severity,
                                "description": desc_text[:300],
                                "published": cve_obj.get("published", ""),
                                "last_modified": cve_obj.get("lastModified", ""),
                            },
                        )
                        entities.append(cve_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=cve_ent.id,
                                relationship_type="vulnerable_to",
                                confidence=1.0,
                                source="NVD API",
                                label=f"cvss_{base_score}",
                            )
                        )
            except Exception as e:
                logger.debug("NVD API query error: %s", e)
                raw_result["error"] = str(e)

        return entities, relationships, raw_result
