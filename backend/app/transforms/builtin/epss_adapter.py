import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class EPSSAdapter(BaseTransform):
    id = "builtin.epss"
    name = "EPSS Score Lookup"
    description = "Retrieves the FIRST Exploit Prediction Scoring System (EPSS) probability for a CVE"
    category = "Vulnerability Intelligence"
    
    input_entity_types = ["cve"]
    output_entity_types = ["ioc"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target_cve = entity.value.strip().upper()
        if not target_cve.startswith("CVE-"):
            return [], [], {"error": "Invalid CVE format"}
            
        url = f"https://api.first.org/data/v1/epss?cve={target_cve}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"EPSS API returned {resp.status_code}"}
                    
                data = resp.json()
                epss_data = data.get("data", [])
                
                if not epss_data:
                    return [], [], {"message": f"No EPSS score found for {target_cve}."}
                    
                record = epss_data[0]
                epss_prob = float(record.get("epss", 0))
                percentile = float(record.get("percentile", 0))
                
                if epss_prob > 0.05: # High relative probability
                    prob_desc = "High"
                elif epss_prob > 0.01:
                    prob_desc = "Medium"
                else:
                    prob_desc = "Low"
                
                epss_ent = Entity(
                    entity_type="ioc",
                    value=f"EPSS: {epss_prob:.4f}",
                    label=f"Exploit Probability: {prob_desc}",
                    confidence=1.0,
                    source="FIRST EPSS"
                )
                
                epss_ent.properties = {
                    "epss_probability": epss_prob,
                    "percentile": percentile,
                    "date": record.get("date")
                }
                
                results.append(epss_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=epss_ent.id,
                        relationship_type="has_epss_score",
                        confidence=1.0,
                        source="FIRST EPSS"
                    )
                )
                            
                return results, relationships, {"raw_output": str(record)}
                
        except Exception as e:
            return [], [], {"error": str(e)}
