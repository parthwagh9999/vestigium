"""WHOIS lookup transform for domains."""
from __future__ import annotations
import asyncio
import re
import socket
from typing import Any
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class WHOISTransform(BaseTransform):
    """Transform to query WHOIS records for domain registration information."""
    id = "builtin.whois_lookup"
    name = "WHOIS Domain Query"
    description = "Queries WHOIS server for registrant email, nameservers, and registrar"
    category = "Registration"
    
    input_entity_types = ["domain", "subdomain", "website"]
    output_entity_types = ["email", "organization", "server", "person"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        domain = entity.value.replace("https://", "").replace("http://", "").split("/")[0].strip()
        
        raw_whois = await self._raw_whois_query(domain)
        if not raw_whois:
            raise RuntimeError(f"WHOIS lookup failed or timed out for domain {domain}")
            
        entities = []
        relationships = []
        
        emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_whois))
        for email in emails:
            if not email.endswith(".png") and not email.endswith(".jpg"):
                e = Entity(entity_type="email", value=email.lower(), label=email.lower(), confidence=1.0, source="WHOIS")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="whois_registrant_email", confidence=1.0, source="WHOIS"))
                
        registrar_match = re.search(r"Registrar:\s*(.+)", raw_whois, re.IGNORECASE)
        if registrar_match:
            registrar_name = registrar_match.group(1).strip()
            e = Entity(entity_type="organization", value=registrar_name, label=registrar_name, confidence=1.0, source="WHOIS")
            entities.append(e)
            relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="registered_via", confidence=1.0, source="WHOIS"))
            
        ns_matches = set(re.findall(r"Name Server:\s*([^\s]+)", raw_whois, re.IGNORECASE))
        for ns in ns_matches:
            ns_clean = ns.strip().lower()
            if ns_clean:
                e = Entity(entity_type="domain", value=ns_clean, label=ns_clean, confidence=1.0, source="WHOIS")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_nameserver", confidence=1.0, source="WHOIS"))
                
        return entities, relationships, {"raw_data": {"whois_text": raw_whois}}

    async def _raw_whois_query(self, domain: str) -> str | None:
        try:
            loop = asyncio.get_running_loop()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("whois.iana.org", 43), timeout=5.0
            )
            writer.write(f"{domain}\r\n".encode())
            await writer.drain()
            response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            writer.close()
            await writer.wait_closed()
            text = response.decode("utf-8", errors="ignore")
            
            refer_match = re.search(r"refer:\s*([^\s]+)", text, re.IGNORECASE)
            if refer_match:
                refer_server = refer_match.group(1).strip()
                try:
                    reader2, writer2 = await asyncio.wait_for(
                        asyncio.open_connection(refer_server, 43), timeout=5.0
                    )
                    writer2.write(f"{domain}\r\n".encode())
                    await writer2.drain()
                    response2 = await asyncio.wait_for(reader2.read(8192), timeout=5.0)
                    writer2.close()
                    await writer2.wait_closed()
                    return response2.decode("utf-8", errors="ignore")
                except Exception:
                    pass
            return text
        except Exception:
            return None
