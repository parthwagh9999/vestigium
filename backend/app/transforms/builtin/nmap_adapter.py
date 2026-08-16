import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)

class NmapTransform(BaseTransform):
    """Nmap adapter for active network scanning."""
    
    id = "builtin.nmap"
    name = "Nmap Port Scanner"
    description = "Actively scans an IP address for open ports and services using Nmap."
    category = "Internet Asset Discovery"
    source = "Nmap"
    documentation_url = "https://nmap.org/book/man.html"
    license = "Nmap Public Source License"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["service", "port"]
    relationships_created = ["has_open_port"]
    
    execution_type = "binary"
    passive_or_active = "ACTIVE_AUTHORIZED"
    authorization_required = True
    
    installation_required = True
    api_key_required = False
    
    # We enforce a timeout for active scanning to prevent long-running tasks
    timeout = 120
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        
        entities = []
        relationships = []
        raw_output = {}
        
        import shutil
        if not shutil.which("nmap"):
            return [], [], {"warning": "nmap binary is not installed in PATH. Install nmap or add to system PATH."}
        
        # -F (Fast mode: top 100 ports), -T4 (Aggressive timing), -oX (XML output)
        cmd = ["nmap", "-F", "-T4", "-oX", "-", ip]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and stderr:
                logger.warning(f"Nmap returned error code {process.returncode}: {stderr.decode('utf-8', errors='ignore')}")
                
            out_str = stdout.decode('utf-8', errors='ignore')
            if stderr:
                raw_output["stderr"] = stderr.decode('utf-8', errors='ignore')
                
            if not out_str.strip():
                return entities, relationships, raw_output
                
            # Parse Nmap XML output
            root = ET.fromstring(out_str)
            raw_output["nmap_xml"] = out_str
            
            ports_found = []
            
            for host in root.findall('host'):
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        state = port.find('state')
                        if state is not None and state.get('state') == 'open':
                            port_id = port.get('portid')
                            protocol = port.get('protocol')
                            
                            service_node = port.find('service')
                            service_name = service_node.get('name') if service_node is not None else "unknown"
                            
                            port_label = f"Port {port_id}/{protocol} ({service_name})"
                            ports_found.append(port_label)
                            
                            e = Entity(entity_type="service", value=port_label, label=port_label, confidence=1.0, source="Nmap")
                            entities.append(e)
                            relationships.append(EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=e.id,
                                relationship_type="has_open_port",
                                confidence=1.0,
                                source="Nmap"
                            ))
                            
            raw_output["open_ports"] = ports_found
            return entities, relationships, raw_output
            
        except Exception as e:
            logger.error(f"Nmap execution error: {e}")
            return [], [], {"error": str(e)}
