import httpx
import re
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class PeeringDBAdapter(BaseTransform):
    id = "builtin.peeringdb"
    name = "PeeringDB Network Intel"
    description = "Retrieves network organization and peering details from PeeringDB"
    category = "Network Intelligence"
    
    input_entity_types = ["asn"]
    output_entity_types = ["organization", "url"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip().upper()
        # Extract just the number
        asn_num = re.sub(r'[^0-9]', '', target)
        
        if not asn_num:
            return [], [], {"error": "Invalid ASN format"}
            
        url = f"https://www.peeringdb.com/api/net?asn={asn_num}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"PeeringDB API returned {resp.status_code}"}
                    
                data = resp.json()
                nets = data.get("data", [])
                
                if not nets:
                    return [], [], {"message": "No PeeringDB record found."}
                    
                net_info = nets[0]
                
                org_name = net_info.get("name")
                website = net_info.get("website")
                
                if org_name:
                    org_ent = Entity(
                        entity_type="organization",
                        value=org_name,
                        label="Peering Network",
                        confidence=1.0,
                        source="PeeringDB"
                    )
                    
                    org_ent.properties = {
                        "aka": net_info.get("aka"),
                        "info_traffic": net_info.get("info_traffic"),
                        "info_type": net_info.get("info_type"),
                        "policy_general": net_info.get("policy_general")
                    }
                    
                    results.append(org_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=org_ent.id,
                            relationship_type="registered_to",
                            confidence=1.0,
                            source="PeeringDB"
                        )
                    )
                    
                    if website:
                        url_ent = Entity(
                            entity_type="url",
                            value=website,
                            label="Website",
                            confidence=1.0,
                            source="PeeringDB"
                        )
                        results.append(url_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=org_ent.id,
                                target_entity_id=url_ent.id,
                                relationship_type="has_website",
                                confidence=1.0,
                                source="PeeringDB"
                            )
                        )
                            
                return results, relationships, {"raw_output": str(net_info)[:2000]}
                
        except Exception as e:
            return [], [], {"error": str(e)}
