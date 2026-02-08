"""
Real-time collaborative editing system for workflows
Uses WebSockets and Operational Transformation for conflict-free editing
"""
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class OperationType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    CONNECT = "connect"
    DISCONNECT = "disconnect"


@dataclass
class Operation:
    """Single operation in the workflow"""
    id: str
    type: OperationType
    path: str  # JSON path to the target
    value: Any = None
    old_value: Any = None
    timestamp: float = field(default_factory=time.time)
    user_id: str = ""
    revision: int = 0


@dataclass
class Cursor:
    """User cursor position"""
    user_id: str
    user_name: str
    user_color: str
    node_id: Optional[str] = None
    x: float = 0
    y: float = 0
    last_update: float = field(default_factory=time.time)


class OTEngine:
    """
    Operational Transformation Engine
    Handles concurrent edits without conflicts
    """

    def __init__(self):
        self.operations: List[Operation] = []
        self.revision = 0
        self._transform_cache: Dict[tuple, Operation] = {}

    def apply_operation(self, op: Operation) -> Operation:
        """Apply an operation and increment revision"""
        self.revision += 1
        op.revision = self.revision
        self.operations.append(op)
        return op

    def transform(self, op1: Operation, op2: Operation) -> Operation:
        """
        Transform op1 against op2
        Returns modified op1 that accounts for op2
        """
        cache_key = (op1.id, op2.id)
        if cache_key in self._transform_cache:
            return self._transform_cache[cache_key]

        # Simplified OT - in production use proper OT algorithms
        transformed = Operation(
            id=op1.id,
            type=op1.type,
            path=op1.path,
            value=op1.value,
            old_value=op1.old_value,
            timestamp=op1.timestamp,
            user_id=op1.user_id,
            revision=op1.revision
        )

        # Handle path conflicts
        if op1.path == op2.path:
            if op1.timestamp < op2.timestamp:
                # op1 happened first, keep it
                pass
            else:
                # op2 happened first, adjust op1
                transformed.value = op2.value

        self._transform_cache[cache_key] = transformed
        return transformed

    def get_operations_since(self, revision: int) -> List[Operation]:
        """Get all operations after a specific revision"""
        return [op for op in self.operations if op.revision > revision]


class CollaborationRoom:
    """A room where multiple users collaborate on a workflow"""

    def __init__(self, room_id: str, workflow_id: str):
        self.room_id = room_id
        self.workflow_id = workflow_id
        self.ot_engine = OTEngine()
        self.users: Dict[str, 'CollaborationClient'] = {}
        self.cursors: Dict[str, Cursor] = {}
        self.chat_history: List[Dict[str, Any]] = []
        self.created_at = time.time()
        self.last_activity = time.time()

    def join(self, client: 'CollaborationClient') -> bool:
        """Add a user to the room"""
        if client.user_id not in self.users:
            self.users[client.user_id] = client
            self.broadcast_user_joined(client)
            return True
        return False

    def leave(self, user_id: str) -> bool:
        """Remove a user from the room"""
        if user_id in self.users:
            del self.users[user_id]
            if user_id in self.cursors:
                del self.cursors[user_id]
            self.broadcast_user_left(user_id)
            return True
        return False

    def apply_operation(self, op: Operation, user_id: str) -> Operation:
        """Apply an operation from a user"""
        op.user_id = user_id

        # Transform against concurrent operations
        for existing_op in self.ot_engine.get_operations_since(op.revision):
            if existing_op.user_id != user_id:
                op = self.ot_engine.transform(op, existing_op)

        # Apply the operation
        applied_op = self.ot_engine.apply_operation(op)

        # Broadcast to all users
        self.broadcast_operation(applied_op)

        self.last_activity = time.time()
        return applied_op

    def update_cursor(self, cursor: Cursor):
        """Update user's cursor position"""
        self.cursors[cursor.user_id] = cursor
        self.broadcast_cursor_update(cursor)

    def add_chat_message(self, user_id: str, user_name: str, message: str):
        """Add a chat message"""
        chat_msg = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_name": user_name,
            "message": message,
            "timestamp": time.time()
        }
        self.chat_history.append(chat_msg)

        # Keep only last 100 messages
        if len(self.chat_history) > 100:
            self.chat_history = self.chat_history[-100:]

        self.broadcast_chat_message(chat_msg)

    def broadcast_operation(self, op: Operation):
        """Send operation to all connected users"""
        message = {
            "type": "operation",
            "data": {
                "id": op.id,
                "type": op.type.value,
                "path": op.path,
                "value": op.value,
                "user_id": op.user_id,
                "revision": op.revision,
                "timestamp": op.timestamp
            }
        }
        self._broadcast(message)

    def broadcast_cursor_update(self, cursor: Cursor):
        """Broadcast cursor position"""
        message = {
            "type": "cursor_update",
            "data": {
                "user_id": cursor.user_id,
                "user_name": cursor.user_name,
                "user_color": cursor.user_color,
                "node_id": cursor.node_id,
                "x": cursor.x,
                "y": cursor.y
            }
        }
        self._broadcast(message, exclude=cursor.user_id)

    def broadcast_user_joined(self, client: 'CollaborationClient'):
        """Notify users of new participant"""
        message = {
            "type": "user_joined",
            "data": {
                "user_id": client.user_id,
                "user_name": client.user_name,
                "user_color": client.user_color
            }
        }
        self._broadcast(message, exclude=client.user_id)

    def broadcast_user_left(self, user_id: str):
        """Notify users of participant leaving"""
        message = {
            "type": "user_left",
            "data": {"user_id": user_id}
        }
        self._broadcast(message)

    def broadcast_chat_message(self, chat_msg: Dict[str, Any]):
        """Broadcast chat message"""
        message = {
            "type": "chat_message",
            "data": chat_msg
        }
        self._broadcast(message)

    def _broadcast(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """Send message to all connected clients"""
        for user_id, client in self.users.items():
            if user_id != exclude:
                try:
                    client.send(message)
                except Exception:
                    pass

    def get_room_state(self) -> Dict[str, Any]:
        """Get current room state for new users"""
        return {
            "room_id": self.room_id,
            "workflow_id": self.workflow_id,
            "revision": self.ot_engine.revision,
            "users": [
                {
                    "user_id": c.user_id,
                    "user_name": c.user_name,
                    "user_color": c.user_color
                }
                for c in self.users.values()
            ],
            "cursors": [
                {
                    "user_id": c.user_id,
                    "x": c.x,
                    "y": c.y,
                    "node_id": c.node_id
                }
                for c in self.cursors.values()
            ],
            "chat_history": self.chat_history[-20:]  # Last 20 messages
        }


class CollaborationClient:
    """A client connected to a collaboration room"""

    USER_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
        "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
    ]

    def __init__(self, user_id: str, user_name: str, room: CollaborationRoom):
        self.user_id = user_id
        self.user_name = user_name
        self.user_color = self._assign_color(room)
        self.room = room
        self._message_handler: Optional[Callable[[Dict[str, Any]], None]] = None

    def _assign_color(self, room: CollaborationRoom) -> str:
        """Assign a unique color to the user"""
        used_colors = {c.user_color for c in room.users.values()}
        for color in self.USER_COLORS:
            if color not in used_colors:
                return color
        return self.USER_COLORS[0]

    def on_message(self, handler: Callable[[Dict[str, Any]], None]):
        """Set message handler"""
        self._message_handler = handler

    def send(self, message: Dict[str, Any]):
        """Send message to client"""
        if self._message_handler:
            self._message_handler(message)

    def handle_operation(self, data: Dict[str, Any]):
        """Handle incoming operation from client"""
        op = Operation(
            id=data.get("id", str(uuid.uuid4())),
            type=OperationType(data.get("type", "update")),
            path=data.get("path", ""),
            value=data.get("value"),
            old_value=data.get("old_value"),
            user_id=self.user_id,
            revision=data.get("revision", 0)
        )
        self.room.apply_operation(op, self.user_id)

    def handle_cursor_update(self, data: Dict[str, Any]):
        """Handle cursor position update"""
        cursor = Cursor(
            user_id=self.user_id,
            user_name=self.user_name,
            user_color=self.user_color,
            node_id=data.get("node_id"),
            x=data.get("x", 0),
            y=data.get("y", 0)
        )
        self.room.update_cursor(cursor)

    def handle_chat_message(self, data: Dict[str, Any]):
        """Handle chat message"""
        self.room.add_chat_message(
            self.user_id,
            self.user_name,
            data.get("message", "")
        )


