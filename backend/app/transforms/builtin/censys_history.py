import httpx
import base64
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CensysHistoryAdapter(BaseTransform):
    id = "builtin.censys.history"
    name = "Censys Historical Observations"
    description = "Retrieves historical open ports and observations for an IP via Censys (Requires API Key)"
    category = "Historical Intelligence"
    
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
            
        url = f"https://search.censys.io/api/v2/hosts/{target}/events?per_page=50"
        auth_str = base64.b64encode(f"{api_id}:{api_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return [], [], {"message": "No historical Censys records found for this IP."}
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid Censys API Credentials."}
                if resp.status_code != 200:
                    return [], [], {"error": f"Censys API returned {resp.status_code}"}
                    
                events = resp.json().get("result", {}).get("events", [])
                
                seen_ports = set()
                
                for event in events:
                    if event.get("_event") == "service_observation":
                        port = event.get("port")
                        service = event.get("service_name")
                        
                        if port and port not in seen_ports:
                            seen_ports.add(port)
                            
                            port_ent = Entity(
                                entity_type="port",
                                value=str(port),
                                label=f"Historical Port {port}",
                                confidence=0.8,
                                source="Censys History"
                            )
                            results.append(port_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=port_ent.id,
                                    relationship_type="had_open_port_historically",
                                    confidence=0.8,
                                    source="Censys History"
                                )
                            )
                            
                            if service:
                                svc_ent = Entity(
                                    entity_type="service",
                                    value=service,
                                    label=f"Service: {service}",
                                    confidence=0.8,
                                    source="Censys History"
                                )
                                results.append(svc_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=port_ent.id,
                                        target_entity_id=svc_ent.id,
                                        relationship_type="ran_service_historically",
                                        confidence=0.8,
                                        source="Censys History"
                                    )
                                )
                                
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} historical ports across {len(events)} events."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
