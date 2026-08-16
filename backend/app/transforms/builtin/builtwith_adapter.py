import httpx
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class BuiltWithAdapter(BaseTransform):
    id = "builtin.builtwith"
    name = "BuiltWith Tech Stack"
    description = "Searches BuiltWith for technologies used by a domain (Requires API Key)"
    category = "Web Intelligence"
    
    input_entity_types = ["domain", "url"]
    output_entity_types = ["technology"]
    
    is_passive = True
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            
        api_key = params.get("api_keys", {}).get("BUILTWITH_API_KEY")
        if not api_key:
            return [], [], {"error": "BUILTWITH_API_KEY is required."}
            
        url = f"https://api.builtwith.com/v20/api.json?KEY={api_key}&LOOKUP={target}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url)
                if resp.status_code == 401 or resp.status_code == 403:
                    return [], [], {"error": "Invalid BuiltWith API Key."}
                if resp.status_code != 200:
                    return [], [], {"error": f"BuiltWith API returned {resp.status_code}"}
                    
                data = resp.json()
                if "Errors" in data and data["Errors"]:
                    return [], [], {"error": str(data["Errors"])}
                    
                paths = data.get("Results", [])
                
                if not paths:
                    return [], [], {"message": "No BuiltWith records found for this domain."}
                    
                seen_tech = set()
                
                for path in paths:
                    result_data = path.get("Result", {})
                    tech_paths = result_data.get("Paths", [])
                    
                    for t_path in tech_paths:
                        technologies = t_path.get("Technologies", [])
                        for tech in technologies:
                            tech_name = tech.get("Name")
                            categories = tech.get("Categories", [])
                            
                            if tech_name and tech_name not in seen_tech:
                                seen_tech.add(tech_name)
                                
                                tech_ent = Entity(
                                    entity_type="technology",
                                    value=tech_name,
                                    label=f"{tech_name} (Tech)",
                                    confidence=1.0,
                                    source="BuiltWith"
                                )
                                
                                tech_ent.properties = {
                                    "software": tech_name,
                                    "categories": ", ".join(categories)
                                }
                                
                                results.append(tech_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=tech_ent.id,
                                        relationship_type="uses_technology",
                                        confidence=1.0,
                                        source="BuiltWith"
                                    )
                                )
                                
                return results, relationships, {"raw_output": f"Found {len(seen_tech)} technologies."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
