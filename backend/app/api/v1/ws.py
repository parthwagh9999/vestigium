"""WebSocket API route for real-time graph collaboration."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from app.core.websocket import manager

router = APIRouter()


@router.websocket("/ws/investigation/{investigation_id}")
async def investigation_websocket(
    websocket: WebSocket,
    investigation_id: str,
) -> None:
    """WebSocket endpoint for real-time investigation collaboration.

    Supports the following message types:
    - node_added: A new entity was added to the graph
    - node_updated: An entity was modified (position, properties, etc.)
    - node_removed: An entity was deleted
    - edge_added: A new relationship was created
    - edge_removed: A relationship was deleted
    - cursor_move: User cursor position update for presence awareness
    - selection_change: User selection changed
    - lock_node: User locked a node for editing
    - unlock_node: User released a node lock
    """
    # Extract user info from query params (simplified — in production use JWT)
    user_id = websocket.query_params.get("user_id")
    username = websocket.query_params.get("username", "Anonymous")

    await manager.connect(websocket, investigation_id, user_id, username)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = message.get("type")

            if msg_type in (
                "node_added", "node_updated", "node_removed",
                "edge_added", "edge_removed",
                "cursor_move", "selection_change",
                "lock_node", "unlock_node",
            ):
                # Broadcast to other clients in the same investigation
                message["sender_id"] = user_id
                message["sender_username"] = username
                await manager.broadcast(investigation_id, message, exclude=websocket)
            elif msg_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            else:
                await manager.send_personal(
                    websocket,
                    {"type": "error", "message": f"Unknown message type: {msg_type}"},
                )
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
