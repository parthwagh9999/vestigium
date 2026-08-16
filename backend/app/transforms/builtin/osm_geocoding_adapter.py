"""OpenStreetMap Nominatim Geospatial and Reverse Geocoding Transform."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class OSMGeocodingTransform(BaseTransform):
    """OpenStreetMap Nominatim Geocoding and Reverse Geocoding."""

    id = "builtin.osm_geocoding"
    name = "OpenStreetMap Geospatial Geocoder"
    description = "Convert city, country, or street address into GPS coordinates, or reverse geocode latitude/longitude coordinates to location entities."
    category = "Geospatial Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "OpenStreetMap / Nominatim"
    documentation_url = "https://nominatim.org/release-docs/latest/api/Overview/"
    license = "ODbL"

    input_entity_types = ["country", "city", "street_address", "gps_coordinate"]
    output_entity_types = ["gps_coordinate", "country", "city"]
    relationships_created = ["located_at_coordinates", "part_of_country"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    installation_required = False
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 15
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        query_val = entity.value.strip()
        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_result: dict[str, Any] = {}

        headers = {"User-Agent": "VESTIGIUM-OSINT-Geospatial/1.0 (contact@vestigium-intel.local)"}

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            # 1. Reverse Geocoding (Input is "lat, lon")
            if "," in query_val and all(p.strip().replace("-", "").replace(".", "").isdigit() for p in query_val.split(",")):
                lat, lon = [p.strip() for p in query_val.split(",", 1)]
                try:
                    resp = await client.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}")
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_result = data
                        address = data.get("address", {})
                        country = address.get("country", "")
                        city = address.get("city") or address.get("town") or address.get("village", "")

                        if country:
                            country_ent = Entity(
                                entity_type="country",
                                value=country,
                                label=f"Country: {country}",
                                confidence=1.0,
                                source="OSM Nominatim",
                                properties={"country_code": address.get("country_code", "").upper()},
                            )
                            entities.append(country_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=country_ent.id,
                                    relationship_type="part_of_country",
                                    confidence=1.0,
                                    source="OSM Nominatim",
                                    label="country",
                                )
                            )

                        if city:
                            city_ent = Entity(
                                entity_type="city",
                                value=city,
                                label=f"City: {city}",
                                confidence=1.0,
                                source="OSM Nominatim",
                                properties={"city": city, "country": country},
                            )
                            entities.append(city_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=city_ent.id,
                                    relationship_type="located_in",
                                    confidence=1.0,
                                    source="OSM Nominatim",
                                    label="city",
                                )
                            )
                except Exception as e:
                    logger.debug("OSM reverse geocoding error: %s", e)

            # 2. Forward Geocoding (Input is place/country/city name)
            else:
                try:
                    resp = await client.get(f"https://nominatim.openstreetmap.org/search?format=json&q={query_val}&limit=1")
                    if resp.status_code == 200 and resp.json():
                        place = resp.json()[0]
                        raw_result = place
                        lat = place.get("lat")
                        lon = place.get("lon")
                        display_name = place.get("display_name", query_val)

                        if lat and lon:
                            gps_coord = f"{lat}, {lon}"
                            gps_ent = Entity(
                                entity_type="gps_coordinate",
                                value=gps_coord,
                                label=f"GPS: {gps_coord} ({display_name[:40]}...)",
                                confidence=1.0,
                                source="OSM Nominatim",
                                properties={"latitude": float(lat), "longitude": float(lon), "display_name": display_name},
                            )
                            entities.append(gps_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=gps_ent.id,
                                    relationship_type="located_at_coordinates",
                                    confidence=1.0,
                                    source="OSM Nominatim",
                                    label="coordinates",
                                )
                            )
                except Exception as e:
                    logger.debug("OSM forward geocoding error: %s", e)

        return entities, relationships, raw_result
