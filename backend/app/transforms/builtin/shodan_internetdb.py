"""Shodan InternetDB Transform for IP address open ports, CVEs, and hostnames."""
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class ShodanInternetDBTransform(BaseTransform):
    """Transform to query Shodan's free InternetDB for open ports, vulnerabilities (CVEs), and hostnames."""
    id = "builtin.shodan_internetdb"
    name = "Shodan InternetDB Query"
    description = "Discovers open ports, vulnerabilities (CVEs), hostnames, and CPEs using Shodan InternetDB"
    category = "Threat Intelligence"
    
    input_entity_types = ["ip_address"]
    output_entity_types = ["cve", "domain", "subdomain", "service"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        url = f"https://internetdb.shodan.io/{ip}"
        
        entities = []
        relationships = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return [], [], {"message": "No open ports or vulnerabilities found in Shodan InternetDB"}
                if resp.status_code != 200:
                    raise RuntimeError(f"Shodan InternetDB returned status code {resp.status_code}")
                data = resp.json()
                
            for port in data.get("ports", []):
                e = Entity(entity_type="service", value=f"Port {port}", label=f"Port {port}", confidence=1.0, source="Shodan")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="open_port", confidence=1.0, source="Shodan"))
                
            for host in data.get("hostnames", []):
                ent_type = "domain" if len(host.split(".")) == 2 else "subdomain"
                e = Entity(entity_type=ent_type, value=host.lower(), label=host.lower(), confidence=1.0, source="Shodan")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="host_name", confidence=1.0, source="Shodan"))
                
            for cve in data.get("vulns", [])[:20]:
                e = Entity(entity_type="cve", value=cve, label=cve, confidence=1.0, source="Shodan")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="vulnerable_to", confidence=1.0, source="Shodan"))
                
            return entities, relationships, {"raw_data": data}
            
        except Exception as e:
            raise RuntimeError(f"Shodan InternetDB request failed: {e}")
