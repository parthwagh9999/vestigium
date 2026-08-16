import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class SSLyzeAdapter(BaseTransform):
    id = "builtin.sslyze"
    name = "SSLyze TLS Scanner"
    description = "Extremely fast TLS configuration and vulnerability scanner"
    category = "Active Reconnaissance"
    
    input_entity_types = ["domain", "url"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("sslyze") is not None or shutil.which("python -m sslyze") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            import urllib.parse
            target = urllib.parse.urlparse(target).hostname
            
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        cmd = ["sslyze", f"{target}:443", "--json_out", tmp_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "SSLyze timed out after 60 seconds."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"error": "SSLyze failed to produce JSON output."}
                
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            seen_vulns = set()
            
            # Parse the SSLyze JSON output for vulnerabilities
            results_list = data.get("server_scan_results", [])
            for res in results_list:
                scan_res = res.get("scan_result", {})
                
                # Check for Heartbleed
                heartbleed = scan_res.get("heartbleed", {}).get("result", {})
                if heartbleed.get("is_vulnerable_to_heartbleed"):
                    seen_vulns.add("Heartbleed")
                    
                # Check for CCS Injection
                ccs = scan_res.get("openssl_ccs_injection", {}).get("result", {})
                if ccs.get("is_vulnerable_to_ccs_injection"):
                    seen_vulns.add("OpenSSL CCS Injection")
                    
                # Check for ROBOT
                robot = scan_res.get("robot", {}).get("result", {})
                if robot.get("robot_result") == "VULNERABLE_STRONG_ORACLE":
                    seen_vulns.add("ROBOT Attack")
                    
                # Certificates
                certs = scan_res.get("certificate_info", {}).get("result", {})
                if certs:
                    for validation in certs.get("path_validation_results", []):
                        if not validation.get("was_validation_successful"):
                            seen_vulns.add("Invalid/Untrusted Certificate")
                            break
                            
            for vuln in seen_vulns:
                vuln_ent = Entity(
                    entity_type="vulnerability",
                    value=vuln,
                    label=f"TLS: {vuln}",
                    confidence=1.0,
                    source="SSLyze"
                )
                results.append(vuln_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=vuln_ent.id,
                        relationship_type="vulnerable_to",
                        confidence=1.0,
                        source="SSLyze"
                    )
                )
                
            return results, relationships, {"raw_output": f"SSLyze discovered {len(seen_vulns)} TLS vulnerabilities/misconfigurations."}
            
        except FileNotFoundError:
            return [], [], {"error": "SSLyze CLI not installed. (pip install sslyze)"}
        except json.JSONDecodeError:
            return [], [], {"error": "Failed to parse SSLyze JSON output."}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
