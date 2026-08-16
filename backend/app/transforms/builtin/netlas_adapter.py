import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class NetlasAdapter(BaseTransform):
    id = "builtin.netlas"
    name = "Netlas Host Search"
    description = "Searches Netlas.io for open ports and services on an IP (Requires API Key)"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["port", "service"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_key = params.get("api_keys", {}).get("NETLAS_API_KEY")
        if not api_key:
            return [], [], {"error": "NETLAS_API_KEY is required."}
            
        url = f"https://app.netlas.io/api/responses/?q=ip:{target}"
        headers = {
            "X-Api-Key": api_key,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid Netlas API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"Netlas API returned {resp.status_code}"}
                    
                data = resp.json()
                items = data.get("items", [])
                
                if not items:
                    return [], [], {"message": "No Netlas records found for this IP."}
                    
                seen_ports = set()
                
                for item in items:
                    port = item.get("data", {}).get("port")
                    protocol = item.get("data", {}).get("protocol")
                    
                    if port and port not in seen_ports:
                        seen_ports.add(port)
                        port_ent = Entity(
                            entity_type="port",
                            value=str(port),
                            label=f"Port {port}",
                            confidence=1.0,
                            source="Netlas"
                        )
                        results.append(port_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=port_ent.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="Netlas"
                            )
                        )
                        
                        if protocol:
                            svc_ent = Entity(
                                entity_type="service",
                                value=protocol,
                                label=f"Service: {protocol}",
                                confidence=0.9,
                                source="Netlas"
                            )
                            results.append(svc_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=port_ent.id,
                                    target_entity_id=svc_ent.id,
                                    relationship_type="runs_service",
                                    confidence=0.9,
                                    source="Netlas"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} open ports."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
