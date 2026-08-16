import httpx
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class RIPEstatAdapter(BaseTransform):
    id = "builtin.ripestat"
    name = "RIPEstat Network Info"
    description = "Retrieves network routing and ASN information from RIPEstat"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["asn", "netblock"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = f"https://stat.ripe.net/data/network-info/data.json?resource={target}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"RIPEstat API returned {resp.status_code}"}
                    
                data = resp.json()
                if data.get("status") != "ok":
                    return [], [], {"error": "RIPEstat API status not OK"}
                    
                data_payload = data.get("data", {})
                asns = data_payload.get("asns", [])
                prefix = data_payload.get("prefix")
                
                if not asns and not prefix:
                    return [], [], {"message": "No routing information found."}
                    
                if prefix:
                    netblock_ent = Entity(
                        entity_type="netblock",
                        value=prefix,
                        label="Routing Prefix",
                        confidence=1.0,
                        source="RIPEstat"
                    )
                    results.append(netblock_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=netblock_ent.id,
                            relationship_type="part_of_netblock",
                            confidence=1.0,
                            source="RIPEstat"
                        )
                    )
                
                for asn in asns:
                    asn_str = str(asn)
                    if not asn_str.startswith("AS"):
                        asn_str = f"AS{asn_str}"
                        
                    asn_ent = Entity(
                        entity_type="asn",
                        value=asn_str,
                        label="Autonomous System",
                        confidence=1.0,
                        source="RIPEstat"
                    )
                    results.append(asn_ent)
                    
                    # Link IP to ASN
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=asn_ent.id,
                            relationship_type="routed_by",
                            confidence=1.0,
                            source="RIPEstat"
                        )
                    )
                    
                    # Link Netblock to ASN if both exist
                    if prefix:
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=netblock_ent.id,
                                target_entity_id=asn_ent.id,
                                relationship_type="announced_by",
                                confidence=1.0,
                                source="RIPEstat"
                            )
                        )
                            
                return results, relationships, {"raw_output": str(data_payload)}
                
        except Exception as e:
            return [], [], {"error": str(e)}
