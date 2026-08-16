import asyncio
import json
import shutil
import tempfile
import os
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class NaabuAdapter(BaseTransform):
    id = "builtin.naabu"
    name = "Naabu Port Scanner"
    description = "Fast and reliable port scanner by ProjectDiscovery"
    category = "Active Reconnaissance"
    
    input_entity_types = ["ip_address", "domain"]
    output_entity_types = ["port"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("naabu") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        cmd = ["naabu", "-host", target, "-json", "-o", tmp_path, "-silent"]
        
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
                return [], [], {"error": "Naabu timed out."}
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return [], [], {"message": "Naabu found no open ports."}
                
            seen_ports = set()
            
            with open(tmp_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        port_num = record.get("port")
                        
                        if port_num and port_num not in seen_ports:
                            seen_ports.add(port_num)
                            
                            port_ent = Entity(
                                entity_type="port",
                                value=str(port_num),
                                label=f"Port {port_num}",
                                confidence=1.0,
                                source="Naabu"
                            )
                            port_ent.properties = {
                                "number": port_num,
                                "state": "open"
                            }
                            
                            results.append(port_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=port_ent.id,
                                    relationship_type="has_open_port",
                                    confidence=1.0,
                                    source="Naabu"
                                )
                            )
                    except json.JSONDecodeError:
                        continue
                        
            return results, relationships, {"raw_output": f"Naabu discovered {len(seen_ports)} open ports."}
            
        except FileNotFoundError:
            return [], [], {"error": "Naabu CLI not installed. (go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest)"}
        except Exception as e:
            return [], [], {"error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
