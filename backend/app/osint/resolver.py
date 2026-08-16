"""Entity resolver for the OSINT Pipeline.

Ensures zero-duplicate graphs by canonicalizing and merging entities.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entity import Entity
from app.osint.normalizer import normalize_entity_value

logger = logging.getLogger(__name__)

async def resolve_entity(
    db: AsyncSession, 
    investigation_id: str, 
    entity_type: str, 
    raw_value: str,
    create_if_missing: bool = True
) -> Entity | None:
    """
    Resolve an entity to ensure no duplicates exist in the investigation.
    
    Applies normalization, searches for existing entities by value/alias,
    and optionally creates a new canonical entity.
    """
    normalized_value = normalize_entity_value(entity_type, raw_value)
    
    # First, try to find an exact match for the normalized value
    stmt = select(Entity).where(
        Entity.investigation_id == investigation_id,
        Entity.entity_type == entity_type,
        Entity.value == normalized_value
    )
    result = await db.execute(stmt)
    existing_entity = result.scalars().first()
    
    if existing_entity:
        return existing_entity
        
    # TODO: Add fuzzy alias matching here if needed
    
    if not create_if_missing:
        return None
        
    # If not found, create a new entity
    new_entity = Entity(
        investigation_id=investigation_id,
        entity_type=entity_type,
        value=normalized_value,
        label=normalized_value,
        confidence=1.0  # Base confidence
    )
    db.add(new_entity)
    await db.flush()
    return new_entity
