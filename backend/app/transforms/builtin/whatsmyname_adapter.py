import asyncio
import json
import shutil
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class WhatsMyNameAdapter(BaseTransform):
    id = "builtin.whatsmyname"
    name = "WhatsMyName Dataset Search"
    description = "Searches the WhatsMyName OSINT dataset for username presence"
    category = "Social Intelligence"
    
    input_entity_types = ["username"]
    output_entity_types = ["social_profile"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("whatsmyname") is not None or shutil.which("wmn") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        executable = "whatsmyname" if shutil.which("whatsmyname") else "wmn"
        
        # We expect a tool that outputs json or parseable text
        cmd = [executable, "-u", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # WMN can take a bit, give it 60s
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            except asyncio.TimeoutError:
                process.kill()
                return [], [], {"error": "WhatsMyName timed out."}
                
            output = stdout.decode('utf-8', errors='ignore')
            
            # Attempt to parse as JSON if the tool supports it, else regex
            try:
                data = json.loads(output)
                # Parse JSON array of found sites
                # Example: [{"site": "Twitter", "url": "...", "status": "FOUND"}]
                found_sites = [s for s in data if s.get("status", "").upper() == "FOUND"]
                
                stats = {
                    "FOUND": len(found_sites),
                    "NOT_FOUND": len([s for s in data if s.get("status", "").upper() == "NOT_FOUND"]),
                    "UNKNOWN": 0,
                    "RATE_LIMITED": 0
                }
                
                for item in found_sites:
                    site = item.get("site", "Unknown Site")
                    profile_url = item.get("url")
                    
                    if profile_url:
                        profile_ent = Entity(
                            entity_type="social_profile",
                            value=profile_url,
                            label=f"{site}: {target}",
                            confidence=0.5, # Inference, not fact
                            source="WhatsMyName"
                        )
                        profile_ent.properties = {
                            "network": site,
                            "username": target,
                            "status": "FOUND"
                        }
                        results.append(profile_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=profile_ent.id,
                                relationship_type="possible_alias",
                                confidence=0.5,
                                source="WhatsMyName"
                            )
                        )
                        
            except json.JSONDecodeError:
                # Fallback to regex parsing if output is standard text
                import re
                found_pattern = re.compile(r'(?:FOUND|SUCCESS|\[\+\]).*?(https?://\S+)', re.IGNORECASE)
                
                found_urls = found_pattern.findall(output)
                stats = {
                    "FOUND": len(found_urls),
                    "NOT_FOUND": len(re.findall(r'NOT FOUND|\[-\]', output, re.IGNORECASE)),
                    "UNKNOWN": len(re.findall(r'ERROR|UNKNOWN|\[!\]', output, re.IGNORECASE)),
                    "RATE_LIMITED": len(re.findall(r'RATE|429', output, re.IGNORECASE))
                }
                
                for url in found_urls:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace("www.", "")
                    
                    profile_ent = Entity(
                        entity_type="social_profile",
                        value=url,
                        label=f"{domain}: {target}",
                        confidence=0.5,
                        source="WhatsMyName"
                    )
                    profile_ent.properties = {
                        "network": domain,
                        "username": target,
                        "status": "FOUND"
                    }
                    results.append(profile_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=profile_ent.id,
                            relationship_type="possible_alias",
                            confidence=0.5,
                            source="WhatsMyName"
                        )
                    )
                    
            summary = f"WhatsMyName scan complete. Found: {stats['FOUND']} | Not Found: {stats['NOT_FOUND']} | Unknown: {stats['UNKNOWN']} | Rate Limited: {stats['RATE_LIMITED']}"
            return results, relationships, {"raw_output": summary, "statistics": stats}
            
        except FileNotFoundError:
            return [], [], {"error": "WhatsMyName CLI not installed."}
        except Exception as e:
            return [], [], {"error": str(e)}
