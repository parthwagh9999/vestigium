import asyncio
import json
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class RustScanAdapter(BaseTransform):
    id = "builtin.rustscan"
    name = "RustScan Port Scanner"
    description = "Ultra-fast port scanner written in Rust"
    category = "Active Reconnaissance"
    
    input_entity_types = ["ip_address"]
    output_entity_types = ["port"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("rustscan") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        # RustScan typically pipes directly into nmap by default. We can use --g to just output open ports
        cmd = ["rustscan", "-a", target, "-g"]
        
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
                return [], [], {"error": "RustScan timed out."}
                
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output:
                return [], [], {"message": "RustScan found no open ports."}
                
            # Rustscan -g outputs in the format:
            # 192.168.1.1 -> [22,80,443]
            seen_ports = set()
            
            import re
            match = re.search(r'\[(.*?)\]', output)
            if match:
                ports_str = match.group(1)
                for port_str in ports_str.split(","):
                    port_num = port_str.strip()
                    if port_num and port_num.isdigit() and port_num not in seen_ports:
                        seen_ports.add(port_num)
                        
                        port_ent = Entity(
                            entity_type="port",
                            value=port_num,
                            label=f"Port {port_num}",
                            confidence=1.0,
                            source="RustScan"
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
                                source="RustScan"
                            )
                        )
                        
            return results, relationships, {"raw_output": f"RustScan discovered {len(seen_ports)} open ports."}
            
        except FileNotFoundError:
            return [], [], {"error": "RustScan CLI not installed."}
        except Exception as e:
            return [], [], {"error": str(e)}
