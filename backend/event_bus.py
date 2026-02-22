"""
Central event bus for broadcasting agent events to WebSocket clients.
"""
import json
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine


class EventType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_MESSAGE = "agent_message"
    AGENT_STATUS = "agent_status"
    HANDOFF = "handoff"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETE = "task_complete"
    EVOLUTION_ROUND_START = "evolution_round_start"
    EVOLUTION_ROUND_END = "evolution_round_end"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETE = "training_complete"
    MERGE_COMPLETE = "merge_complete"
    LINEAGE_UPDATE = "lineage_update"
    ERROR = "error"
    # New event types for PC control
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_RESOLVED = "approval_resolved"
    COMMAND_OUTPUT = "command_output"
    SCREENSHOT_CAPTURED = "screenshot_captured"


class EventBus:
    def __init__(self):
        self._broadcast_fn: Callable[[str], Coroutine] | None = None

    def set_broadcast_fn(self, fn: Callable[[str], Coroutine]):
        self._broadcast_fn = fn

    async def emit(self, event_type: EventType, data: dict[str, Any]):
        event = {
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        if self._broadcast_fn:
            await self._broadcast_fn(json.dumps(event))


# Global singleton instance
event_bus = EventBus()
