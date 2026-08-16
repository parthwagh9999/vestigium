import httpx
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CertSpotterAdapter(BaseTransform):
    id = "builtin.certspotter"
    name = "CertSpotter CT Search"
    description = "Searches CertSpotter Certificate Transparency logs for subdomains"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain", "subdomain"]
    output_entity_types = ["subdomain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            
        url = f"https://api.certspotter.com/v1/issuances?domain={target}&include_subdomains=true&expand=dns_names"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 429:
                    return [], [], {"error": "CertSpotter API rate limit exceeded."}
                if resp.status_code != 200:
                    return [], [], {"error": f"CertSpotter API returned {resp.status_code}"}
                    
                data = resp.json()
                if not isinstance(data, list):
                    return [], [], {"error": "Unexpected API response format"}
                    
                seen_subs = set()
                
                for issuance in data:
                    for dns_name in issuance.get("dns_names", []):
                        dns_name = dns_name.lower().lstrip('*').lstrip('.')
                        if dns_name.endswith(target) and dns_name != target and dns_name not in seen_subs:
                            seen_subs.add(dns_name)
                            
                            sub_ent = Entity(
                                entity_type="subdomain",
                                value=dns_name,
                                label="Subdomain",
                                confidence=1.0,
                                source="CertSpotter"
                            )
                            results.append(sub_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=sub_ent.id,
                                    relationship_type="subdomain_of",
                                    confidence=1.0,
                                    source="CertSpotter"
                                )
                            )
                            
                return results, relationships, {"raw_output": str(data)[:2000]}
                
        except Exception as e:
            return [], [], {"error": str(e)}
