"""JSONL audit logging for all agent actions."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only JSONL audit log for agent actions."""

    def __init__(self, log_dir: str | Path = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / "audit.jsonl"

    def log(
        self,
        action_type: str,
        action_detail: str,
        agent_name: str,
        tier: str,
        approved: bool,
        resolved_by: str = "auto",
        metadata: dict[str, Any] | None = None,
    ):
        """Write an audit entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "action_detail": action_detail[:2000],
            "agent_name": agent_name,
            "tier": tier,
            "approved": approved,
            "resolved_by": resolved_by,
        }
        if metadata:
            entry["metadata"] = metadata

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Read recent audit entries."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries[-limit:]
