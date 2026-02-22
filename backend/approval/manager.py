"""ApprovalManager: orchestrates approval requests via WebSocket and REST."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Coroutine

from backend.approval.policy import ApprovalPolicy, ApprovalTier
from backend.approval.audit import AuditLogger


# Timeout for approval requests (5 minutes)
APPROVAL_TIMEOUT = 300


class ApprovalRequest:
    """A pending approval request."""

    def __init__(self, action_type: str, action_detail: str, agent_name: str, tier: ApprovalTier, category: str):
        self.id = str(uuid.uuid4())[:8]
        self.action_type = action_type
        self.action_detail = action_detail
        self.agent_name = agent_name
        self.tier = tier
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.future: asyncio.Future = asyncio.get_event_loop().create_future()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "action_detail": self.action_detail,
            "agent_name": self.agent_name,
            "tier": self.tier.value,
            "category": self.category,
            "created_at": self.created_at,
        }


class ApprovalManager:
    """Manages approval flow for agent actions.

    Integrates with WebSocket for real-time approval requests and
    supports REST-based resolution as well.
    """

    def __init__(self, policy_path: str | None = None, log_dir: str = "./logs"):
        self.policy = ApprovalPolicy(policy_path)
        self.audit = AuditLogger(log_dir)
        self.pending: dict[str, ApprovalRequest] = {}
        self._broadcast_fn: Callable[[str], Coroutine] | None = None

    def set_broadcast_fn(self, fn: Callable[[str], Coroutine]):
        """Set the WebSocket broadcast function for sending approval requests."""
        self._broadcast_fn = fn

    async def request_approval(
        self,
        action_type: str,
        action_detail: str,
        agent_name: str = "unknown",
    ) -> bool:
        """Request approval for an action. Returns True if approved.

        AUTO actions are approved immediately.
        BLOCK actions are denied immediately.
        ASK actions wait for user response via WebSocket/REST.
        """
        tier, category = self.policy.classify(action_type, action_detail)

        if tier == ApprovalTier.AUTO:
            self.audit.log(action_type, action_detail, agent_name, tier.value, True, "auto")
            return True

        if tier == ApprovalTier.BLOCK:
            self.audit.log(action_type, action_detail, agent_name, tier.value, False, "policy")
            return False

        # ASK tier - need user approval
        request = ApprovalRequest(action_type, action_detail, agent_name, tier, category)
        self.pending[request.id] = request

        # Broadcast approval request via WebSocket
        if self._broadcast_fn:
            import json
            await self._broadcast_fn(json.dumps({
                "event_type": "approval_required",
                "timestamp": request.created_at,
                "data": request.to_dict(),
            }))

        # Wait for resolution with timeout
        try:
            approved = await asyncio.wait_for(request.future, timeout=APPROVAL_TIMEOUT)
        except asyncio.TimeoutError:
            approved = False
            self.audit.log(action_type, action_detail, agent_name, tier.value, False, "timeout")
        finally:
            self.pending.pop(request.id, None)

        return approved

    def resolve(self, request_id: str, approved: bool, resolved_by: str = "user") -> bool:
        """Resolve a pending approval request.

        Returns True if the request was found and resolved.
        """
        request = self.pending.get(request_id)
        if not request:
            return False

        self.audit.log(
            request.action_type,
            request.action_detail,
            request.agent_name,
            request.tier.value,
            approved,
            resolved_by,
        )

        if not request.future.done():
            request.future.set_result(approved)

        return True

    def get_pending(self) -> list[dict[str, Any]]:
        """Get all pending approval requests."""
        return [r.to_dict() for r in self.pending.values()]

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent audit log entries."""
        return self.audit.get_recent(limit)
