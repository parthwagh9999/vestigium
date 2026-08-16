import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class BGPViewAdapter(BaseTransform):
    id = "builtin.bgpview"
    name = "BGPView IP Intel"
    description = "Retrieves ASN, prefix, and organization from BGPView API"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["asn", "netblock", "organization"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = f"https://api.bgpview.io/ip/{target}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"BGPView API returned {resp.status_code}"}
                    
                data = resp.json()
                if data.get("status") != "ok":
                    return [], [], {"error": "BGPView API status not OK"}
                    
                prefixes = data.get("data", {}).get("prefixes", [])
                
                if not prefixes:
                    return [], [], {"message": "No BGP prefixes found."}
                    
                seen_asns = set()
                seen_orgs = set()
                
                for p in prefixes:
                    prefix_str = p.get("prefix")
                    asn_info = p.get("asn", {})
                    asn_id = asn_info.get("asn")
                    org_name = asn_info.get("description") or asn_info.get("name")
                    
                    netblock_ent = None
                    if prefix_str:
                        netblock_ent = Entity(
                            entity_type="netblock",
                            value=prefix_str,
                            label="BGP Prefix",
                            confidence=1.0,
                            source="BGPView"
                        )
                        results.append(netblock_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=netblock_ent.id,
                                relationship_type="part_of_netblock",
                                confidence=1.0,
                                source="BGPView"
                            )
                        )
                        
                    asn_ent = None
                    if asn_id and asn_id not in seen_asns:
                        seen_asns.add(asn_id)
                        asn_ent = Entity(
                            entity_type="asn",
                            value=f"AS{asn_id}",
                            label="Autonomous System",
                            confidence=1.0,
                            source="BGPView"
                        )
                        results.append(asn_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=asn_ent.id,
                                relationship_type="routed_by",
                                confidence=1.0,
                                source="BGPView"
                            )
                        )
                        
                        if netblock_ent:
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=netblock_ent.id,
                                    target_entity_id=asn_ent.id,
                                    relationship_type="announced_by",
                                    confidence=1.0,
                                    source="BGPView"
                                )
                            )
                            
                    if org_name and org_name not in seen_orgs:
                        seen_orgs.add(org_name)
                        org_ent = Entity(
                            entity_type="organization",
                            value=org_name,
                            label="ASN Organization",
                            confidence=0.9,
                            source="BGPView"
                        )
                        results.append(org_ent)
                        
                        if asn_ent:
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=asn_ent.id,
                                    target_entity_id=org_ent.id,
                                    relationship_type="registered_to",
                                    confidence=0.9,
                                    source="BGPView"
                                )
                            )
                            
                return results, relationships, {"raw_output": str(prefixes)}
                
        except Exception as e:
            return [], [], {"error": str(e)}
