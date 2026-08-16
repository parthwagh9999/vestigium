import asyncio
import re
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class HoleheAdapter(BaseTransform):
    id = "builtin.holehe"
    name = "Holehe Email OSINT"
    description = "Checks if an email is attached to an account on 120+ sites (without alerting the target)"
    category = "Social Intelligence"
    
    input_entity_types = ["email_address"]
    output_entity_types = ["social_profile"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("holehe") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        # We can pass --only-used to only show positive results to save parsing,
        # but we want stats on what was checked
        cmd = ["holehe", "--no-color", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # holehe can take a while checking 120 sites
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=90.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "Holehe timed out."}
                
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output:
                return [], [], {"error": "Holehe returned no output."}
                
            # Holehe output uses [+] for found, [-] for not found, [x] for rate limit/error
            # e.g. [+] Twitter
            
            found_pattern = re.compile(r'\[\+\]\s+([A-Za-z0-9_\-\.]+)', re.IGNORECASE)
            
            found_sites = found_pattern.findall(output)
            
            stats = {
                "FOUND": len(found_sites),
                "NOT_FOUND": len(re.findall(r'\[-\]', output)),
                "RATE_LIMITED_OR_ERROR": len(re.findall(r'\[x\]', output))
            }
            
            for site in found_sites:
                site = site.strip()
                
                # Holehe doesn't provide exact URLs, so we create a generic profile entity
                profile_ent = Entity(
                    entity_type="social_profile",
                    value=f"{target} on {site}",
                    label=f"{site} Account",
                    confidence=0.9, # For email presence, this is usually highly accurate because it uses password reset API
                    source="Holehe"
                )
                
                profile_ent.properties = {
                    "network": site,
                    "email": target,
                    "status": "FOUND"
                }
                
                results.append(profile_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=profile_ent.id,
                        relationship_type="registered_to",
                        confidence=0.9,
                        source="Holehe"
                    )
                )
                
            summary = f"Holehe scan complete. Found: {stats['FOUND']} | Not Found: {stats['NOT_FOUND']} | Errors/Rate Limited: {stats['RATE_LIMITED_OR_ERROR']}"
            return results, relationships, {"raw_output": summary, "statistics": stats}
            
        except FileNotFoundError:
            return [], [], {"error": "Holehe CLI not installed. (pip install holehe)"}
        except Exception as e:
            return [], [], {"error": str(e)}
