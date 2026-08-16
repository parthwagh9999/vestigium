import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class MasscanAdapter(BaseTransform):
    id = "builtin.masscan"
    name = "Masscan High-Speed Port Scanner"
    description = "Discovers open ports at extremely high speeds using Masscan"
    category = "Active Reconnaissance"
    
    input_entity_types = ["ip_address"]
    output_entity_types = ["port"]
    
    is_passive = False # EXTREMELY NOISY
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("masscan") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        # Top 1000 ports, very fast rate. This requires root/sudo on most systems.
        cmd = ["masscan", target, "-p1-1000", "--rate=1000", "-oJ", tmp_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "Masscan timed out."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                # Often fails if not run as root
                stderr_text = stderr.decode('utf-8', errors='ignore')
                if "root" in stderr_text.lower() or "permission denied" in stderr_text.lower():
                    return [], [], {"error": "Masscan requires root/sudo privileges to run raw sockets."}
                return [], [], {"error": "Masscan failed to produce output."}
                
            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            seen_ports = set()
            
            for host in data:
                ports = host.get("ports", [])
                for p in ports:
                    port_num = p.get("port")
                    protocol = p.get("proto")
                    
                    if port_num and port_num not in seen_ports:
                        seen_ports.add(port_num)
                        
                        port_ent = Entity(
                            entity_type="port",
                            value=f"{port_num}/{protocol}",
                            label=f"Port {port_num}",
                            confidence=1.0,
                            source="Masscan"
                        )
                        port_ent.properties = {
                            "number": port_num,
                            "protocol": protocol,
                            "state": "open"
                        }
                        
                        results.append(port_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=port_ent.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="Masscan"
                            )
                        )
                        
            return results, relationships, {"raw_output": f"Masscan discovered {len(seen_ports)} open ports."}
            
        except FileNotFoundError:
            return [], [], {"error": "Masscan CLI not installed."}
        except json.JSONDecodeError:
            return [], [], {"error": "Failed to parse Masscan JSON output."}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
