import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class TestSSLAdapter(BaseTransform):
    id = "builtin.testssl"
    name = "testssl.sh Scanner"
    description = "Aggressive TLS/SSL vulnerability scanner using testssl.sh"
    category = "Web Intelligence"
    
    input_entity_types = ["url", "domain", "ip_address"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("testssl.sh") is not None or shutil.which("testssl") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "url":
            # Just extract host
            import urllib.parse
            target = urllib.parse.urlparse(target).hostname
            
        executable = "testssl.sh" if shutil.which("testssl.sh") else "testssl"
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        cmd = [executable, "--fast", "-U", "--jsonfile", tmp_path, target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # testssl can take a long time, give it 60 seconds
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "testssl.sh timed out after 60 seconds."}
            
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"error": "testssl.sh failed to produce JSON output."}
                
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            seen_vulns = set()
            
            if isinstance(data, list):
                for finding in data:
                    vuln_id = finding.get("id")
                    severity = finding.get("severity")
                    finding_str = finding.get("finding")
                    
                    if severity in ["HIGH", "CRITICAL"] and vuln_id not in seen_vulns:
                        seen_vulns.add(vuln_id)
                        
                        vuln_ent = Entity(
                            entity_type="vulnerability",
                            value=vuln_id,
                            label=f"TLS Vuln: {vuln_id}",
                            confidence=1.0,
                            source="testssl.sh"
                        )
                        vuln_ent.properties = {
                            "severity": severity,
                            "finding": finding_str
                        }
                        
                        results.append(vuln_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=vuln_ent.id,
                                relationship_type="vulnerable_to",
                                confidence=1.0,
                                source="testssl.sh"
                            )
                        )
                        
            return results, relationships, {"raw_output": f"Found {len(seen_vulns)} high/critical TLS vulnerabilities."}
            
        except FileNotFoundError:
            return [], [], {"error": "testssl.sh not installed."}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
