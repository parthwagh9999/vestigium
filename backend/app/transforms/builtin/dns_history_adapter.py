import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class DNSHistoryAdapter(BaseTransform):
    id = "builtin.dns_history"
    name = "Passive DNS & History (HackerTarget)"
    description = "Retrieves historical IP addresses for a domain via Passive DNS"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain", "subdomain"]
    output_entity_types = ["ip_address"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = f"https://api.hackertarget.com/passivedns/?q={target}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"HackerTarget API returned {resp.status_code}"}
                    
                text = resp.text
                if "error" in text.lower() or "no records" in text.lower():
                    return [], [], {"message": text.strip()}
                    
                for line in text.splitlines():
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        hostname, ip = parts
                        if hostname.lower() == target.lower():
                            ip_ent = Entity(
                                entity_type="ip_address",
                                value=ip,
                                label="Historical IP",
                                confidence=0.7,
                                source="HackerTarget Passive DNS"
                            )
                            results.append(ip_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=ip_ent.id,
                                    relationship_type="historical_resolution",
                                    confidence=0.7,
                                    source="HackerTarget Passive DNS"
                                )
                            )
                            
                return results, relationships, {"raw_output": text[:2000]}
                
        except Exception as e:
            return [], [], {"error": str(e)}
