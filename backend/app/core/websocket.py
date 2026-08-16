"""WebSocket manager for real-time graph collaboration.

Handles per-investigation connection pools and broadcasts graph
mutations to all connected clients in the same investigation.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by investigation ID.

    Each investigation maintains its own set of connected clients.
    When a graph mutation occurs, the change is broadcast to all
    other clients viewing the same investigation.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_map: dict[WebSocket, dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        investigation_id: str,
        user_id: str | None = None,
        username: str | None = None,
    ) -> None:
        """Accept a WebSocket connection and add it to the investigation pool.

        Args:
            websocket: The WebSocket connection.
            investigation_id: The investigation to join.
            user_id: Optional authenticated user ID.
            username: Optional username for display.
        """
        await websocket.accept()
        self._connections[investigation_id].add(websocket)
        self._user_map[websocket] = {
            "user_id": user_id,
            "username": username,
            "investigation_id": investigation_id,
        }

        # Notify others of new participant
        await self.broadcast(
            investigation_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "active_users": self._get_active_users(investigation_id),
            },
            exclude=websocket,
        )

        logger.info(
            "WebSocket connected: user=%s investigation=%s (total=%d)",
            username,
            investigation_id,
            len(self._connections[investigation_id]),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and notify others.

        Args:
            websocket: The WebSocket connection to remove.
        """
        info = self._user_map.pop(websocket, {})
        investigation_id = info.get("investigation_id")

        if investigation_id and investigation_id in self._connections:
            self._connections[investigation_id].discard(websocket)

            if not self._connections[investigation_id]:
                del self._connections[investigation_id]
            else:
                await self.broadcast(
                    investigation_id,
                    {
                        "type": "user_left",
                        "user_id": info.get("user_id"),
                        "username": info.get("username"),
                        "active_users": self._get_active_users(investigation_id),
                    },
                )

            logger.info(
                "WebSocket disconnected: user=%s investigation=%s",
                info.get("username"),
                investigation_id,
            )

    async def broadcast(
        self,
        investigation_id: str,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ) -> None:
        """Broadcast a message to all connections in an investigation.

        Args:
            investigation_id: The investigation to broadcast to.
            message: The message payload.
            exclude: Optional WebSocket to exclude from broadcast.
        """
        if investigation_id not in self._connections:
            return

        payload = json.dumps(message, default=str)
        disconnected: list[WebSocket] = []

        for connection in self._connections[investigation_id]:
            if connection is exclude:
                continue
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a specific WebSocket connection.

        Args:
            websocket: The target connection.
            message: The message payload.
        """
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            await self.disconnect(websocket)

    def _get_active_users(self, investigation_id: str) -> list[dict[str, Any]]:
        """Get list of active users in an investigation."""
        users = []
        for ws in self._connections.get(investigation_id, set()):
            info = self._user_map.get(ws, {})
            if info.get("user_id"):
                users.append({
                    "user_id": info["user_id"],
                    "username": info.get("username"),
                })
        return users

    def get_connection_count(self, investigation_id: str | None = None) -> int:
        """Get the number of active connections.

        Args:
            investigation_id: If provided, count for a specific investigation.

        Returns:
            Number of active connections.
        """
        if investigation_id:
            return len(self._connections.get(investigation_id, set()))
        return sum(len(conns) for conns in self._connections.values())


# Singleton instance
manager = ConnectionManager()
