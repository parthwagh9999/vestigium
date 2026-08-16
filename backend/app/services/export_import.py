"""Export and Import Service for investigations, entities, relationships, and graphs."""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExportError, ImportError_, NotFoundError
from app.models.entity import Entity
from app.models.investigation import Investigation
from app.models.relationship import EntityRelationship
from app.repositories.entity import EntityRepository
from app.repositories.investigation import InvestigationRepository
from app.repositories.relationship import RelationshipRepository
from app.services.graph import GraphService

logger = logging.getLogger(__name__)


class ExportImportService:
    """Service handling JSON, CSV, and GraphML export and import operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.investigation_repo = InvestigationRepository(session)
        self.entity_repo = EntityRepository(session)
        self.relationship_repo = RelationshipRepository(session)
        self.graph_service = GraphService(session)

    async def export_json(self, investigation_id: str) -> dict[str, Any]:
        """Export an entire investigation to a structured JSON object.

        Args:
            investigation_id: Investigation ID to export

        Returns:
            Structured dictionary suitable for JSON serialization
        """
        inv = await self.investigation_repo.get_by_id(investigation_id)
        if not inv:
            raise NotFoundError("Investigation", investigation_id)

        entities = await self.entity_repo.get_by_investigation(investigation_id, limit=100000)
        relationships = await self.relationship_repo.get_by_investigation(investigation_id, limit=100000)

        entities_data = []
        for e in entities:
            props = json.loads(e.properties) if e.properties else None
            entities_data.append(
                {
                    "id": e.id,
                    "entity_type": e.entity_type,
                    "label": e.label,
                    "value": e.value,
                    "properties": props,
                    "confidence": e.confidence,
                    "source": e.source,
                    "icon": e.icon,
                    "color": e.color,
                    "position_x": e.position_x,
                    "position_y": e.position_y,
                    "is_pinned": e.is_pinned,
                    "notes_text": e.notes_text,
                }
            )

        relationships_data = []
        for r in relationships:
            props = json.loads(r.properties) if r.properties else None
            relationships_data.append(
                {
                    "id": r.id,
                    "source_entity_id": r.source_entity_id,
                    "target_entity_id": r.target_entity_id,
                    "relationship_type": r.relationship_type,
                    "label": r.label,
                    "weight": r.weight,
                    "confidence": r.confidence,
                    "source": r.source,
                    "properties": props,
                    "is_bidirectional": r.is_bidirectional,
                    "color": r.color,
                    "style": r.style,
                }
            )

        return {
            "version": "1.0",
            "exporter": "VESTIGIUM",
            "investigation": {
                "id": inv.id,
                "name": inv.name,
                "description": inv.description,
                "status": inv.status,
                "priority": inv.priority,
                "icon": inv.icon,
                "color": inv.color,
            },
            "entities": entities_data,
            "relationships": relationships_data,
        }

    async def import_json(self, workspace_id: str, data: dict[str, Any], user_id: str | None = None) -> Investigation:
        """Import an investigation from a structured JSON export.

        Args:
            workspace_id: Target workspace
            data: Loaded JSON object
            user_id: Importing user ID

        Returns:
            Created Investigation object
        """
        inv_data = data.get("investigation", {})
        if not inv_data.get("name"):
            raise ImportError_("JSON", "Missing investigation name in import file")

        # Create Investigation
        inv = await self.investigation_repo.create(
            workspace_id=workspace_id,
            owner_id=user_id,
            name=f"{inv_data.get('name')} (Imported)",
            description=inv_data.get("description"),
            status=inv_data.get("status", "active"),
            priority=inv_data.get("priority", "medium"),
            icon=inv_data.get("icon"),
            color=inv_data.get("color"),
        )

        id_mapping: dict[str, str] = {}

        # Import entities
        for e_item in data.get("entities", []):
            old_id = e_item.get("id")
            props = json.dumps(e_item.get("properties")) if e_item.get("properties") else None
            new_entity = await self.entity_repo.create(
                investigation_id=inv.id,
                entity_type=e_item.get("entity_type", "custom"),
                label=e_item.get("label", "Imported Entity"),
                value=e_item.get("value", ""),
                properties=props,
                confidence=e_item.get("confidence", 1.0),
                source=e_item.get("source", "JSON Import"),
                icon=e_item.get("icon"),
                color=e_item.get("color"),
                position_x=e_item.get("position_x", 0.0),
                position_y=e_item.get("position_y", 0.0),
                is_pinned=e_item.get("is_pinned", False),
                notes_text=e_item.get("notes_text"),
            )
            if old_id:
                id_mapping[old_id] = new_entity.id

        # Import relationships
        for r_item in data.get("relationships", []):
            old_source = r_item.get("source_entity_id")
            old_target = r_item.get("target_entity_id")

            new_source = id_mapping.get(old_source)
            new_target = id_mapping.get(old_target)

            if new_source and new_target:
                props = json.dumps(r_item.get("properties")) if r_item.get("properties") else None
                await self.relationship_repo.create(
                    investigation_id=inv.id,
                    source_entity_id=new_source,
                    target_entity_id=new_target,
                    relationship_type=r_item.get("relationship_type", "related_to"),
                    label=r_item.get("label"),
                    weight=r_item.get("weight", 1.0),
                    confidence=r_item.get("confidence", 1.0),
                    source=r_item.get("source", "JSON Import"),
                    properties=props,
                    is_bidirectional=r_item.get("is_bidirectional", False),
                    color=r_item.get("color"),
                    style=r_item.get("style"),
                )

        await self.session.commit()
        return inv

    async def export_graphml(self, investigation_id: str) -> str:
        """Export investigation graph to GraphML format string.

        Args:
            investigation_id: Investigation ID

        Returns:
            GraphML XML string representation
        """
        nx_graph = await self.graph_service.build_networkx_graph(investigation_id)
        output = io.BytesIO()
        nx.write_graphml(nx_graph, output)
        return output.getvalue().decode("utf-8")

    async def export_csv(self, investigation_id: str) -> str:
        """Export entities list of investigation to CSV string format."""
        entities = await self.entity_repo.get_by_investigation(investigation_id, limit=100000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Entity Type", "Label", "Value", "Confidence", "Source", "Position X", "Position Y"])

        for e in entities:
            writer.writerow([e.id, e.entity_type, e.label, e.value, e.confidence, e.source or "", e.position_x, e.position_y])

        return output.getvalue()
