"""Sherlock adapter for Username Intelligence."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import re
from typing import Any

from app.transforms.base import BaseTransform, TransformResponse, TransformResultItem

logger = logging.getLogger(__name__)

class SherlockAdapter(BaseTransform):
    """OSINT adapter for Sherlock."""

    id = "kali.sherlock"
    name = "Sherlock Username OSINT"
    description = "Hunt down social media accounts by username across social networks."
    category = "Social Intelligence"
    author = "Kali Linux Integration"
    version = "1.0.0"

    input_entity_types = ["username"]
    output_entity_types = ["social_profile", "url", "website"]
    
    is_passive = True
    requires_api_key = False
    
    try:
        subprocess.run(["sherlock", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        install_status = "installed"
    except Exception:
        install_status = "not_installed"

    async def execute(
        self,
        entity: Any,
        params: dict[str, Any],
    ) -> tuple[list[Any], list[Any], dict[str, Any]]:
        from app.models.entity import Entity
        from app.models.relationship import EntityRelationship
        
        username = entity.value.strip()
        
        if self.install_status != "installed":
            # Graceful degradation
            return [], [], {"error": "Sherlock is not installed"}
            
        entities = []
        relationships = []
        raw_output = ""
        
        try:
            cmd = ["sherlock", username, "--timeout", "5"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            raw_output = stdout.decode("utf-8")
            
            # Parse sherlock CLI output
            # Format usually looks like:
            # [*] Checking username username on:
            # [+] Platform: https://platform.com/username
            
            lines = raw_output.split("\n")
            for line in lines:
                if "[+]" in line:
                    match = re.search(r"\[\+\]\s+(.*?):\s+(https?://\S+)", line)
                    if match:
                        platform = match.group(1).strip()
                        url = match.group(2).strip()
                        
                        e = Entity(entity_type="social_profile", value=url, label=f"{username} on {platform}", properties={"platform": platform, "url": url})
                        entities.append(e)
                        relationships.append(EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=e.id,
                            relationship_type="has_profile",
                            label=f"Profile on {platform}"
                        ))
                                    
        except Exception as e:
            logger.error(f"Error running Sherlock: {e}")
            return [], [], {"error": str(e), "stdout": raw_output}

        return entities, relationships, {"stdout": raw_output}
