import asyncio
import os
import shutil
import re
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class FierceAdapter(BaseTransform):
    id = "builtin.fierce"
    name = "Fierce DNS Recon"
    description = "Discovers subdomains and IP space using Fierce (Active/Noisy)"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain", "ip_address"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("fierce") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            if not target:
                return [], [], {}
                
        cmd = ["fierce", "--domain", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # Fierce output format: Found: subdomain.domain.com. (1.2.3.4)
            found_pattern = re.compile(r'Found:\s+([a-zA-Z0-9\-\.]+)\.?\s+\(([0-9\.]+)\)', re.IGNORECASE)
            
            seen_subs = set()
            seen_ips = set()
            
            for match in found_pattern.finditer(output):
                hostname = match.group(1).rstrip('.')
                ip = match.group(2)
                
                if hostname.endswith(target) and hostname != target and hostname not in seen_subs:
                    seen_subs.add(hostname)
                    sub_ent = Entity(
                        entity_type="subdomain",
                        value=hostname,
                        label="Subdomain",
                        confidence=0.9,
                        source="Fierce"
                    )
                    results.append(sub_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=sub_ent.id,
                            relationship_type="subdomain_of",
                            confidence=0.9,
                            source="Fierce"
                        )
                    )
                    
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    ip_ent = Entity(
                        entity_type="ip_address",
                        value=ip,
                        label="IP Address",
                        confidence=0.9,
                        source="Fierce"
                    )
                    results.append(ip_ent)
                    
                    parent_id = entity.id if hostname == target else None
                    if not parent_id:
                        parent_ent = next((r for r in results if r.value == hostname), None)
                        if parent_ent:
                            parent_id = parent_ent.id
                    
                    if parent_id:
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=parent_id,
                                target_entity_id=ip_ent.id,
                                relationship_type="resolves_to",
                                confidence=0.9,
                                source="Fierce"
                            )
                        )
                
            return results, relationships, {"raw_output": output[:3000]}
            
        except FileNotFoundError:
            return [], [], {"error": "fierce not installed"}
        except Exception as e:
            return [], [], {"error": str(e)}
