import httpx
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class SecurityTrailsAdapter(BaseTransform):
    id = "builtin.securitytrails"
    name = "SecurityTrails Subdomain Search"
    description = "Searches SecurityTrails for subdomains (Requires API Key)"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            
        api_key = params.get("api_keys", {}).get("SECURITYTRAILS_API_KEY")
        if not api_key:
            return [], [], {"error": "SECURITYTRAILS_API_KEY is required."}
            
        url = f"https://api.securitytrails.com/v1/domain/{target}/subdomains?children_only=false&include_inactive=true"
        headers = {
            "APIKEY": api_key,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid SecurityTrails API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"SecurityTrails API returned {resp.status_code}"}
                    
                data = resp.json()
                subdomains = data.get("subdomains", [])
                
                seen_subs = set()
                
                for prefix in subdomains:
                    if not prefix:
                        continue
                    
                    full_subdomain = f"{prefix}.{target}"
                    
                    if full_subdomain not in seen_subs:
                        seen_subs.add(full_subdomain)
                        
                        sub_ent = Entity(
                            entity_type="subdomain",
                            value=full_subdomain,
                            label="Subdomain",
                            confidence=1.0,
                            source="SecurityTrails"
                        )
                        results.append(sub_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=sub_ent.id,
                                relationship_type="subdomain_of",
                                confidence=1.0,
                                source="SecurityTrails"
                            )
                        )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_subs)} subdomains."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
