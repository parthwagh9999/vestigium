import httpx
import logging
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)

class CrtShTransform(BaseTransform):
    """crt.sh adapter for passive Certificate Transparency (CT) log searching."""
    
    id = "builtin.crt_sh"
    name = "crt.sh Certificate Search"
    description = "Searches crt.sh for SSL/TLS certificates belonging to a domain to discover subdomains"
    category = "Certificate & TLS Intelligence"
    source = "crt.sh"
    documentation_url = "https://crt.sh/"
    license = "Public Domain"
    
    input_entity_types = ["domain"]
    output_entity_types = ["subdomain", "certificate"]
    relationships_created = ["has_certificate", "has_subdomain"]
    
    execution_type = "api"
    passive_or_active = "PASSIVE"
    authorization_required = False
    
    installation_required = False
    api_key_required = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        domain = entity.value.strip().lower()
        
        entities = []
        relationships = []
        raw_output = {}
        
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"crt.sh returned HTTP {resp.status_code}")
                    return [], [], {"warning": f"crt.sh service returned HTTP {resp.status_code}"}
                data = resp.json()
                
            raw_output["certificates"] = data
            
            seen_subdomains = set()
            
            for cert in data:
                # Extract subdomains from name_value
                name_value = cert.get("name_value", "")
                if name_value:
                    names = name_value.split("\n")
                    for name in names:
                        name = name.strip().lower()
                        # Clean wildcards
                        if name.startswith("*."):
                            name = name[2:]
                            
                        if name.endswith(domain) and name != domain and name not in seen_subdomains:
                            seen_subdomains.add(name)
                            e = Entity(entity_type="subdomain", value=name, label=name, confidence=1.0, source="crt.sh")
                            entities.append(e)
                            relationships.append(EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=e.id,
                                relationship_type="has_subdomain",
                                confidence=1.0,
                                source="crt.sh"
                            ))
                
            return entities, relationships, raw_output
            
        except Exception as e:
            logger.error(f"crt.sh execution error: {e}")
            return [], [], {"error": str(e)}
