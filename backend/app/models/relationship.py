"""EntityRelationship model — edges in the investigation graph.

Represents typed, weighted, directional relationships between entities
with confidence scoring and source tracking.
"""

from __future__ import annotations

import enum

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class RelationshipType(str, enum.Enum):
    """All supported relationship types between entities."""

    # ---- Ownership & Registration ----
    OWNS = "owns"
    REGISTERED_TO = "registered_to"
    HOSTED_ON = "hosted_on"
    RESOLVES_TO = "resolves_to"

    # ---- Structural ----
    CONTAINS = "contains"
    PART_OF = "part_of"
    PARENT_COMPANY = "parent_company"
    SUBSIDIARY = "subsidiary"

    # ---- People & Organizations ----
    CREATED_BY = "created_by"
    MEMBER_OF = "member_of"
    WORKS_FOR = "works_for"
    FRIEND_OF = "friend_of"
    KNOWS = "knows"

    # ---- Communication & Usage ----
    USES = "uses"
    COMMUNICATES_WITH = "communicates_with"
    CONNECTED_TO = "connected_to"

    # ---- Sharing ----
    SHARES_CERTIFICATE = "shares_certificate"
    SHARES_EMAIL = "shares_email"
    SHARES_PHONE = "shares_phone"
    SHARES_USERNAME = "shares_username"
    SHARES_IP = "shares_ip"
    SHARES_NAMESERVER = "shares_nameserver"
    SHARES_REGISTRAR = "shares_registrar"

    # ---- Identity ----
    SAME_AS = "same_as"
    ALIAS_OF = "alias_of"
    RELATED_TO = "related_to"
    LINKED_TO = "linked_to"

    # ---- Security ----
    TARGETS = "targets"
    EXPLOITS = "exploits"
    ATTRIBUTED_TO = "attributed_to"
    DISTRIBUTES = "distributes"
    DOWNLOADS_FROM = "downloads_from"
    COMMUNICATES_WITH_C2 = "communicates_with_c2"

    # ---- Financial ----
    TRANSACTS_WITH = "transacts_with"
    FUNDED_BY = "funded_by"

    # ---- Custom ----
    CUSTOM = "custom"


class EntityRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """A directed edge between two entities in the investigation graph.

    Attributes:
        source_entity_id: The entity where the relationship originates.
        target_entity_id: The entity where the relationship points to.
        relationship_type: The semantic type of the relationship.
        label: Custom display label for the edge.
        weight: Numeric weight for graph analysis algorithms.
        confidence: Confidence score (0.0 to 1.0) of this relationship.
        source: Where this relationship was discovered.
        properties: JSON-serialized additional properties.
    """

    __tablename__ = "entity_relationships"
    
    __table_args__ = (
        UniqueConstraint("investigation_id", "source_entity_id", "target_entity_id", "relationship_type", name="uix_investigation_source_target_type"),
    )

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    label: Mapped[str | None] = mapped_column(String(500), nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    properties: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_bidirectional: Mapped[bool] = mapped_column(default=False, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    style: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="relationships",
    )
    source_entity: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="source_relationships",
    )
    target_entity: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[target_entity_id],
        back_populates="target_relationships",
    )

    def __repr__(self) -> str:
        return (
            f"<EntityRelationship(id={self.id}, "
            f"{self.source_entity_id} --[{self.relationship_type}]--> {self.target_entity_id})>"
        )
