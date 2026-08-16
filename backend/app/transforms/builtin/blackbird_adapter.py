import asyncio
import re
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class BlackbirdAdapter(BaseTransform):
    id = "builtin.blackbird"
    name = "Blackbird Username OSINT"
    description = "Searches hundreds of sites for a username using Blackbird"
    category = "Social Intelligence"
    
    input_entity_types = ["username"]
    output_entity_types = ["social_profile"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("blackbird") is not None or shutil.which("python blackbird.py") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        executable = "blackbird"
        cmd = [executable, "-u", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output:
                return [], [], {"error": "Blackbird returned no output."}
                
            # Example Blackbird output:
            # [FOUND] - Twitter: https://twitter.com/username
            # [NOT FOUND] - Instagram
            # [ERROR] - Facebook
            
            found_pattern = re.compile(r'\[(?:FOUND|\+)\]\s*-\s*([A-Za-z0-9_\-\.]+):\s*(https?://\S+)', re.IGNORECASE)
            
            stats = {
                "FOUND": 0,
                "NOT_FOUND": len(re.findall(r'\[NOT FOUND\]', output, re.IGNORECASE)),
                "UNKNOWN_OR_ERROR": len(re.findall(r'\[ERROR\]', output, re.IGNORECASE)),
                "RATE_LIMITED": len(re.findall(r'429|rate limit', output, re.IGNORECASE))
            }
            
            for match in found_pattern.finditer(output):
                site_name = match.group(1).strip()
                profile_url = match.group(2).strip()
                
                stats["FOUND"] += 1
                
                profile_ent = Entity(
                    entity_type="social_profile",
                    value=profile_url,
                    label=f"{site_name}: {target}",
                    confidence=0.5, # Deliberately low confidence: just because the username exists doesn't mean it's the exact same person
                    source="Blackbird"
                )
                
                profile_ent.properties = {
                    "network": site_name,
                    "username": target,
                    "status": "FOUND"
                }
                
                results.append(profile_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=profile_ent.id,
                        relationship_type="possible_alias",
                        confidence=0.5, # Explicitly marked as a possible alias
                        source="Blackbird"
                    )
                )
                
            summary_msg = f"Blackbird scan complete. Found: {stats['FOUND']} | Not Found: {stats['NOT_FOUND']} | Errors/Unknown: {stats['UNKNOWN_OR_ERROR']} | Rate Limited: {stats['RATE_LIMITED']}"
            return results, relationships, {"raw_output": summary_msg, "statistics": stats}
            
        except FileNotFoundError:
            return [], [], {"error": "Blackbird CLI not installed."}
        except Exception as e:
            return [], [], {"error": str(e)}
