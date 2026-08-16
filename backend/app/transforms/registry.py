"""Transform registry for discovery and management of installed transforms."""

from __future__ import annotations

import logging
from typing import Type

from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class TransformRegistry:
    """Registry that holds all registered transform classes and instances."""

    def __init__(self) -> None:
        self._transforms: dict[str, BaseTransform] = {}

    def register(self, transform_cls: type[BaseTransform]) -> BaseTransform:
        """Register a transform class.

        Args:
            transform_cls: Class inheriting from BaseTransform

        Returns:
            Instantiated transform instance
        """
        instance = transform_cls()
        if instance.id in self._transforms:
            logger.warning("Overwriting registered transform with ID: %s", instance.id)
        self._transforms[instance.id] = instance
        logger.debug("Registered transform: %s (%s)", instance.name, instance.id)
        return instance

    def get(self, transform_id: str) -> BaseTransform | None:
        """Retrieve transform instance by ID."""
        return self._transforms.get(transform_id)

    def list_all(self) -> list[BaseTransform]:
        """List all active registered transforms."""
        return [t for t in self._transforms.values() if t.is_active]

    def get_by_input_type(self, input_type: str) -> list[BaseTransform]:
        """Get all transforms that accept a specific input entity type or alias."""
        results = []
        normalized_type = input_type.lower().strip()
        aliases = {normalized_type}
        if normalized_type in ("domain", "subdomain", "url", "website"):
            aliases.update(["domain", "subdomain", "url", "website"])
        elif normalized_type in ("ip", "ip_address", "ipv4", "ipv6", "server"):
            aliases.update(["ip_address", "ipv6_address", "server"])
        for transform in self.list_all():
            if "*" in transform.input_entity_types or any(t in transform.input_entity_types for t in aliases):
                results.append(transform)
        return results

    def get_categories(self) -> list[str]:
        """List unique categories of all registered transforms."""
        return sorted(list({t.category for t in self.list_all()}))

    def get_stats(self) -> dict[str, int]:
        """Compute ecosystem statistics across all registered transforms."""
        all_t = self.list_all()
        return {
            "total": len(all_t),
            "available": sum(1 for t in all_t if t.availability_status == "AVAILABLE"),
            "api_required": sum(1 for t in all_t if t.api_key_required or t.requires_api_key),
            "installation_required": sum(1 for t in all_t if t.installation_required or t.execution_type == "binary"),
            "not_installed": sum(1 for t in all_t if t.availability_status == "NOT_INSTALLED"),
            "passive": sum(1 for t in all_t if t.passive_or_active == "PASSIVE" or t.is_passive),
            "active_authorized": sum(1 for t in all_t if t.passive_or_active == "ACTIVE_AUTHORIZED"),
        }

    def refresh_availability(self, configured_keys: set[str] | None = None) -> None:
        """Run truthful availability probe across all registered transforms."""
        for transform in self._transforms.values():
            transform.check_availability(configured_keys)


# Global singleton transform registry
transform_registry = TransformRegistry()
