"""Subdomain enumeration transform using Certificate Transparency logs."""
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class SubdomainEnumTransform(BaseTransform):
    """Transform to discover subdomains via Certificate Transparency (CT) logs."""
    id = "builtin.subdomain_enum"
    name = "Subdomain Search (CT Logs)"
    description = "Discovers subdomains associated with a root domain using Certificate Transparency logs"
    category = "Infrastructure"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain", "domain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        domain = entity.value.replace("https://", "").replace("http://", "").split("/")[0].strip().lower()
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        
        entities = []
        relationships = []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"crt.sh returned status code {resp.status_code}"}
                data = resp.json()
                
            found_subdomains: set[str] = set()
            for entry in data:
                name_value = entry.get("name_value", "")
                for name in name_value.split("\n"):
                    name_clean = name.strip().lower()
                    if name_clean and "*" not in name_clean and name_clean.endswith(domain) and name_clean != domain:
                        found_subdomains.add(name_clean)
                        
            for sub in list(found_subdomains)[:50]:
                e = Entity(entity_type="subdomain", value=sub, label=sub, confidence=0.9, source="crt.sh")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="subdomain_of", confidence=0.9, source="crt.sh"))
                
            return entities, relationships, {"raw_data": {"count": len(found_subdomains), "subdomains": list(found_subdomains)}}
        except Exception as e:
            return [], [], {"error": f"Subdomain enumeration failed: {e}"}
