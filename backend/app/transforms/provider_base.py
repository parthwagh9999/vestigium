from typing import Any
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class BaseProviderTransform(BaseTransform):
    """Abstract base for transforms that can use multiple providers for the same functionality."""
    
    provider_name: str = "Unknown Provider"

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        raise NotImplementedError("Provider transforms must implement execute")
