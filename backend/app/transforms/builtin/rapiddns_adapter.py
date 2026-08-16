import httpx
import re
import urllib.parse
from typing import Any
from bs4 import BeautifulSoup

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class RapidDNSAdapter(BaseTransform):
    id = "builtin.rapiddns"
    name = "RapidDNS Search"
    description = "Searches RapidDNS for subdomains and DNS records"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            
        url = f"https://rapiddns.io/s/{target}?full=1#result"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"RapidDNS returned {resp.status_code}"}
                    
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.find('table', {'id': 'table'})
                
                if not table:
                    return [], [], {"message": "No results table found on RapidDNS."}
                    
                seen_subs = set()
                
                for row in table.find_all('tr')[1:]: # Skip header
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        subdomain = cols[0].text.strip()
                        if subdomain.endswith(target) and subdomain != target and subdomain not in seen_subs:
                            seen_subs.add(subdomain)
                            
                            sub_ent = Entity(
                                entity_type="subdomain",
                                value=subdomain,
                                label="Subdomain",
                                confidence=0.8,
                                source="RapidDNS"
                            )
                            results.append(sub_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=sub_ent.id,
                                    relationship_type="subdomain_of",
                                    confidence=0.8,
                                    source="RapidDNS"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Found {len(seen_subs)} subdomains."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
