import asyncio
import os
import shutil
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class FindomainAdapter(BaseTransform):
    id = "builtin.findomain"
    name = "Findomain Subdomain Enumeration"
    description = "Discovers subdomains using Findomain (Passive)"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain"]
    
    is_passive = True
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("findomain") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value
        # Basic sanitization
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            if not target:
                return [], [], {}
                
        # Run findomain
        cmd = ["findomain", "-t", target, "-q"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return [], [], {"error": f"findomain failed: {stderr.decode()}"}
                
            output = stdout.decode('utf-8')
            
            for line in output.splitlines():
                subdomain = line.strip()
                if not subdomain or subdomain == target or not subdomain.endswith(target):
                    continue
                    
                sub_ent = Entity(
                    entity_type="subdomain",
                    value=subdomain,
                    label="Subdomain",
                    confidence=1.0,
                    source="Findomain"
                )
                results.append(sub_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=sub_ent.id,
                        relationship_type="subdomain_of",
                        confidence=1.0,
                        source="Findomain"
                    )
                )
                
            return results, relationships, {"raw_output": output[:2000]}
            
        except FileNotFoundError:
            return [], [], {"error": "findomain not installed"}
        except Exception as e:
            return [], [], {"error": str(e)}
