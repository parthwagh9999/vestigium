import httpx
import re
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class IPinfoAdapter(BaseTransform):
    id = "builtin.ipinfo"
    name = "IPinfo.io Intel"
    description = "Retrieves geolocation, hostname, and ASN from IPinfo.io"
    category = "Network Intelligence"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["location", "asn", "organization", "domain"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        url = f"https://ipinfo.io/{target}/json"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code == 429:
                    return [], [], {"error": "IPinfo API rate limit exceeded."}
                if resp.status_code != 200:
                    return [], [], {"error": f"IPinfo API returned {resp.status_code}"}
                    
                data = resp.json()
                if "bogon" in data:
                    return [], [], {"message": "IP is a bogon/local address."}
                    
                city = data.get("city")
                country = data.get("country")
                if city and country:
                    loc_name = f"{city}, {country}"
                    loc_ent = Entity(
                        entity_type="location",
                        value=loc_name,
                        label="Geolocation",
                        confidence=0.9,
                        source="IPinfo"
                    )
                    loc_ent.properties = {
                        "coordinates": data.get("loc"),
                        "region": data.get("region")
                    }
                    results.append(loc_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=loc_ent.id,
                            relationship_type="located_in",
                            confidence=0.9,
                            source="IPinfo"
                        )
                    )
                    
                hostname = data.get("hostname")
                if hostname:
                    host_ent = Entity(
                        entity_type="domain",
                        value=hostname,
                        label="Hostname",
                        confidence=0.9,
                        source="IPinfo"
                    )
                    results.append(host_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=host_ent.id,
                            relationship_type="resolves_to",
                            confidence=0.9,
                            source="IPinfo"
                        )
                    )
                    
                org_field = data.get("org")
                if org_field:
                    # Usually formatted as "AS12345 Organization Name"
                    asn_match = re.match(r'(AS\d+)\s+(.*)', org_field)
                    if asn_match:
                        asn_str = asn_match.group(1)
                        org_name = asn_match.group(2)
                        
                        asn_ent = Entity(
                            entity_type="asn",
                            value=asn_str,
                            label="Autonomous System",
                            confidence=0.9,
                            source="IPinfo"
                        )
                        results.append(asn_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=asn_ent.id,
                                relationship_type="routed_by",
                                confidence=0.9,
                                source="IPinfo"
                            )
                        )
                        
                        org_ent = Entity(
                            entity_type="organization",
                            value=org_name,
                            label="Organization",
                            confidence=0.9,
                            source="IPinfo"
                        )
                        results.append(org_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=asn_ent.id,
                                target_entity_id=org_ent.id,
                                relationship_type="registered_to",
                                confidence=0.9,
                                source="IPinfo"
                            )
                        )
                    else:
                        # Just an org name
                        org_ent = Entity(
                            entity_type="organization",
                            value=org_field,
                            label="Organization",
                            confidence=0.9,
                            source="IPinfo"
                        )
                        results.append(org_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=org_ent.id,
                                relationship_type="owned_by",
                                confidence=0.9,
                                source="IPinfo"
                            )
                        )
                            
                return results, relationships, {"raw_output": str(data)}
                
        except Exception as e:
            return [], [], {"error": str(e)}
