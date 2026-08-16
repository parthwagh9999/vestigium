import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class NiktoAdapter(BaseTransform):
    id = "builtin.nikto"
    name = "Nikto Web Scanner"
    description = "Comprehensive web server scanner for outdated software and misconfigurations"
    category = "Active Reconnaissance"
    
    input_entity_types = ["url", "domain", "ip_address"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False # Extremely noisy
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("nikto") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        cmd = ["nikto", "-h", target, "-Format", "json", "-output", tmp_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "Nikto timed out after 3 minutes."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"error": "Nikto failed to produce JSON output."}
                
            seen_vulns = set()
            
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Nikto JSON structure usually has a 'vulnerabilities' array
            vulns = data.get("vulnerabilities", [])
            if not vulns and "nikto" in data:
                # Sometimes wrapped
                for scan in data.get("nikto", {}).get("scandata", []):
                    for item in scan.get("item", []):
                        desc = item.get("description", "").strip()
                        osvdb = item.get("osvdbid")
                        if desc and desc not in seen_vulns:
                            seen_vulns.add(desc)
                            
                            title = desc[:50] + "..." if len(desc) > 50 else desc
                            vuln_ent = Entity(
                                entity_type="vulnerability",
                                value=title,
                                label=f"Nikto: {title}",
                                confidence=0.8,
                                source="Nikto"
                            )
                            vuln_ent.properties = {
                                "description": desc,
                                "osvdb": osvdb
                            }
                            results.append(vuln_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=vuln_ent.id,
                                    relationship_type="vulnerable_to",
                                    confidence=0.8,
                                    source="Nikto"
                                )
                            )
                            
            return results, relationships, {"raw_output": f"Nikto discovered {len(seen_vulns)} potential vulnerabilities/misconfigurations."}
            
        except FileNotFoundError:
            return [], [], {"error": "Nikto CLI not installed."}
        except json.JSONDecodeError:
            return [], [], {"error": "Failed to parse Nikto JSON output."}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
