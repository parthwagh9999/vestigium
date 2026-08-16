"""HackerTarget Transforms for Reverse IP lookup and Host Search."""
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class ReverseIPTransform(BaseTransform):
    """Transform to discover other domains co-hosted on the same IP address."""
    id = "builtin.reverse_ip_lookup"
    name = "Reverse IP Lookup (Co-hosted Domains)"
    description = "Finds other domains co-hosted on the same IP address using HackerTarget"
    category = "Infrastructure"
    
    input_entity_types = ["ip_address"]
    output_entity_types = ["domain", "subdomain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        url = f"https://api.hackertarget.com/reverseiplookup/?q={ip}"
        
        entities = []
        relationships = []
        
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise RuntimeError(f"HackerTarget returned status code {resp.status_code}")
                text = resp.text.strip()
                
            if "No records found" in text or "error" in text.lower() or "API count exceeded" in text:
                return [], [], {"message": text}
                
            domains = [line.strip().lower() for line in text.split("\n") if line.strip()]
            
            for d in domains[:30]:
                ent_type = "domain" if len(d.split(".")) == 2 else "subdomain"
                e = Entity(entity_type=ent_type, value=d, label=d, confidence=1.0, source="HackerTarget")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="co_hosted_with", confidence=1.0, source="HackerTarget"))
                
            return entities, relationships, {"raw_data": {"domains": domains}}
        except Exception as e:
            raise RuntimeError(f"Reverse IP lookup failed: {e}")
