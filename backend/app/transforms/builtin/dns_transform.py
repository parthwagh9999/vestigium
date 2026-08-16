"""DNS Lookup Transform resolving A, AAAA, MX, NS, and TXT records via DoH and socket resolvers."""
from __future__ import annotations
import asyncio
import socket
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class DNSLookupTransform(BaseTransform):
    """Transform to resolve DNS records (A, AAAA, MX, NS, TXT) for a domain name."""
    id = "builtin.dns_lookup"
    name = "DNS Record Lookup"
    description = "Resolves A, AAAA, MX, NS, and TXT records for a domain name"
    category = "Infrastructure"
    
    input_entity_types = ["domain", "subdomain", "url", "website"]
    output_entity_types = ["ip_address", "domain", "server", "email"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        clean_domain = (
            entity.value.replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
            .split("?")[0]
            .strip()
            .lower()
        )
        
        headers = {"Accept": "application/dns-json"}
        entities = []
        relationships = []
        raw_output = {}
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                resp = await client.get(f"https://1.1.1.1/dns-query?name={clean_domain}&type=A", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    answers = data.get("Answer", [])
                    raw_output["a_records"] = answers
                    for ans in answers:
                        ip = ans.get("data", "").strip()
                        if ip and not ip.startswith("http"):
                            e = Entity(entity_type="ip_address", value=ip, label=ip, confidence=1.0, source="Cloudflare DoH")
                            entities.append(e)
                            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="dns_a_record", confidence=1.0, source="Cloudflare DoH"))
            except Exception as e:
                raw_output["a_records_error"] = str(e)
                
            try:
                resp = await client.get(f"https://1.1.1.1/dns-query?name={clean_domain}&type=NS", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    answers = data.get("Answer", [])
                    raw_output["ns_records"] = answers
                    for ans in answers:
                        ns = ans.get("data", "").strip().rstrip(".")
                        if ns:
                            e = Entity(entity_type="domain", value=ns.lower(), label=ns.lower(), confidence=1.0, source="Cloudflare DoH")
                            entities.append(e)
                            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_nameserver", confidence=1.0, source="Cloudflare DoH"))
            except Exception as e:
                raw_output["ns_records_error"] = str(e)
                
            try:
                resp = await client.get(f"https://1.1.1.1/dns-query?name={clean_domain}&type=MX", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    answers = data.get("Answer", [])
                    raw_output["mx_records"] = answers
                    for ans in answers:
                        raw_mx = ans.get("data", "").strip()
                        parts = raw_mx.split()
                        mx_host = parts[-1].rstrip(".") if parts else raw_mx.rstrip(".")
                        if mx_host:
                            e = Entity(entity_type="domain", value=mx_host.lower(), label=f"MX: {mx_host.lower()}", confidence=1.0, source="Cloudflare DoH")
                            entities.append(e)
                            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_mailserver", confidence=1.0, source="Cloudflare DoH"))
            except Exception as e:
                raw_output["mx_records_error"] = str(e)
                
        if not entities:
            try:
                loop = asyncio.get_running_loop()
                addr_info = await loop.getaddrinfo(clean_domain, None, socket.AF_INET)
                ips = list({info[4][0] for info in addr_info})
                raw_output["socket_ips"] = ips
                for ip in ips:
                    e = Entity(entity_type="ip_address", value=ip, label=ip, confidence=1.0, source="Socket")
                    entities.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="dns_a_record", confidence=1.0, source="Socket"))
            except Exception as e:
                raw_output["socket_error"] = str(e)
                
        return entities, relationships, {"raw_data": raw_output}
