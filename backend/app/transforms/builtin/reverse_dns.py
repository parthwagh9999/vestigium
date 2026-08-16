"""Reverse DNS PTR lookup transform."""
from __future__ import annotations
import asyncio
import socket
from typing import Any
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class ReverseDNSTransform(BaseTransform):
    """Transform to resolve IP addresses to domain names via PTR record lookup."""
    id = "builtin.reverse_dns"
    name = "Reverse DNS PTR Query"
    description = "Resolves IP address to hostnames and domains using PTR DNS query"
    category = "Infrastructure"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["domain", "subdomain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        entities = []
        relationships = []
        
        try:
            loop = asyncio.get_running_loop()
            hostname, _, _ = await loop.gethostbyaddr(ip)
            
            if hostname:
                ent_type = "domain" if len(hostname.split(".")) == 2 else "subdomain"
                e = Entity(entity_type=ent_type, value=hostname.lower(), label=hostname.lower(), confidence=1.0, source="Socket PTR")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="ptr_record", confidence=1.0, source="Socket PTR"))
                
            return entities, relationships, {"hostname": hostname}
        except Exception as e:
            return [], [], {"error": str(e)}
