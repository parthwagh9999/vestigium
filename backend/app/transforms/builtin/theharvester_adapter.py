"""theHarvester adapter for Domain Intelligence."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from typing import Any

from app.transforms.base import BaseTransform, TransformResponse, TransformResultItem

logger = logging.getLogger(__name__)

class TheHarvesterAdapter(BaseTransform):
    """OSINT adapter for theHarvester."""

    id = "kali.theharvester"
    name = "theHarvester Domain OSINT"
    description = "Gathers emails, subdomains, hosts, and employee names using public sources."
    category = "Domain Intelligence"
    author = "Kali Linux Integration"
    version = "1.0.0"

    input_entity_types = ["domain", "website", "url"]
    output_entity_types = ["email", "subdomain", "ip_address"]
    
    is_passive = True
    requires_api_key = False
    
    # Check if installed by trying to run it
    try:
        subprocess.run(["theHarvester", "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
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
        
        domain = entity.value.replace("https://", "").replace("http://", "").split("/")[0].strip()
        
        if self.install_status != "installed":
            # Graceful degradation: log error or return empty
            return [], [], {"error": "theHarvester is not installed"}
            
        entities = []
        relationships = []
        raw_output = ""
        
        try:
            # We run theHarvester on a small subset of sources for performance
            # e.g., theHarvester -d example.com -b baidu,crtsh,yahoo -f output.json
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as tmpdir:
                out_path = os.path.join(tmpdir, "output")
                
                cmd = ["theHarvester", "-d", domain, "-b", "all", "-f", out_path]
                
                # Execute asynchronously
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                raw_output = stdout.decode("utf-8")
                
                # Try parsing the JSON output
                json_path = out_path + ".json"
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        
                        # Process emails
                        for email in data.get("emails", []):
                            e = Entity(entity_type="email", value=email, label=email)
                            entities.append(e)
                            relationships.append(EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=e.id,
                                relationship_type="associated_email",
                                label="found publicly on"
                            ))
                            
                        # Process IPs / Hosts
                        for host in data.get("hosts", []):
                            # host could be "subdomain:ip"
                            parts = host.split(":")
                            subdomain = parts[0]
                            if subdomain:
                                e = Entity(entity_type="subdomain", value=subdomain, label=subdomain)
                                entities.append(e)
                                relationships.append(EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=e.id,
                                    relationship_type="discovered_subdomain",
                                    label="publicly exposed subdomain"
                                ))
                            if len(parts) > 1:
                                ip = parts[1]
                                if ip:
                                    e = Entity(entity_type="ip_address", value=ip, label=ip)
                                    entities.append(e)
                                    relationships.append(EntityRelationship(
                                        source_entity_id=entity.id,
                                        target_entity_id=e.id,
                                        relationship_type="resolves_to",
                                        label="resolves to"
                                    ))
                                    
        except Exception as e:
            logger.error(f"Error running theHarvester: {e}")
            return [], [], {"error": str(e), "stdout": raw_output}

        return entities, relationships, {"stdout": raw_output}
