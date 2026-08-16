import asyncio
import json
import shutil
from typing import Any
import re

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class GHuntAdapter(BaseTransform):
    id = "builtin.ghunt"
    name = "GHunt Google OSINT"
    description = "Extracts Google Account intelligence (Reviews, Maps, YouTube) from a Gmail address"
    category = "Social Intelligence"
    
    input_entity_types = ["email_address"]
    output_entity_types = ["social_profile", "location"]
    
    is_passive = False
    requires_api_key = True # Treats GHunt login cookies as a required key equivalent
    
    @property
    def is_available(self) -> bool:
        return shutil.which("ghunt") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        if not target.lower().endswith("@gmail.com") and not target.lower().endswith("@googlemail.com"):
            return [], [], {"message": "GHunt is highly optimized for Gmail addresses. Skipping non-Google email."}
            
        cmd = ["ghunt", "email", target, "--json", "/dev/stdout"] 
        # GHunt v2 supports JSON output, but sometimes requires a file. If it doesn't support stdout, we parse text.
        
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
                return [], [], {"error": "GHunt timed out."}
                
            output = stdout.decode('utf-8', errors='ignore')
            
            if "not logged in" in output.lower() or "login" in output.lower():
                return [], [], {"error": "GHunt requires authentication. Please run 'ghunt login' on the server."}
                
            if not output:
                return [], [], {"error": "GHunt returned no output."}
                
            # Parse Google Maps locations if present
            location_pattern = re.compile(r'Location:\s*(.*?)(?:\n|$)', re.IGNORECASE)
            locations = location_pattern.findall(output)
            
            for loc in locations:
                loc = loc.strip()
                if loc and loc.lower() != "unknown":
                    loc_ent = Entity(
                        entity_type="location",
                        value=loc,
                        label=f"Google Maps: {loc}",
                        confidence=0.8,
                        source="GHunt"
                    )
                    results.append(loc_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=loc_ent.id,
                            relationship_type="reviewed_location",
                            confidence=0.8,
                            source="GHunt"
                        )
                    )
                    
            # Check for YouTube channel
            yt_pattern = re.compile(r'(https?://(?:www\.)?youtube\.com/channel/[a-zA-Z0-9_\-]+)', re.IGNORECASE)
            yt_matches = yt_pattern.findall(output)
            
            for yt_link in yt_matches:
                yt_ent = Entity(
                    entity_type="social_profile",
                    value=yt_link,
                    label="YouTube Channel",
                    confidence=1.0, # Highly confident if tied to the Google account
                    source="GHunt"
                )
                yt_ent.properties = {
                    "network": "YouTube",
                    "status": "FOUND"
                }
                results.append(yt_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=yt_ent.id,
                        relationship_type="owns_account",
                        confidence=1.0,
                        source="GHunt"
                    )
                )
                
            # Generic Google Account Profile
            profile_ent = Entity(
                entity_type="social_profile",
                value=f"{target} (Google Account)",
                label="Google Account Info",
                confidence=1.0,
                source="GHunt"
            )
            profile_ent.properties = {
                "network": "Google",
                "email": target,
                "status": "FOUND"
            }
            results.append(profile_ent)
            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=profile_ent.id,
                    relationship_type="owns_account",
                    confidence=1.0,
                    source="GHunt"
                )
            )

            return results, relationships, {"raw_output": "GHunt successfully extracted Google intelligence.", "raw_text": output[:500]}
            
        except FileNotFoundError:
            return [], [], {"error": "GHunt CLI not installed. (pipx install ghunt)"}
        except Exception as e:
            return [], [], {"error": str(e)}
