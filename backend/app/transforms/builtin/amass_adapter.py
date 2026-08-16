import asyncio
import json
import logging
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)


class AmassAdapter(BaseTransform):
    id = "kali.amass"
    name = "Amass (Domain Recon)"
    description = "Passive subdomain enumeration using OWASP Amass."
    category = "Domain Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain", "ip_address"]
    
    is_passive = True
    requires_api_key = False
    supported_os = ["linux", "darwin", "windows"] # It works anywhere, assuming amass is in PATH
    
    # Actually checking if it's installed
    import shutil
    install_status = "installed" if shutil.which("amass") else "not_installed"

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        
        if self.install_status != "installed":
            # Graceful degradation
            return [], [], {"error": "Amass is not installed"}

        domain = entity.value
        
        # Run amass enum -passive -d domain -json output.json
        # Since we want to parse stdout in real-time or from a temp file, 
        # for this wrapper we'll do something simple with stdout.
        # Amass can take a while even on passive.
        
        cmd = ["amass", "enum", "-passive", "-d", domain, "-json", "-"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and not stdout:
                logger.error(f"Amass failed: {stderr.decode()}")
                raise RuntimeError(f"Amass execution failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Failed to run Amass: {e}")
            raise RuntimeError(f"Failed to run Amass: {e}")

        # Parse output
        output_text = stdout.decode('utf-8')
        lines = output_text.strip().split('\n')
        
        entities = []
        relationships = []
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                name = data.get("name")
                if name and name != domain:
                    sub_entity = Entity(
                        entity_type="subdomain",
                        value=name,
                        label=name,
                        confidence=0.9,
                        source="Amass"
                    )
                    entities.append(sub_entity)
                    
                    # Also link it
                    rel = EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=sub_entity.id,
                        relationship_type="has_subdomain",
                        label="Amass"
                    )
                    relationships.append(rel)
                    
            except json.JSONDecodeError:
                pass
                
        return entities, relationships, {"raw_output": output_text}
