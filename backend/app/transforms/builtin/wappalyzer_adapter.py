import asyncio
import json
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class WappalyzerAdapter(BaseTransform):
    id = "builtin.wappalyzer"
    name = "Wappalyzer Tech Scanner"
    description = "Detects technologies, versions, and CPEs on a website using Wappalyzer"
    category = "Web Intelligence"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["technology", "cpe"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("wappalyzer") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
            
        cmd = ["wappalyzer", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if not stdout:
                return [], [], {"error": "Wappalyzer returned no output."}
                
            data = json.loads(stdout.decode('utf-8'))
            technologies = data.get("technologies", [])
            
            for tech in technologies:
                tech_name = tech.get("name")
                versions = tech.get("versions", [])
                cpe = tech.get("cpe")
                categories = [c.get("name") for c in tech.get("categories", [])]
                
                version = versions[0] if versions else None
                
                if tech_name:
                    tech_ent = Entity(
                        entity_type="technology",
                        value=f"{tech_name} {version}" if version else tech_name,
                        label=f"{tech_name} (Tech)",
                        confidence=1.0,
                        source="Wappalyzer"
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
                            confidence=1.0,
                            source="Wappalyzer"
                        )
                    )
                    
                    # Generate CPE if Wappalyzer provides it, this bridges perfectly into CVEIntelTransform
                    if cpe:
                        cpe_ent = Entity(
                            entity_type="cpe",
                            value=cpe,
                            label=cpe,
                            confidence=1.0,
                            source="Wappalyzer"
                        )
                        results.append(cpe_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=tech_ent.id,
                                target_entity_id=cpe_ent.id,
                                relationship_type="has_cpe",
                                confidence=1.0,
                                source="Wappalyzer"
                            )
                        )
                
            return results, relationships, {"raw_output": f"Found {len(technologies)} technologies."}
            
        except FileNotFoundError:
            return [], [], {"error": "wappalyzer CLI not installed. (npm i -g wappalyzer)"}
        except json.JSONDecodeError:
            return [], [], {"error": "Failed to parse Wappalyzer output as JSON"}
        except Exception as e:
            return [], [], {"error": str(e)}
