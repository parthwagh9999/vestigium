import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CriminalIPAdapter(BaseTransform):
    id = "builtin.criminalip"
    name = "Criminal IP Threat Intel"
    description = "Searches Criminal IP for open ports and threat intel on an IP (Requires API Key)"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["port", "service"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_key = params.get("api_keys", {}).get("CRIMINALIP_API_KEY")
        if not api_key:
            return [], [], {"error": "CRIMINALIP_API_KEY is required."}
            
        url = f"https://api.criminalip.io/v1/asset/ip/report?ip={target}"
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid Criminal IP API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"Criminal IP API returned {resp.status_code}"}
                    
                data = resp.json()
                port_data = data.get("port", {})
                open_ports = port_data.get("data", [])
                
                if not open_ports:
                    return [], [], {"message": "No open ports found on Criminal IP."}
                    
                seen_ports = set()
                
                for item in open_ports:
                    port = item.get("port")
                    protocol = item.get("protocol")
                    app_name = item.get("app_name")
                    
                    if port and port not in seen_ports:
                        seen_ports.add(port)
                        port_ent = Entity(
                            entity_type="port",
                            value=str(port),
                            label=f"Port {port}",
                            confidence=1.0,
                            source="Criminal IP"
                        )
                        results.append(port_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=port_ent.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="Criminal IP"
                            )
                        )
                        
                        svc_name = app_name or protocol
                        if svc_name:
                            svc_ent = Entity(
                                entity_type="service",
                                value=svc_name,
                                label=f"Service: {svc_name}",
                                confidence=0.9,
                                source="Criminal IP"
                            )
                            results.append(svc_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=port_ent.id,
                                    target_entity_id=svc_ent.id,
                                    relationship_type="runs_service",
                                    confidence=0.9,
                                    source="Criminal IP"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} open ports."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
