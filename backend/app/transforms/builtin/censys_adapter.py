import httpx
import base64
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CensysAdapter(BaseTransform):
    id = "builtin.censys"
    name = "Censys Host Search"
    description = "Searches Censys for open ports and services on an IP (Requires API Key)"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["port", "service"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_id = params.get("api_keys", {}).get("CENSYS_API_ID")
        api_secret = params.get("api_keys", {}).get("CENSYS_API_SECRET")
        if not api_id or not api_secret:
            return [], [], {"error": "CENSYS_API_ID and CENSYS_API_SECRET are required."}
            
        url = f"https://search.censys.io/api/v2/hosts/{target}"
        auth_str = base64.b64encode(f"{api_id}:{api_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return [], [], {"message": "No Censys record found for this IP."}
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid Censys API Credentials."}
                if resp.status_code != 200:
                    return [], [], {"error": f"Censys API returned {resp.status_code}"}
                    
                data = resp.json().get("result", {})
                services = data.get("services", [])
                
                seen_ports = set()
                
                for svc in services:
                    port = svc.get("port")
                    svc_name = svc.get("service_name")
                    
                    if port and port not in seen_ports:
                        seen_ports.add(port)
                        port_ent = Entity(
                            entity_type="port",
                            value=str(port),
                            label=f"Port {port}",
                            confidence=1.0,
                            source="Censys"
                        )
                        results.append(port_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=port_ent.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="Censys"
                            )
                        )
                        
                        if svc_name:
                            svc_ent = Entity(
                                entity_type="service",
                                value=svc_name,
                                label=f"Service: {svc_name}",
                                confidence=0.9,
                                source="Censys"
                            )
                            results.append(svc_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=port_ent.id,
                                    target_entity_id=svc_ent.id,
                                    relationship_type="runs_service",
                                    confidence=0.9,
                                    source="Censys"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} open ports."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
