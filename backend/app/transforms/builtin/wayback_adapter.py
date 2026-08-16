import httpx
import logging
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)

class WaybackMachineTransform(BaseTransform):
    """Wayback Machine adapter for discovering historical URLs."""
    
    id = "builtin.wayback_machine"
    name = "Wayback Machine Archive Search"
    description = "Searches the Internet Archive for historical snapshots and URLs belonging to a domain"
    category = "Web Archive Intelligence"
    source = "Internet Archive"
    documentation_url = "https://archive.org/help/wayback_api.php"
    license = "Public Domain"
    
    input_entity_types = ["domain", "website"]
    output_entity_types = ["url"]
    relationships_created = ["has_archived_url"]
    
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
        domain = entity.value.strip().replace("https://", "").replace("http://", "").split("/")[0]
        
        entities = []
        relationships = []
        raw_output = {}
        
        # Wayback Machine CDX API
        # We limit to 50 results to prevent massive graph bloat
        url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original,timestamp,mimetype,statuscode&collapse=urlkey&limit=50"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Wayback Machine returned HTTP {resp.status_code}")
                    return [], [], {"warning": f"Wayback Machine returned HTTP {resp.status_code}"}
                
                # The first row is the header: ["original", "timestamp", "mimetype", "statuscode"]
                data = resp.json()
                
            if len(data) > 1:
                headers = data[0]
                rows = data[1:]
                
                raw_output["archived_urls"] = rows
                
                for row in rows:
                    if len(row) >= 1:
                        target_url = row[0]
                        timestamp = row[1] if len(row) > 1 else ""
                        mimetype = row[2] if len(row) > 2 else ""
                        statuscode = row[3] if len(row) > 3 else ""
                        
                        props = {
                            "timestamp": timestamp,
                            "mimetype": mimetype,
                            "statuscode": statuscode
                        }
                        
                        e = Entity(entity_type="url", value=target_url, label=target_url, confidence=1.0, source="Wayback Machine", properties=props)
                        entities.append(e)
                        relationships.append(EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=e.id,
                            relationship_type="has_archived_url",
                            confidence=1.0,
                            source="Wayback Machine"
                        ))
                        
            return entities, relationships, raw_output
            
        except Exception as e:
            logger.error(f"Wayback Machine execution error: {e}")
            return [], [], {"error": str(e)}
