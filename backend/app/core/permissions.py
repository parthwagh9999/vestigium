"""RBAC permission system.

Defines all system permissions and provides utilities for checking
user authorization against required permissions.
"""

from __future__ import annotations

from enum import Enum


class SystemPermission(str, Enum):
    """All system-level permissions following resource:action convention."""

    # ---- Investigation ----
    INVESTIGATION_CREATE = "investigation:create"
    INVESTIGATION_READ = "investigation:read"
    INVESTIGATION_UPDATE = "investigation:update"
    INVESTIGATION_DELETE = "investigation:delete"
    INVESTIGATION_EXPORT = "investigation:export"
    INVESTIGATION_IMPORT = "investigation:import"

    # ---- Entity ----
    ENTITY_CREATE = "entity:create"
    ENTITY_READ = "entity:read"
    ENTITY_UPDATE = "entity:update"
    ENTITY_DELETE = "entity:delete"

    # ---- Relationship ----
    RELATIONSHIP_CREATE = "relationship:create"
    RELATIONSHIP_READ = "relationship:read"
    RELATIONSHIP_UPDATE = "relationship:update"
    RELATIONSHIP_DELETE = "relationship:delete"

    # ---- Transform ----
    TRANSFORM_EXECUTE = "transform:execute"
    TRANSFORM_CANCEL = "transform:cancel"
    TRANSFORM_VIEW_HISTORY = "transform:view_history"

    # ---- Plugin ----
    PLUGIN_INSTALL = "plugin:install"
    PLUGIN_UNINSTALL = "plugin:uninstall"
    PLUGIN_CONFIGURE = "plugin:configure"
    PLUGIN_VIEW = "plugin:view"

    # ---- Workspace ----
    WORKSPACE_CREATE = "workspace:create"
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_MANAGE_MEMBERS = "workspace:manage_members"

    # ---- User Administration ----
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_ROLES = "admin:manage_roles"
    ADMIN_VIEW_AUDIT = "admin:view_audit"
    ADMIN_MANAGE_SETTINGS = "admin:manage_settings"
    ADMIN_MANAGE_BACKUPS = "admin:manage_backups"
    ADMIN_MANAGE_API_KEYS = "admin:manage_api_keys"

    # ---- Evidence ----
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_UPDATE = "evidence:update"
    EVIDENCE_DELETE = "evidence:delete"

    # ---- Search ----
    SEARCH_EXECUTE = "search:execute"
    SEARCH_SAVE = "search:save"


# ---- Default Role Definitions ----

ROLE_ADMIN_PERMISSIONS: list[SystemPermission] = list(SystemPermission)

ROLE_ANALYST_PERMISSIONS: list[SystemPermission] = [
    SystemPermission.INVESTIGATION_CREATE,
    SystemPermission.INVESTIGATION_READ,
    SystemPermission.INVESTIGATION_UPDATE,
    SystemPermission.INVESTIGATION_EXPORT,
    SystemPermission.INVESTIGATION_IMPORT,
    SystemPermission.ENTITY_CREATE,
    SystemPermission.ENTITY_READ,
    SystemPermission.ENTITY_UPDATE,
    SystemPermission.ENTITY_DELETE,
    SystemPermission.RELATIONSHIP_CREATE,
    SystemPermission.RELATIONSHIP_READ,
    SystemPermission.RELATIONSHIP_UPDATE,
    SystemPermission.RELATIONSHIP_DELETE,
    SystemPermission.TRANSFORM_EXECUTE,
    SystemPermission.TRANSFORM_CANCEL,
    SystemPermission.TRANSFORM_VIEW_HISTORY,
    SystemPermission.PLUGIN_VIEW,
    SystemPermission.WORKSPACE_READ,
    SystemPermission.EVIDENCE_CREATE,
    SystemPermission.EVIDENCE_READ,
    SystemPermission.EVIDENCE_UPDATE,
    SystemPermission.EVIDENCE_DELETE,
    SystemPermission.SEARCH_EXECUTE,
    SystemPermission.SEARCH_SAVE,
]

ROLE_VIEWER_PERMISSIONS: list[SystemPermission] = [
    SystemPermission.INVESTIGATION_READ,
    SystemPermission.ENTITY_READ,
    SystemPermission.RELATIONSHIP_READ,
    SystemPermission.TRANSFORM_VIEW_HISTORY,
    SystemPermission.PLUGIN_VIEW,
    SystemPermission.WORKSPACE_READ,
    SystemPermission.EVIDENCE_READ,
    SystemPermission.SEARCH_EXECUTE,
]

DEFAULT_ROLES: dict[str, dict] = {
    "admin": {
        "description": "Full system administrator with all permissions",
        "permissions": ROLE_ADMIN_PERMISSIONS,
        "is_system": True,
    },
    "analyst": {
        "description": "Intelligence analyst with investigation and transform permissions",
        "permissions": ROLE_ANALYST_PERMISSIONS,
        "is_system": True,
    },
    "viewer": {
        "description": "Read-only access to investigations and data",
        "permissions": ROLE_VIEWER_PERMISSIONS,
        "is_system": True,
    },
}


def check_permission(user_permissions: set[str], required: SystemPermission) -> bool:
    """Check if a set of user permissions includes the required permission.

    Args:
        user_permissions: Set of permission name strings the user has.
        required: The permission to check for.

    Returns:
        True if the user has the required permission.
    """
    return required.value in user_permissions


def get_user_permissions(roles: list) -> set[str]:
    """Extract all permission names from a user's assigned roles.

    Args:
        roles: List of Role model instances.

    Returns:
        Set of permission name strings.
    """
    permissions: set[str] = set()
    for role in roles:
        for perm in role.permissions:
            permissions.add(perm.name)
    return permissions
