"""Entity model — the core node type for the investigation graph.

Uses a single-table design with a JSON properties column for maximum flexibility.
Each entity has a type (from the EntityType enum) and type-specific properties
stored as JSON. This allows adding new entity types without schema migrations.

Supports:
    - 100+ entity types across all OSINT categories
    - Custom fields per entity instance
    - Confidence scoring and source tracking
    - Full history/audit trail
    - Attachments and notes
"""

from __future__ import annotations

import enum

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EntityType(str, enum.Enum):
    """All supported entity types organized by category.

    The entity type determines which icon, color, and property schema
    is used for display and validation.
    """

    # ---- People & Organizations ----
    PERSON = "person"
    ORGANIZATION = "organization"
    COMPANY = "company"

    # ---- Network Infrastructure ----
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    URL = "url"
    IP_ADDRESS = "ip_address"
    IPV6_ADDRESS = "ipv6_address"
    ASN = "asn"
    NETBLOCK = "netblock"

    # ---- DNS Records ----
    DNS_RECORD = "dns_record"
    MX_RECORD = "mx_record"
    TXT_RECORD = "txt_record"
    SPF_RECORD = "spf_record"
    DKIM_RECORD = "dkim_record"
    DMARC_RECORD = "dmarc_record"
    NS_RECORD = "ns_record"
    SOA_RECORD = "soa_record"
    PTR_RECORD = "ptr_record"
    SRV_RECORD = "srv_record"
    CNAME_RECORD = "cname_record"

    # ---- Communication ----
    EMAIL = "email"
    PHONE = "phone"
    USERNAME = "username"

    # ---- Web & Infrastructure ----
    CERTIFICATE = "certificate"
    WEBSITE = "website"
    SERVER = "server"
    CLOUD_ASSET = "cloud_asset"

    # ---- Code & Repositories ----
    REPOSITORY = "repository"
    GITHUB_USER = "github_user"
    GITLAB_USER = "gitlab_user"

    # ---- Social Media ----
    SOCIAL_PROFILE = "social_profile"
    TWITTER_PROFILE = "twitter_profile"
    FACEBOOK_PROFILE = "facebook_profile"
    INSTAGRAM_PROFILE = "instagram_profile"
    LINKEDIN_PROFILE = "linkedin_profile"
    TIKTOK_PROFILE = "tiktok_profile"
    YOUTUBE_PROFILE = "youtube_profile"
    REDDIT_PROFILE = "reddit_profile"
    TELEGRAM_PROFILE = "telegram_profile"
    DISCORD_PROFILE = "discord_profile"
    MASTODON_PROFILE = "mastodon_profile"

    # ---- Cryptocurrency ----
    WALLET = "wallet"
    BITCOIN_WALLET = "bitcoin_wallet"
    ETHEREUM_WALLET = "ethereum_wallet"

    # ---- Files ----
    FILE = "file"
    PDF_FILE = "pdf_file"
    WORD_FILE = "word_file"
    EXCEL_FILE = "excel_file"
    POWERPOINT_FILE = "powerpoint_file"
    ZIP_FILE = "zip_file"
    IMAGE_FILE = "image_file"
    VIDEO_FILE = "video_file"
    AUDIO_FILE = "audio_file"

    # ---- Security & Threat Intelligence ----
    MALWARE = "malware"
    HASH = "hash"
    IOC = "ioc"
    CVE = "cve"
    THREAT_ACTOR = "threat_actor"
    CAMPAIGN = "campaign"

    # ---- Geolocation ----
    STREET_ADDRESS = "street_address"
    COUNTRY = "country"
    CITY = "city"
    GPS_COORDINATE = "gps_coordinate"

    # ---- Custom ----
    CUSTOM = "custom"


# Default icon mapping for entity types
ENTITY_ICONS: dict[str, str] = {
    EntityType.PERSON: "user",
    EntityType.ORGANIZATION: "building",
    EntityType.COMPANY: "briefcase",
    EntityType.DOMAIN: "globe",
    EntityType.SUBDOMAIN: "globe-alt",
    EntityType.URL: "link",
    EntityType.IP_ADDRESS: "server",
    EntityType.IPV6_ADDRESS: "server",
    EntityType.ASN: "network",
    EntityType.NETBLOCK: "network",
    EntityType.EMAIL: "envelope",
    EntityType.PHONE: "phone",
    EntityType.USERNAME: "at-sign",
    EntityType.CERTIFICATE: "shield-check",
    EntityType.WEBSITE: "browser",
    EntityType.SERVER: "database",
    EntityType.CLOUD_ASSET: "cloud",
    EntityType.REPOSITORY: "code",
    EntityType.GITHUB_USER: "github",
    EntityType.GITLAB_USER: "gitlab",
    EntityType.SOCIAL_PROFILE: "share",
    EntityType.TWITTER_PROFILE: "twitter",
    EntityType.FACEBOOK_PROFILE: "facebook",
    EntityType.INSTAGRAM_PROFILE: "instagram",
    EntityType.LINKEDIN_PROFILE: "linkedin",
    EntityType.WALLET: "wallet",
    EntityType.BITCOIN_WALLET: "bitcoin",
    EntityType.ETHEREUM_WALLET: "ethereum",
    EntityType.FILE: "file",
    EntityType.IMAGE_FILE: "image",
    EntityType.VIDEO_FILE: "video",
    EntityType.AUDIO_FILE: "music",
    EntityType.MALWARE: "bug",
    EntityType.HASH: "hash",
    EntityType.IOC: "alert-triangle",
    EntityType.CVE: "shield-alert",
    EntityType.THREAT_ACTOR: "skull",
    EntityType.CAMPAIGN: "flag",
    EntityType.STREET_ADDRESS: "map-pin",
    EntityType.COUNTRY: "flag",
    EntityType.CITY: "building-2",
    EntityType.GPS_COORDINATE: "map",
    EntityType.CUSTOM: "puzzle",
}

