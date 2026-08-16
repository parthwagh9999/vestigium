import asyncio
import re
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class BGPToolsAdapter(BaseTransform):
    id = "builtin.bgptools"
    name = "bgp.tools DNS Lookup"
    description = "Retrieves ASN and Routing intel via bgp.tools DNS TXT records"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address"]
    output_entity_types = ["asn", "netblock"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        
        # bgp.tools allows querying IP.asn.bgp.tools for TXT records
        query = f"{target}.asn.bgp.tools"
        cmd = ["nslookup", "-type=txt", query]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # nslookup output for TXT usually looks like:
            # "13335 | 1.1.1.0/24 | US | cloudflare.com | Cloudflare, Inc."
            
            txt_match = re.search(r'"([^"]+)"', output)
            if not txt_match:
                return [], [], {"message": "No bgp.tools TXT record found."}
                
            record = txt_match.group(1)
            parts = [p.strip() for p in record.split('|')]
            
            if len(parts) >= 2:
                asn_id = parts[0]
                prefix = parts[1]
                
                asn_ent = Entity(
                    entity_type="asn",
                    value=f"AS{asn_id}",
                    label="Autonomous System",
                    confidence=1.0,
                    source="bgp.tools"
                )
                results.append(asn_ent)
                
                netblock_ent = Entity(
                    entity_type="netblock",
                    value=prefix,
                    label="BGP Prefix",
                    confidence=1.0,
                    source="bgp.tools"
                )
                results.append(netblock_ent)
                
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=asn_ent.id,
                        relationship_type="routed_by",
                        confidence=1.0,
                        source="bgp.tools"
                    )
                )
                
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=netblock_ent.id,
                        relationship_type="part_of_netblock",
                        confidence=1.0,
                        source="bgp.tools"
                    )
                )
                
                relationships.append(
                    EntityRelationship(
                        source_entity_id=netblock_ent.id,
                        target_entity_id=asn_ent.id,
                        relationship_type="announced_by",
                        confidence=1.0,
                        source="bgp.tools"
                    )
                )
                
                if len(parts) >= 5:
                    org_name = parts[4]
                    org_ent = Entity(
                        entity_type="organization",
                        value=org_name,
                        label="ASN Organization",
                        confidence=0.9,
                        source="bgp.tools"
                    )
                    results.append(org_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=asn_ent.id,
                            target_entity_id=org_ent.id,
                            relationship_type="registered_to",
                            confidence=0.9,
                            source="bgp.tools"
                        )
                    )
                            
            return results, relationships, {"raw_output": record}
                
        except Exception as e:
            return [], [], {"error": str(e)}
