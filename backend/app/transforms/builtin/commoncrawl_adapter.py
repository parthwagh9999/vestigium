import httpx
import json
from typing import Any
import urllib.parse

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CommonCrawlAdapter(BaseTransform):
    id = "builtin.commoncrawl"
    name = "Common Crawl Index Search"
    description = "Searches the massive Common Crawl indices for historical URLs and subdomains"
    category = "Historical Intelligence"
    
    input_entity_types = ["domain", "url"]
    output_entity_types = ["url"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # 1. Fetch latest index
                collinfo_url = "https://index.commoncrawl.org/collinfo.json"
                resp_info = await client.get(collinfo_url)
                if resp_info.status_code != 200:
                    return [], [], {"error": "Failed to fetch Common Crawl indices."}
                    
                indices = resp_info.json()
                if not indices:
                    return [], [], {"error": "Empty indices from Common Crawl."}
                    
                # Use the latest index API endpoint
                latest_index_api = indices[0].get("cdx-api")
                
                # 2. Query for the domain
                query_url = f"{latest_index_api}?url=*.{target}/*&output=json&limit=50"
                
                resp_search = await client.get(query_url)
                if resp_search.status_code == 404:
                    return [], [], {"message": "No records found in the latest Common Crawl index."}
                if resp_search.status_code != 200:
                    return [], [], {"error": f"CC Index API returned {resp_search.status_code}"}
                    
                seen_urls = set()
                
                # output is JSONL
                for line in resp_search.text.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        url_val = record.get("url")
                        timestamp = record.get("timestamp")
                        
                        if url_val and url_val not in seen_urls:
                            seen_urls.add(url_val)
                            
                            url_ent = Entity(
                                entity_type="url",
                                value=url_val,
                                label=url_val[:40] + "..." if len(url_val) > 40 else url_val,
                                confidence=0.8,
                                source="Common Crawl"
                            )
                            
                            url_ent.properties = {
                                "timestamp": timestamp,
                                "mime": record.get("mime"),
                                "status": record.get("status")
                            }
                            
                            results.append(url_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=url_ent.id,
                                    relationship_type="hosted_historically",
                                    confidence=0.8,
                                    source="Common Crawl"
                                )
                            )
                            
                    except json.JSONDecodeError:
                        continue
                        
                return results, relationships, {"raw_output": f"Found {len(seen_urls)} historical URLs."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
