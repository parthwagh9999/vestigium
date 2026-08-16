import asyncio
import json
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class WebanalyzeAdapter(BaseTransform):
    id = "builtin.webanalyze"
    name = "Webanalyze Scanner"
    description = "High-performance technology stack detection using Webanalyze (Wappalyzer alternative)"
    category = "Web Intelligence"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["technology"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("webanalyze") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
            
        cmd = ["webanalyze", "-host", target, "-output", "json"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if not stdout:
                return [], [], {"error": "Webanalyze returned no output."}
                
            data = json.loads(stdout.decode('utf-8'))
            
            if not isinstance(data, list):
                if "matches" in data:
                    data = [data]
                else:
                    return [], [], {"error": "Unexpected output format."}
            
            seen_tech = set()
                    
            for item in data:
                matches = item.get("matches", [])
                for match in matches:
                    tech_name = match.get("app_name")
                    version = match.get("version")
                    categories = match.get("category_names", [])
                    
                    if tech_name and tech_name not in seen_tech:
                        seen_tech.add(tech_name)
                        
                        tech_ent = Entity(
                            entity_type="technology",
                            value=f"{tech_name} {version}" if version else tech_name,
                            label=f"{tech_name} (Tech)",
                            confidence=0.9,
                            source="Webanalyze"
                        )
                        
                        tech_ent.properties = {
                            "software": tech_name,
                            "version": version,
                            "categories": ", ".join(categories)
                        }
                        
                        results.append(tech_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=tech_ent.id,
                                relationship_type="uses_technology",
                                confidence=0.9,
                                source="Webanalyze"
                            )
                        )
                
            return results, relationships, {"raw_output": f"Found {len(seen_tech)} technologies."}
            
        except FileNotFoundError:
            return [], [], {"error": "webanalyze CLI not installed."}
        except json.JSONDecodeError:
            # Webanalyze sometimes outputs plain text before JSON
            return [], [], {"error": "Failed to parse Webanalyze output as JSON. Output may be unformatted."}
        except Exception as e:
            return [], [], {"error": str(e)}
