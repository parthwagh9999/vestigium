import httpx
import base64
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class FofaAdapter(BaseTransform):
    id = "builtin.fofa"
    name = "FOFA Host Search"
    description = "Searches FOFA for open ports and services on an IP (Requires API Key)"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["port", "service"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_key = params.get("api_keys", {}).get("FOFA_API_KEY")
        if not api_key:
            return [], [], {"error": "FOFA_API_KEY is required."}
            
        query = f'ip="{target}"'
        qbase64 = base64.b64encode(query.encode()).decode()
        
        url = f"https://fofa.info/api/v1/search/all?key={api_key}&qbase64={qbase64}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid FOFA API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"FOFA API returned {resp.status_code}"}
                    
                data = resp.json()
                if data.get("error"):
                    return [], [], {"error": data.get("errmsg", "FOFA API Error")}
                    
                results_data = data.get("results", [])
                
                if not results_data:
                    return [], [], {"message": "No FOFA records found for this IP."}
                    
                seen_ports = set()
                
                for item in results_data:
                    if len(item) >= 3:
                        port = item[2] # FOFA default fields: host, ip, port
                        
                        if port and port not in seen_ports:
                            seen_ports.add(port)
                            port_ent = Entity(
                                entity_type="port",
                                value=str(port),
                                label=f"Port {port}",
                                confidence=1.0,
                                source="FOFA"
                            )
                            results.append(port_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=port_ent.id,
                                    relationship_type="has_open_port",
                                    confidence=1.0,
                                    source="FOFA"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_ports)} open ports."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
