"""Models package — all SQLAlchemy domain models.

Imports all models so Alembic and the application can discover them
through a single import.
"""

from app.models.api_key import APIKeyVault
from app.models.audit import AuditLog
from app.models.bookmark import Bookmark
from app.models.entity import Entity, EntityCustomField, EntityHistory
from app.models.evidence import Attachment, Evidence, SourceURL
from app.models.investigation import Investigation, InvestigationSnapshot, InvestigationVersion
from app.models.note import Note
from app.models.plugin import InstalledPlugin, PluginConfig
from app.models.relationship import EntityRelationship
from app.models.search import SavedQuery, SavedSearch
from app.models.tag import Tag, entity_tags, investigation_tags
from app.models.task import Task
from app.models.timeline import TimelineEvent
from app.models.transform import TransformResult, TransformRun
from app.models.user import Permission, Role, User, role_permissions, user_roles
from app.models.workspace import Workspace, workspace_members

__all__ = [
    "APIKeyVault",
    "Attachment",
    "AuditLog",
    "Bookmark",
    "Entity",
    "EntityCustomField",
    "EntityHistory",
    "EntityRelationship",
    "Evidence",
    "InstalledPlugin",
    "Investigation",
    "InvestigationSnapshot",
    "InvestigationVersion",
    "Note",
    "Permission",
    "PluginConfig",
    "Role",
    "SavedQuery",
    "SavedSearch",
    "SourceURL",
    "Tag",
    "Task",
    "TimelineEvent",
    "TransformResult",
    "TransformRun",
    "User",
    "Workspace",
    "entity_tags",
    "investigation_tags",
    "role_permissions",
    "user_roles",
    "workspace_members",
]
