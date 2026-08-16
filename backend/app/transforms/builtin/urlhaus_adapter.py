import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class URLhausAdapter(BaseTransform):
    id = "builtin.urlhaus"
    name = "URLhaus Malware Search"
    description = "Searches Abuse.ch URLhaus for malware URLs hosted on an IP or Domain"
    category = "Threat Intelligence"
    
    input_entity_types = ["domain", "ip_address", "ipv6_address"]
    output_entity_types = ["url", "malware"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = "https://urlhaus-api.abuse.ch/v1/host/"
        
        payload = {
            "host": target
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, data=payload)
                if resp.status_code != 200:
                    return [], [], {"error": f"URLhaus API returned {resp.status_code}"}
                    
                data = resp.json()
                if data.get("query_status") != "ok" or not data.get("urls"):
                    return [], [], {"message": "No malware URLs found."}
                    
                seen_urls = set()
                
                for item in data.get("urls", []):
                    malicious_url = item.get("url")
                    if not malicious_url or malicious_url in seen_urls:
                        continue
                        
                    seen_urls.add(malicious_url)
                    
                    status = item.get("url_status", "unknown")
                    confidence = 1.0 if status == "online" else 0.7
                    
                    url_ent = Entity(
                        entity_type="url",
                        value=malicious_url,
                        label="Malicious URL",
                        confidence=confidence,
                        source="URLhaus"
                    )
                    results.append(url_ent)
                    
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=url_ent.id,
                            relationship_type="hosts_malicious_url",
                            confidence=confidence,
                            source="URLhaus"
                        )
                    )
                    
                    # If tags exist, treat them as generic malware/threat actors
                    tags = item.get("tags")
                    if tags and isinstance(tags, list):
                        for tag in tags:
                            if not tag:
                                continue
                            tag_ent = Entity(
                                entity_type="malware",
                                value=tag,
                                label="Malware Tag",
                                confidence=0.8,
                                source="URLhaus"
                            )
                            results.append(tag_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=url_ent.id,
                                    target_entity_id=tag_ent.id,
                                    relationship_type="distributes_malware",
                                    confidence=0.8,
                                    source="URLhaus"
                                )
                            )
                            
                return results, relationships, {"raw_output": str(data)[:2000]}
                
        except Exception as e:
            return [], [], {"error": str(e)}