class CollaborationManager:
    """Manages all collaboration rooms"""

    def __init__(self):
        self.rooms: Dict[str, CollaborationRoom] = {}
        self.user_rooms: Dict[str, str] = {}  # user_id -> room_id
        self._cleanup_task: Optional[asyncio.Task] = None

    def get_or_create_room(self, workflow_id: str) -> CollaborationRoom:
        """Get existing room or create new one"""
        room_id = f"room_{workflow_id}"

        if room_id not in self.rooms:
            self.rooms[room_id] = CollaborationRoom(room_id, workflow_id)

        return self.rooms[room_id]

    def join_room(self, workflow_id: str, user_id: str, user_name: str) -> tuple[CollaborationRoom, CollaborationClient]:
        """Join a collaboration room"""
        room = self.get_or_create_room(workflow_id)

        # Leave previous room if any
        if user_id in self.user_rooms:
            old_room_id = self.user_rooms[user_id]
            if old_room_id in self.rooms:
                self.rooms[old_room_id].leave(user_id)

        # Create client and join
        client = CollaborationClient(user_id, user_name, room)
        room.join(client)

        self.user_rooms[user_id] = room.room_id

        return room, client

    def leave_room(self, user_id: str):
        """Leave current room"""
        if user_id in self.user_rooms:
            room_id = self.user_rooms[user_id]
            if room_id in self.rooms:
                self.rooms[room_id].leave(user_id)
            del self.user_rooms[user_id]

    def get_room(self, room_id: str) -> Optional[CollaborationRoom]:
        """Get room by ID"""
        return self.rooms.get(room_id)

    def list_rooms(self) -> List[Dict[str, Any]]:
        """List all active rooms"""
        return [
            {
                "room_id": room.room_id,
                "workflow_id": room.workflow_id,
                "user_count": len(room.users),
                "created_at": room.created_at,
                "last_activity": room.last_activity
            }
            for room in self.rooms.values()
        ]

    async def start_cleanup_task(self, max_idle_seconds: float = 3600):
        """Start background task to clean up idle rooms"""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes
            await self._cleanup_idle_rooms(max_idle_seconds)

    async def _cleanup_idle_rooms(self, max_idle_seconds: float):
        """Remove rooms that have been idle for too long"""
        current_time = time.time()
        rooms_to_remove = []

        for room_id, room in self.rooms.items():
            if current_time - room.last_activity > max_idle_seconds:
                rooms_to_remove.append(room_id)

        for room_id in rooms_to_remove:
            room = self.rooms[room_id]
            # Kick all users
            for user_id in list(room.users.keys()):
                room.leave(user_id)
                if user_id in self.user_rooms:
                    del self.user_rooms[user_id]

            del self.rooms[room_id]
            print(f"Cleaned up idle room: {room_id}")


# Global collaboration manager
collaboration_manager = CollaborationManager()
