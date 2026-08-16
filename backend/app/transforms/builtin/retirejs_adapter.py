import asyncio
import json
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class RetireJSAdapter(BaseTransform):
    id = "builtin.retirejs"
    name = "Retire.js Vulnerability Scanner"
    description = "Scans a URL for vulnerable JavaScript libraries using Retire.js"
    category = "Web Intelligence"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["technology", "cve", "vulnerability"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("retire") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
            
        # Note: Retire.js does not natively support scanning remote URLs out of the box without specific plugins/proxies
        # However, some forks or specific versions allow --uri or local temp dir scanning.
        # This wrapper expects a command line utility that can take a URL.
        cmd = ["retire", "--jspath", target, "--outputformat", "json"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if not stdout:
                return [], [], {"error": "Retire.js returned no output or does not support remote URLs."}
                
            data = json.loads(stdout.decode('utf-8'))
            
            for file_result in data:
                results_list = file_result.get("results", [])
                for res in results_list:
                    lib_name = res.get("component")
                    lib_version = res.get("version")
                    vulnerabilities = res.get("vulnerabilities", [])
                    
                    if lib_name:
                        tech_ent = Entity(
                            entity_type="technology",
                            value=f"{lib_name} {lib_version}",
                            label=f"{lib_name} (JS Lib)",
                            confidence=1.0,
                            source="Retire.js"
                        )
                        tech_ent.properties = {
                            "software": lib_name,
                            "version": lib_version,
                            "categories": "JavaScript Library"
                        }
                        results.append(tech_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=tech_ent.id,
                                relationship_type="uses_technology",
                                confidence=1.0,
                                source="Retire.js"
                            )
                        )
                        
                        for vuln in vulnerabilities:
                            cves = vuln.get("identifiers", {}).get("CVE", [])
                            for cve_id in cves:
                                cve_ent = Entity(
                                    entity_type="cve",
                                    value=cve_id,
                                    label=cve_id,
                                    confidence=1.0,
                                    source="Retire.js"
                                )
                                results.append(cve_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=tech_ent.id,
                                        target_entity_id=cve_ent.id,
                                        relationship_type="vulnerable_to",
                                        confidence=1.0,
                                        source="Retire.js"
                                    )
                                )
                                
            return results, relationships, {"raw_output": f"Found {len(data)} vulnerable files."}
            
        except FileNotFoundError:
            return [], [], {"error": "retire CLI not installed. (npm i -g retire)"}
        except Exception as e:
            return [], [], {"error": str(e)}
