import httpx
from typing import Any
import urllib.parse

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class MementoAdapter(BaseTransform):
    id = "builtin.memento"
    name = "Memento Time Travel Search"
    description = "Searches multiple web archives (Wayback, Arquivo, UK Web Archive) for historical snapshots"
    category = "Historical Intelligence"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["url"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"http://{target}"
            
        url = f"http://timetravel.mementoweb.org/timemap/json/{target}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return [], [], {"message": "No historical snapshots found across archives."}
                if resp.status_code != 200:
                    return [], [], {"error": f"Memento API returned {resp.status_code}"}
                    
                data = resp.json()
                mementos_list = data.get("mementos", {}).get("list", [])
                
                if not mementos_list:
                    return [], [], {"message": "No historical mementos found."}
                    
                seen_archives = set()
                
                # To prevent overloading the graph, we will group by archive source
                # e.g. "web.archive.org", "arquivo.pt"
                for mem in mementos_list:
                    snapshot_url = mem.get("uri")
                    dt = mem.get("datetime")
                    
                    if not snapshot_url:
                        continue
                        
                    parsed_url = urllib.parse.urlparse(snapshot_url)
                    archive_host = parsed_url.hostname
                    
                    if archive_host and archive_host not in seen_archives:
                        # Just save the first one encountered from each distinct archive host
                        seen_archives.add(archive_host)
                        
                        url_ent = Entity(
                            entity_type="url",
                            value=snapshot_url,
                            label=f"Archive: {archive_host}",
                            confidence=1.0,
                            source="Memento"
                        )
                        url_ent.properties = {
                            "archive": archive_host,
                            "snapshot_date": dt
                        }
                        
                        results.append(url_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=url_ent.id,
                                relationship_type="archived_at",
                                confidence=1.0,
                                source="Memento"
                            )
                        )
                        
                        # Stop if we have > 10 unique archives to prevent spam
                        if len(seen_archives) >= 10:
                            break
                            
                return results, relationships, {"raw_output": f"Found snapshots in {len(seen_archives)} unique web archives."}
                
        except Exception as e:
            return [], [], {"error": str(e)}
