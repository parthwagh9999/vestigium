"""IP Geolocation transform using HTTP API."""
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class IPGeolocationTransform(BaseTransform):
    """Transform to locate geographical location, country, city, and ISP of an IP address."""
    id = "builtin.ip_geolocation"
    name = "IP Geolocation Lookup"
    description = "Retrieves country, city, ISP, and organization details for an IP address"
    category = "Geolocation"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["country", "city", "organization", "asn"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,lat,lon,isp,org,as,query"
        
        entities = []
        relationships = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code} response from geolocation provider")
                data = resp.json()
                
            if data.get("status") != "success":
                raise RuntimeError(data.get("message", "Geolocation lookup failed"))
                
            country = data.get("country")
            city = data.get("city")
            isp = data.get("isp") or data.get("org")
            as_num = data.get("as")
            
            if country:
                e = Entity(entity_type="country", value=country, label=country, confidence=1.0, source="ip-api.com")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="located_in", confidence=1.0, source="ip-api.com"))
                
            if city:
                city_val = f"{city}, {country}" if country else city
                e = Entity(entity_type="city", value=city_val, label=city, confidence=1.0, source="ip-api.com")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="located_in", confidence=1.0, source="ip-api.com"))
                
            if isp:
                e = Entity(entity_type="organization", value=isp, label=isp, confidence=1.0, source="ip-api.com")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="hosted_by", confidence=1.0, source="ip-api.com"))
                
            if as_num:
                e = Entity(entity_type="asn", value=as_num, label=as_num, confidence=1.0, source="ip-api.com")
                entities.append(e)
                relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="belongs_to_asn", confidence=1.0, source="ip-api.com"))
                
            return entities, relationships, {"raw_data": data}
            
        except Exception as e:
            raise RuntimeError(f"Geolocation request failed: {e}")
