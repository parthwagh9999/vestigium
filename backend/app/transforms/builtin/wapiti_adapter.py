import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class WapitiAdapter(BaseTransform):
    id = "builtin.wapiti"
    name = "Wapiti Web Application Scanner"
    description = "Aggressive black-box web vulnerability scanner (XSS, SQLi, SSRF)"
    category = "Active Reconnaissance"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("wapiti") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
            
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        # --flush-session prevents state issues, -f json for output
        cmd = ["wapiti", "-u", target, "-f", "json", "-o", tmp_path, "--flush-session"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # Wapiti can take a long time, limit to 3 mins
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "Wapiti timed out after 3 minutes."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"message": "Wapiti found no vulnerabilities."}
                
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            vulns = data.get("vulnerabilities", {})
            seen_vuln_types = set()
            
            for vuln_type, instances in vulns.items():
                if instances and vuln_type not in seen_vuln_types:
                    seen_vuln_types.add(vuln_type)
                    
                    vuln_ent = Entity(
                        entity_type="vulnerability",
                        value=vuln_type,
                        label=f"Wapiti: {vuln_type}",
                        confidence=1.0,
                        source="Wapiti"
                    )
                    vuln_ent.properties = {
                        "instances": len(instances),
                        "description": instances[0].get("info", "") if instances else ""
                    }
                    results.append(vuln_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=vuln_ent.id,
                            relationship_type="vulnerable_to",
                            confidence=1.0,
                            source="Wapiti"
                        )
                    )
                    
            return results, relationships, {"raw_output": f"Wapiti discovered {len(seen_vuln_types)} distinct vulnerability classes."}
            
        except FileNotFoundError:
            return [], [], {"error": "Wapiti CLI not installed. (pip install wapiti3)"}
        except json.JSONDecodeError:
            return [], [], {"error": "Failed to parse Wapiti JSON output."}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
