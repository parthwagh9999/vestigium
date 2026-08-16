import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class ThreatFoxAdapter(BaseTransform):
    id = "builtin.threatfox"
    name = "ThreatFox IOC Search"
    description = "Searches Abuse.ch ThreatFox for malware indicators associated with an IP or Domain"
    category = "Threat Intelligence"
    
    input_entity_types = ["domain", "ip_address", "ipv6_address", "url"]
    output_entity_types = ["malware"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = "https://threatfox-api.abuse.ch/api/v1/"
        
        payload = {
            "query": "search_ioc",
            "search_term": target
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    return [], [], {"error": f"ThreatFox API returned {resp.status_code}"}
                    
                data = resp.json()
                if data.get("query_status") != "ok" or not data.get("data"):
                    return [], [], {"message": "No malware indicators found."}
                    
                seen_malware = set()
                
                for item in data.get("data", []):
                    malware_name = item.get("malware_printable") or item.get("malware")
                    if not malware_name or malware_name in seen_malware:
                        continue
                        
                    seen_malware.add(malware_name)
                    
                    confidence = item.get("confidence_level", 50) / 100.0
                    
                    malware_ent = Entity(
                        entity_type="malware",
                        value=malware_name,
                        label="Malware Family",
                        confidence=confidence,
                        source="ThreatFox"
                    )
                    results.append(malware_ent)
                    
                    threat_type = item.get("threat_type_desc", "Malware Indicator")
                    
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=malware_ent.id,
                            relationship_type="distributes_malware" if "payload" in threat_type.lower() else "associated_with_malware",
                            confidence=confidence,
                            source="ThreatFox"
                        )
                    )
                            
                return results, relationships, {"raw_output": str(data)[:2000]}
                
        except Exception as e:
            return [], [], {"error": str(e)}
