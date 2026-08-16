import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class CisaKevAdapter(BaseTransform):
    id = "builtin.cisa_kev"
    name = "CISA KEV Lookup"
    description = "Checks if a CVE is listed in the CISA Known Exploited Vulnerabilities catalog"
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
            
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"CISA KEV download returned {resp.status_code}"}
                    
                data = resp.json()
                vulnerabilities = data.get("vulnerabilities", [])
                
                matched_vuln = next((v for v in vulnerabilities if v.get("cveID", "").upper() == target_cve), None)
                
                if not matched_vuln:
                    return [], [], {"message": f"{target_cve} is not in the CISA KEV catalog."}
                
                # If found, create an indicator entity representing the exploitation status
                kev_ent = Entity(
                    entity_type="ioc",
                    value="CISA KEV (Actively Exploited)",
                    label="Exploited In The Wild",
                    confidence=1.0,
                    source="CISA KEV"
                )
                
                # Embed the details in properties
                kev_ent.properties = {
                    "date_added": matched_vuln.get("dateAdded"),
                    "vulnerability_name": matched_vuln.get("vulnerabilityName"),
                    "required_action": matched_vuln.get("requiredAction"),
                    "due_date": matched_vuln.get("dueDate"),
                    "notes": matched_vuln.get("notes")
                }
                
                results.append(kev_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=kev_ent.id,
                        relationship_type="known_exploited_status",
                        confidence=1.0,
                        source="CISA KEV"
                    )
                )
                            
                return results, relationships, {"raw_output": str(matched_vuln)}
                
        except Exception as e:
            return [], [], {"error": str(e)}
