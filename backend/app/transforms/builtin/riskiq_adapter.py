import httpx
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class RiskIQAdapter(BaseTransform):
    id = "builtin.riskiq"
    name = "RiskIQ/PassiveTotal Subdomain Search"
    description = "Searches PassiveTotal for subdomains (Requires API Key & Secret)"
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
            
        api_key = params.get("api_keys", {}).get("RISKIQ_API_KEY")
        api_secret = params.get("api_keys", {}).get("RISKIQ_API_SECRET")
        
        if not api_key or not api_secret:
            return [], [], {"error": "RISKIQ_API_KEY and RISKIQ_API_SECRET are required."}
            
        url = f"https://api.passivetotal.org/v2/enrichment/subdomains?query={target}"
        
        try:
            # httpx supports basic auth via auth=(username, password)
            async with httpx.AsyncClient(timeout=15.0, auth=(api_key, api_secret)) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid RiskIQ API credentials."}
                if resp.status_code != 200:
                    return [], [], {"error": f"RiskIQ API returned {resp.status_code}"}
                    
                data = resp.json()
                subdomains = data.get("subdomains", [])
                
                seen_subs = set()
                
                for prefix in subdomains:
                    if not prefix or prefix == "*":
                        continue
                        
                    full_subdomain = f"{prefix}.{target}"
                    
                    if full_subdomain not in seen_subs:
                        seen_subs.add(full_subdomain)
                        
                        sub_ent = Entity(
                            entity_type="subdomain",
                            value=full_subdomain,
                            label="Subdomain",
                            confidence=1.0,
                            source="RiskIQ"
                        )
                        results.append(sub_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=sub_ent.id,
                                relationship_type="subdomain_of",
                                confidence=1.0,
                                source="RiskIQ"
                            )
                        )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_subs)} subdomains."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
