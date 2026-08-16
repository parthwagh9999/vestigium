"""Audit logging service for tracking all user actions."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording audit log entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        investigation_id: str | None = None,
    ) -> AuditLog:
        """Record an audit log entry.

        Args:
            action: The action performed.
            resource_type: The type of resource affected.
            resource_id: The ID of the resource.
            user_id: The user who performed the action.
            details: Additional details as a dictionary.
            ip_address: Client IP address.
            user_agent: Client user agent string.
            before_state: State before the action.
            after_state: State after the action.
            investigation_id: Related investigation ID.

        Returns:
            The created AuditLog entry.
        """
        entry = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            before_state=json.dumps(before_state) if before_state else None,
            after_state=json.dumps(after_state) if after_state else None,
            investigation_id=investigation_id,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
