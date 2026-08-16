import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class NucleiAdapter(BaseTransform):
    id = "builtin.nuclei"
    name = "Nuclei Template Scanner"
    description = "Runs fast, template-based vulnerability scanning using Nuclei"
    category = "Active Reconnaissance"
    
    input_entity_types = ["ip_address", "url", "domain"]
    output_entity_types = ["vulnerability", "technology"]
    
    is_passive = False # Extremely active scanning
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("nuclei") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        # Target specific severities to reduce noise: high, critical, and info (for tech stack)
        cmd = ["nuclei", "-u", target, "-json-export", tmp_path, "-severity", "info,high,critical", "-silent"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # Nuclei can take a very long time depending on templates. Limit to 3 mins.
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "Nuclei timed out after 3 minutes."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"message": "Nuclei found no matching templates or vulnerabilities."}
                
            seen_vulns = set()
            seen_tech = set()
            
            with open(tmp_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        info = record.get("info", {})
                        severity = info.get("severity", "unknown").lower()
                        name = info.get("name")
                        template_id = record.get("template-id")
                        matcher_name = record.get("matcher-name")
                        
                        # Info severity usually means technology detection in Nuclei
                        if severity == "info":
                            tech_name = name or matcher_name or template_id
                            if tech_name and tech_name not in seen_tech:
                                seen_tech.add(tech_name)
                                tech_ent = Entity(
                                    entity_type="technology",
                                    value=tech_name,
                                    label=tech_name,
                                    confidence=1.0,
                                    source="Nuclei"
                                )
                                results.append(tech_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=tech_ent.id,
                                        relationship_type="uses_technology",
                                        confidence=1.0,
                                        source="Nuclei"
                                    )
                                )
                                
                        # High/Critical means actual vulnerability
                        elif severity in ["high", "critical"]:
                            vuln_name = name or template_id
                            if vuln_name and vuln_name not in seen_vulns:
                                seen_vulns.add(vuln_name)
                                vuln_ent = Entity(
                                    entity_type="vulnerability",
                                    value=vuln_name,
                                    label=f"[{severity.upper()}] {vuln_name}",
                                    confidence=1.0,
                                    source="Nuclei"
                                )
                                vuln_ent.properties = {
                                    "severity": severity,
                                    "template": template_id,
                                    "description": info.get("description", "")
                                }
                                results.append(vuln_ent)
                                relationships.append(
                                    EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=vuln_ent.id,
                                        relationship_type="vulnerable_to",
                                        confidence=1.0,
                                        source="Nuclei"
                                    )
                                )
                                
                    except json.JSONDecodeError:
                        continue
                        
            return results, relationships, {"raw_output": f"Nuclei discovered {len(seen_tech)} technologies and {len(seen_vulns)} high/critical vulnerabilities."}
            
        except FileNotFoundError:
            return [], [], {"error": "Nuclei CLI not installed. (go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest)"}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
