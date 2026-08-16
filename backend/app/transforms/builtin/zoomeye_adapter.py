import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class ZoomEyeAdapter(BaseTransform):
    id = "builtin.zoomeye"
    name = "ZoomEye Host Search"
    description = "Searches ZoomEye for open ports and services on an IP (Requires API Key)"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["port", "service"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_key = params.get("api_keys", {}).get("ZOOMEYE_API_KEY")
        if not api_key:
            return [], [], {"error": "ZOOMEYE_API_KEY is required."}
            
        url = f"https://api.zoomeye.org/host/search?query=ip:{target}"
        headers = {
            "API-KEY": api_key,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid ZoomEye API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"ZoomEye API returned {resp.status_code}"}
                    
                data = resp.json()
                matches = data.get("matches", [])
                
                if not matches:
                    return [], [], {"message": "No ZoomEye records found for this IP."}
                    
                seen_ports = set()
                
                for item in matches:
                    portinfo = item.get("portinfo", {})
                    port = portinfo.get("port")
                    service = portinfo.get("service")
                    
                    if port and port not in seen_ports:
                        seen_ports.add(port)
                        port_ent = Entity(
                            entity_type="port",
                            value=str(port),
                            label=f"Port {port}",
                            confidence=1.0,
                            source="ZoomEye"
                        )
                        results.append(port_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=port_ent.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="ZoomEye"
                            )
                        )
                        
                        if service:
                            svc_ent = Entity(
                                entity_type="service",
                                value=service,
                                label=f"Service: {service}",
                                confidence=0.9,
                                source="ZoomEye"
                            )
                            results.append(svc_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=port_ent.id,
                                    target_entity_id=svc_ent.id,
                                    relationship_type="runs_service",
                                    confidence=0.9,
                                    source="ZoomEye"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} open ports."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