# Default color mapping for entity types
ENTITY_COLORS: dict[str, str] = {
    EntityType.PERSON: "#3B82F6",
    EntityType.ORGANIZATION: "#8B5CF6",
    EntityType.COMPANY: "#6366F1",
    EntityType.DOMAIN: "#10B981",
    EntityType.SUBDOMAIN: "#34D399",
    EntityType.URL: "#06B6D4",
    EntityType.IP_ADDRESS: "#F59E0B",
    EntityType.IPV6_ADDRESS: "#F59E0B",
    EntityType.ASN: "#D97706",
    EntityType.NETBLOCK: "#D97706",
    EntityType.EMAIL: "#EC4899",
    EntityType.PHONE: "#14B8A6",
    EntityType.USERNAME: "#8B5CF6",
    EntityType.CERTIFICATE: "#22C55E",
    EntityType.WEBSITE: "#0EA5E9",
    EntityType.SERVER: "#64748B",
    EntityType.CLOUD_ASSET: "#38BDF8",
    EntityType.REPOSITORY: "#A3A3A3",
    EntityType.GITHUB_USER: "#171717",
    EntityType.SOCIAL_PROFILE: "#E11D48",
    EntityType.TWITTER_PROFILE: "#1DA1F2",
    EntityType.FACEBOOK_PROFILE: "#1877F2",
    EntityType.INSTAGRAM_PROFILE: "#E4405F",
    EntityType.LINKEDIN_PROFILE: "#0A66C2",
    EntityType.WALLET: "#F7931A",
    EntityType.BITCOIN_WALLET: "#F7931A",
    EntityType.ETHEREUM_WALLET: "#627EEA",
    EntityType.FILE: "#78716C",
    EntityType.MALWARE: "#EF4444",
    EntityType.HASH: "#71717A",
    EntityType.IOC: "#F97316",
    EntityType.CVE: "#DC2626",
    EntityType.THREAT_ACTOR: "#7C3AED",
    EntityType.CAMPAIGN: "#E11D48",
    EntityType.STREET_ADDRESS: "#059669",
    EntityType.COUNTRY: "#2563EB",
    EntityType.CITY: "#0891B2",
    EntityType.GPS_COORDINATE: "#16A34A",
    EntityType.CUSTOM: "#6B7280",
}


class Entity(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """A node in the investigation graph representing an OSINT entity.

    The entity uses a single-table design with a JSON `properties` column
    that holds type-specific data. This enables adding new entity types
    without database migrations.

    Attributes:
        entity_type: The classification of this entity.
        label: Human-readable display label.
        value: The primary value (e.g., "example.com", "192.168.1.1").
        properties: JSON-serialized type-specific properties.
        confidence: Confidence score (0.0 to 1.0) of this entity's validity.
        source: Where this entity was discovered or created from.
        icon: Custom icon override (defaults come from ENTITY_ICONS).
        color: Custom color override (defaults come from ENTITY_COLORS).
        position_x: X coordinate on the investigation canvas.
        position_y: Y coordinate on the investigation canvas.
    """

    __tablename__ = "entities"
    
    __table_args__ = (
        UniqueConstraint("investigation_id", "entity_type", "value", name="uix_investigation_entity_type_value"),
    )

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    value: Mapped[str] = mapped_column(String(2000), nullable=False, index=True)
    properties: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    position_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="entities",
        foreign_keys="[Entity.investigation_id]"
    )
    custom_fields: Mapped[list[EntityCustomField]] = relationship(
        "EntityCustomField",
        back_populates="entity",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    history_entries: Mapped[list[EntityHistory]] = relationship(
        "EntityHistory",
        back_populates="entity",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    source_relationships: Mapped[list] = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    target_relationships: Mapped[list] = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id}, type={self.entity_type}, value={self.value[:50]})>"


class EntityCustomField(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Custom key-value fields attached to an entity.

    Allows users to add arbitrary metadata to any entity instance
    beyond the standard properties.
    """

    __tablename__ = "entity_custom_fields"

    entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)

    # Relationships
    entity: Mapped[Entity] = relationship(
        "Entity",
        back_populates="custom_fields",
    )

    def __repr__(self) -> str:
        return f"<EntityCustomField(entity_id={self.entity_id}, name={self.field_name})>"


class EntityHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit history entry for entity changes.

    Tracks every modification to an entity, including who made the change,
    what fields were changed, and the before/after values.
    """

    __tablename__ = "entity_history"

    entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_state: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    entity: Mapped[Entity] = relationship(
        "Entity",
        back_populates="history_entries",
    )

    def __repr__(self) -> str:
        return f"<EntityHistory(entity_id={self.entity_id}, action={self.action})>"
