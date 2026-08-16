import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class SecurityTrailsHistoryAdapter(BaseTransform):
    id = "builtin.securitytrails.history"
    name = "SecurityTrails Historical DNS"
    description = "Searches SecurityTrails for historical DNS records (Requires API Key)"
    category = "Historical Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["ip_address", "ipv6_address", "mail_server"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        api_key = params.get("api_keys", {}).get("SECURITYTRAILS_API_KEY")
        if not api_key:
            return [], [], {"error": "SECURITYTRAILS_API_KEY is required."}
            
        headers = {
            "APIKEY": api_key,
            "Accept": "application/json"
        }
        
        seen_ips = set()
        seen_mx = set()
        
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                
                # Fetch A records
                a_url = f"https://api.securitytrails.com/v1/history/{target}/dns/a"
                resp = await client.get(a_url)
                if resp.status_code == 200:
                    records = resp.json().get("records", [])
                    for rec in records:
                        for value in rec.get("values", []):
                            ip = value.get("ip")
                            if ip and ip not in seen_ips:
                                seen_ips.add(ip)
                                ip_ent = Entity(
                                    entity_type="ip_address",
                                    value=ip,
                                    label="Historical IP",
                                    confidence=1.0,
                                    source="SecurityTrails"
                                )
                                results.append(ip_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=ip_ent.id,
                                        relationship_type="resolved_to_historically",
                                        confidence=1.0,
                                        source="SecurityTrails"
                                    )
                                )
                                
                # Fetch MX records
                mx_url = f"https://api.securitytrails.com/v1/history/{target}/dns/mx"
                resp = await client.get(mx_url)
                if resp.status_code == 200:
                    records = resp.json().get("records", [])
                    for rec in records:
                        for value in rec.get("values", []):
                            mx = value.get("host")
                            if mx and mx not in seen_mx:
                                seen_mx.add(mx)
                                mx_ent = Entity(
                                    entity_type="mail_server",
                                    value=mx,
                                    label="Historical MX",
                                    confidence=1.0,
                                    source="SecurityTrails"
                                )
                                results.append(mx_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=mx_ent.id,
                                        relationship_type="used_mx_historically",
                                        confidence=1.0,
                                        source="SecurityTrails"
                                    )
                                )
                                
                return results, relationships, {"raw_output": f"Found {len(seen_ips)} historical IPs and {len(seen_mx)} MX records."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
