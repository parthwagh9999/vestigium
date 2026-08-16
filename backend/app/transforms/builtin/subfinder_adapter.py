import asyncio
import json
import logging
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)

class SubfinderAdapter(BaseTransform):
    """Subfinder adapter for passive subdomain discovery."""
    
    id = "builtin.subfinder"
    name = "Subfinder Subdomain Discovery"
    description = "Passive subdomain discovery using Subfinder"
    category = "Domain Intelligence"
    source = "ProjectDiscovery Subfinder"
    documentation_url = "https://github.com/projectdiscovery/subfinder"
    license = "MIT"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain"]
    relationships_created = ["has_subdomain"]
    
    execution_type = "binary"
    passive_or_active = "PASSIVE"
    authorization_required = False
    
    installation_required = True
    supported_os = ["linux", "windows", "macos"]
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        domain = entity.value.strip()
        
        entities = []
        relationships = []
        raw_output = {}
        
        # Check binary availability
        import shutil
        if not shutil.which("subfinder"):
            return [], [], {"warning": "subfinder binary is not installed in PATH. Install via: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"}
        
        cmd = ["subfinder", "-d", domain, "-silent", "-all", "-json"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and stderr:
                logger.warning(f"Subfinder returned error code {process.returncode}: {stderr.decode()}")
                
            out_str = stdout.decode('utf-8', errors='ignore')
            lines = out_str.strip().split('\n')
            
            subdomains_found = []
            
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    sub = data.get("host")
                    source_str = data.get("source", "subfinder")
                    
                    if sub:
                        subdomains_found.append(sub)
                        e = Entity(entity_type="subdomain", value=sub, label=sub, confidence=1.0, source=f"Subfinder ({source_str})")
                        entities.append(e)
                        relationships.append(EntityRelationship(
                            source_entity_id=entity.id, 
                            target_entity_id=e.id, 
                            relationship_type="has_subdomain", 
                            confidence=1.0, 
                            source="Subfinder"
                        ))
                except json.JSONDecodeError:
                    sub = line.strip()
                    subdomains_found.append(sub)
                    e = Entity(entity_type="subdomain", value=sub, label=sub, confidence=1.0, source="Subfinder")
                    entities.append(e)
                    relationships.append(EntityRelationship(
                        source_entity_id=entity.id, 
                        target_entity_id=e.id, 
                        relationship_type="has_subdomain", 
                        confidence=1.0, 
                        source="Subfinder"
                    ))
                    
            raw_output["subdomains_found"] = subdomains_found
            if stderr:
                raw_output["stderr"] = stderr.decode('utf-8', errors='ignore')
                
            return entities, relationships, raw_output
            
        except Exception as e:
            logger.error(f"Subfinder execution error: {e}")
            return [], [], {"error": str(e)}
