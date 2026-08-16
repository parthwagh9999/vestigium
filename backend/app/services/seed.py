"""Database seeding service for default roles, permissions, and initial admin user.

Called during application startup to ensure required system data exists.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_ROLES, SystemPermission
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.user import Permission, Role, User, role_permissions, user_roles

logger = logging.getLogger(__name__)


async def seed_defaults() -> None:
    """Seed default permissions, roles, and admin user if they don't exist.

    This is idempotent — safe to call on every startup.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            await _seed_permissions(session)
            await _seed_roles(session)
            await _seed_admin_user(session)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Failed to seed defaults")
            raise


async def _seed_permissions(session: AsyncSession) -> None:
    """Create all system permissions if they don't exist."""
    existing = await session.execute(select(Permission.name))
    existing_names = {row[0] for row in existing}

    new_permissions = []
    for perm in SystemPermission:
        if perm.value not in existing_names:
            parts = perm.value.split(":")
            resource = parts[0] if len(parts) > 1 else "system"
            action = parts[1] if len(parts) > 1 else parts[0]

            new_permissions.append(
                Permission(
                    id=str(uuid.uuid4()),
                    name=perm.value,
                    resource=resource,
                    action=action,
                    description=f"Permission to {action} {resource}",
                )
            )

    if new_permissions:
        session.add_all(new_permissions)
        await session.flush()
        logger.info("Created %d permissions", len(new_permissions))


async def _seed_roles(session: AsyncSession) -> None:
    """Create default system roles with their permissions."""
    existing = await session.execute(select(Role.name))
    existing_names = {row[0] for row in existing}

    for role_name, role_def in DEFAULT_ROLES.items():
        if role_name not in existing_names:
            role = Role(
                id=str(uuid.uuid4()),
                name=role_name,
                description=role_def["description"],
                is_system=role_def.get("is_system", True),
            )
            session.add(role)
            await session.flush()

            perm_names = [p.value for p in role_def["permissions"]]
            result = await session.execute(
                select(Permission).where(Permission.name.in_(perm_names))
            )
            permissions = list(result.scalars().all())
            for perm in permissions:
                await session.execute(
                    insert(role_permissions).values(role_id=role.id, permission_id=perm.id)
                )
            await session.flush()
            logger.info("Created role '%s' with %d permissions", role_name, len(permissions))


async def _seed_admin_user(session: AsyncSession) -> None:
    """Create default admin user if no users exist."""
    result = await session.execute(select(User).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    admin_role_result = await session.execute(
        select(Role).where(Role.name == "admin")
    )
    admin_role = admin_role_result.scalar_one_or_none()

    admin = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="admin@localhost",
        hashed_password=hash_password("Admin123!"),
        full_name="System Administrator",
        is_active=True,
        is_superuser=True,
    )

    session.add(admin)
    await session.flush()

    if admin_role:
        await session.execute(
            insert(user_roles).values(user_id=admin.id, role_id=admin_role.id)
        )
        await session.flush()
    logger.info("Created default admin user (username: admin, password: Admin123!)")
