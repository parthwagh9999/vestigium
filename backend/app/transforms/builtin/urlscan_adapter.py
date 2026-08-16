import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class URLScanAdapter(BaseTransform):
    id = "builtin.urlscan"
    name = "urlscan.io Historical Search"
    description = "Retrieves historical IPs and technologies for a domain using URLScan.io"
    category = "Historical Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["ip_address", "technology"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        api_key = params.get("api_keys", {}).get("URLSCAN_API_KEY")
        headers = {}
        if api_key:
            headers["API-Key"] = api_key
            
        url = f"https://urlscan.io/api/v1/search/?q=domain:{target}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 429:
                    return [], [], {"error": "urlscan.io rate limit exceeded."}
                if resp.status_code != 200:
                    return [], [], {"error": f"urlscan.io API returned {resp.status_code}"}
                    
                data = resp.json()
                results_list = data.get("results", [])
                
                if not results_list:
                    return [], [], {"message": "No historical records found on urlscan.io."}
                    
                seen_ips = set()
                seen_techs = set()
                
                for res in results_list:
                    page = res.get("page", {})
                    ip = page.get("ip")
                    server = page.get("server")
                    
                    if ip and ip not in seen_ips:
                        seen_ips.add(ip)
                        ip_ent = Entity(
                            entity_type="ip_address",
                            value=ip,
                            label="Historical IP",
                            confidence=0.9,
                            source="urlscan.io"
                        )
                        results.append(ip_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=ip_ent.id,
                                relationship_type="resolved_to_historically",
                                confidence=0.9,
                                source="urlscan.io"
                            )
                        )
                        
                    if server and server not in seen_techs:
                        seen_techs.add(server)
                        tech_ent = Entity(
                            entity_type="technology",
                            value=server,
                            label=f"{server} (Tech)",
                            confidence=0.9,
                            source="urlscan.io"
                        )
                        tech_ent.properties = {"software": server}
                        results.append(tech_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=tech_ent.id,
                                relationship_type="used_technology_historically",
                                confidence=0.9,
                                source="urlscan.io"
                            )
                        )
                        
                return results, relationships, {"raw_output": f"Found {len(seen_ips)} historical IPs and {len(seen_techs)} technologies."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
