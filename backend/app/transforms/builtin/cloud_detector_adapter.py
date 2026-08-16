"""Cloud Infrastructure and Public Provider Classifier Transform."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)

# Cloud Provider ASN & Keyword mappings
CLOUD_SIGNATURES = [
    {"name": "Amazon Web Services (AWS)", "keywords": ["amazonaws.com", "awsglobalaccelerator", "amazon", "cloudfront.net"], "asn_keywords": ["AMAZON"]},
    {"name": "Microsoft Azure", "keywords": ["azure.com", "azurewebsites.net", "trafficmanager.net", "azureedge.net"], "asn_keywords": ["MICROSOFT"]},
    {"name": "Google Cloud Platform (GCP)", "keywords": ["googleusercontent.com", "1e100.net", "appspot.com", "gcp"], "asn_keywords": ["GOOGLE"]},
    {"name": "Cloudflare", "keywords": ["cloudflare.com", "cloudflare.net"], "asn_keywords": ["CLOUDFLARE"]},
    {"name": "DigitalOcean", "keywords": ["digitalocean.com", "digitaloceanspaces.com"], "asn_keywords": ["DIGITALOCEAN"]},
    {"name": "Oracle Cloud Infrastructure (OCI)", "keywords": ["oraclecloud.com", "oracle.com"], "asn_keywords": ["ORACLE"]},
    {"name": "Hetzner Online", "keywords": ["hetzner.com", "your-server.de"], "asn_keywords": ["HETZNER"]},
    {"name": "OVHcloud", "keywords": ["ovh.net", "ovhcloud.com"], "asn_keywords": ["OVH"]},
    {"name": "Linode / Akamai Cloud", "keywords": ["linode.com", "linodeobjects.com", "akamai.net"], "asn_keywords": ["LINODE", "AKAMAI"]},
]


class CloudDetectorTransform(BaseTransform):
    """Cloud Asset & Public Infrastructure Classifier."""

    id = "builtin.cloud_detector"
    name = "Cloud Provider & Infrastructure Detector"
    description = "Identify public cloud infrastructure (AWS, Azure, GCP, Cloudflare, DigitalOcean, Oracle) associated with target."
    category = "Cloud & ASN Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "Vestigium Cloud Intelligence / PTR / ASN"
    documentation_url = "https://bgp.he.net/"
    license = "MIT"

    input_entity_types = ["ip_address", "domain", "subdomain", "website"]
    output_entity_types = ["cloud_asset", "company", "asn"]
    relationships_created = ["hosted_on_cloud", "belongs_to_provider"]

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

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        matched_clouds: list[dict[str, str]] = []

        loop = asyncio.get_event_loop()

        # 1. Resolve to IP if domain
        ip = target
        hostname = ""
        is_ip = target.replace(".", "").isdigit() or ":" in target

        if not is_ip:
            try:
                ip = await loop.run_in_executor(None, lambda: socket.gethostbyname(target))
            except Exception:
                pass

        # 2. Reverse DNS PTR lookup
        try:
            ptr_res = await loop.run_in_executor(None, lambda: socket.gethostbyaddr(ip))
            hostname = ptr_res[0].lower()
        except Exception:
            pass

        # 3. Query BGP / ASN info via BGPView API
        asn_name = ""
        asn_number = ""
        async with httpx.AsyncClient(timeout=6.0) as client:
            try:
                resp = await client.get(f"https://api.bgpview.io/ip/{ip}")
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    ptr_list = data.get("ptr_records", [])
                    if ptr_list and not hostname:
                        hostname = ptr_list[0].lower()
                    prefixes = data.get("prefixes", [])
                    if prefixes:
                        asn_info = prefixes[0].get("asn", {})
                        asn_name = asn_info.get("name", "").upper()
                        asn_number = str(asn_info.get("asn", ""))
            except Exception as e:
                logger.debug("BGPView lookup error: %s", e)

        # 4. Match signatures against hostname, target, and ASN
        combined_text = f"{target} {hostname} {asn_name}".lower()

        for cloud in CLOUD_SIGNATURES:
            name = cloud["name"]
            matched = False
            match_reason = ""

            for kw in cloud["keywords"]:
                if kw in combined_text:
                    matched = True
                    match_reason = f"Hostname/domain matched keyword '{kw}'"
                    break

            if not matched:
                for asn_kw in cloud["asn_keywords"]:
                    if asn_kw in asn_name:
                        matched = True
                        match_reason = f"ASN name matched '{asn_kw}' (AS{asn_number})"
                        break

            if matched:
                matched_clouds.append({
                    "provider": name,
                    "reason": match_reason,
                    "ip": ip,
                    "hostname": hostname,
                    "asn": asn_number,
                })

                # Create Cloud Asset Entity
                cloud_ent = Entity(
                    entity_type="cloud_asset",
                    value=f"{name} ({ip})",
                    label=f"Cloud: {name}",
                    confidence=0.95,
                    source="Cloud Detector",
                    properties={
                        "provider": name,
                        "ip": ip,
                        "hostname": hostname,
                        "asn": f"AS{asn_number}" if asn_number else "",
                        "match_reason": match_reason,
                    },
                )
                entities.append(cloud_ent)

                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=cloud_ent.id,
                        relationship_type="hosted_on_cloud",
                        confidence=0.95,
                        source="Cloud Detector",
                        label="cloud_infrastructure",
                    )
                )

        return entities, relationships, {
            "target": target,
            "ip": ip,
            "hostname": hostname,
            "asn_name": asn_name,
            "asn_number": asn_number,
            "matched_providers": matched_clouds,
        }
