import asyncio
import os
import shutil
import re
import urllib.parse
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class DNSEnumAdapter(BaseTransform):
    id = "builtin.dnsenum"
    name = "DNSEnum Reconnaissance"
    description = "Discovers subdomains and DNS records using dnsenum (Passive/Active)"
    category = "Domain & DNS Intelligence"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain", "ip_address"]
    
    is_passive = False
    requires_api_key = False
    
    @property
    def is_available(self) -> bool:
        return shutil.which("dnsenum") is not None

    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if "://" in target:
            target = urllib.parse.urlparse(target).hostname
            if not target:
                return [], [], {}
                
        # Run dnsenum without reverse lookups to save time and reduce active noise
        cmd = ["dnsenum", "--noreverse", "--enum", target]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # Simple parsing for subdomains and IPs
            record_pattern = re.compile(r'^([a-zA-Z0-9\-\.]+)\.?\s+\d+\s+IN\s+(A|CNAME)\s+([a-zA-Z0-9\-\.]+)', re.MULTILINE)
            
            seen_subs = set()
            seen_ips = set()
            
            for match in record_pattern.finditer(output):
                hostname = match.group(1).rstrip('.')
                rectype = match.group(2)
                value = match.group(3).rstrip('.')
                
                if hostname.endswith(target) and hostname != target and hostname not in seen_subs:
                    seen_subs.add(hostname)
                    sub_ent = Entity(
                        entity_type="subdomain",
                        value=hostname,
                        label="Subdomain",
                        confidence=0.9,
                        source="dnsenum"
                    )
                    results.append(sub_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=sub_ent.id,
                            relationship_type="subdomain_of",
                            confidence=0.9,
                            source="dnsenum"
                        )
                    )
                    
                if rectype == "A" and value not in seen_ips:
                    seen_ips.add(value)
                    ip_ent = Entity(
                        entity_type="ip_address",
                        value=value,
                        label="IP Address",
                        confidence=0.9,
                        source="dnsenum"
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
                                source="dnsenum"
                            )
                        )
                
            return results, relationships, {"raw_output": output[:3000]}
            
        except FileNotFoundError:
            return [], [], {"error": "dnsenum not installed"}
        except Exception as e:
            return [], [], {"error": str(e)}
