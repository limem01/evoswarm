"""Three-tier approval policy: AUTO, ASK, BLOCK."""
from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any


class ApprovalTier(str, Enum):
    AUTO = "auto"
    ASK = "ask"
    BLOCK = "block"


# Default policy rules - loaded from JSON or hardcoded fallback
_DEFAULT_RULES: list[dict[str, Any]] = [
    # AUTO tier - safe read-only operations
    {"pattern": r"^(ls|dir|pwd|whoami|echo|hostname|date|uptime)(\s|$)", "tier": "auto", "category": "safe_read"},
    {"pattern": r"^cat\s", "tier": "auto", "category": "safe_read"},
    {"pattern": r"^type\s", "tier": "auto", "category": "safe_read"},
    {"pattern": r"^git\s+(status|log|diff|branch|remote|show|tag)", "tier": "auto", "category": "safe_git"},
    {"pattern": r"^systeminfo", "tier": "auto", "category": "safe_system"},
    {"pattern": r"^(tasklist|wmic\s+process)", "tier": "auto", "category": "safe_process"},
    {"pattern": r"^pip\s+(list|show|freeze)", "tier": "auto", "category": "safe_package"},
    {"pattern": r"^npm\s+(list|ls|outdated|info)", "tier": "auto", "category": "safe_package"},
    {"pattern": r"^node\s+--version", "tier": "auto", "category": "safe_read"},
    {"pattern": r"^python\s+--version", "tier": "auto", "category": "safe_read"},

    # BLOCK tier - dangerous/destructive operations
    {"pattern": r"rm\s+(-rf?|--recursive)\s+[/\\]", "tier": "block", "category": "destructive"},
    {"pattern": r"^format\s", "tier": "block", "category": "destructive"},
    {"pattern": r"^(shutdown|reboot|restart-computer)", "tier": "block", "category": "system_control"},
    {"pattern": r"^(del|rmdir)\s+/s\s+[A-Z]:\\(Windows|Program)", "tier": "block", "category": "destructive"},
    {"pattern": r"reg\s+(delete|add)\s+HKLM", "tier": "block", "category": "registry"},
    {"pattern": r"chmod\s+777\s+(/|C:\\Windows)", "tier": "block", "category": "permission_change"},
    {"pattern": r"^(mkfs|fdisk|diskpart)", "tier": "block", "category": "disk_operation"},
    {"pattern": r">\s*(NUL|/dev/null)\s*2>&1.*rm\s", "tier": "block", "category": "sneaky_delete"},
    {"pattern": r"^net\s+(user|localgroup)\s+.*\s+/add", "tier": "block", "category": "user_management"},

    # ASK tier - everything else that modifies state (default)
    {"pattern": r"^pip\s+install", "tier": "ask", "category": "package_install"},
    {"pattern": r"^npm\s+install", "tier": "ask", "category": "package_install"},
    {"pattern": r"^git\s+(commit|push|pull|merge|rebase|checkout|reset)", "tier": "ask", "category": "git_write"},
    {"pattern": r"^(mkdir|md)\s", "tier": "ask", "category": "filesystem"},
    {"pattern": r"^(cp|copy|mv|move|ren|rename)\s", "tier": "ask", "category": "filesystem"},
    {"pattern": r"^(rm|del|rmdir|rd)\s", "tier": "ask", "category": "filesystem"},
    {"pattern": r"^(kill|taskkill|Stop-Process)", "tier": "ask", "category": "process_control"},
    {"pattern": r"^start\s", "tier": "ask", "category": "app_launch"},
]


class ApprovalPolicy:
    """Determines approval tier for a given action."""

    def __init__(self, policy_path: str | Path | None = None):
        self.rules: list[dict[str, Any]] = []
        if policy_path and Path(policy_path).exists():
            with open(policy_path) as f:
                data = json.load(f)
                self.rules = data.get("rules", [])
        if not self.rules:
            self.rules = _DEFAULT_RULES
        # Compile regex patterns
        self._compiled = [
            (re.compile(r["pattern"], re.IGNORECASE), ApprovalTier(r["tier"]), r.get("category", "unknown"))
            for r in self.rules
        ]

    def classify(self, action_type: str, action_detail: str) -> tuple[ApprovalTier, str]:
        """Classify an action into an approval tier.

        Args:
            action_type: Type of action (e.g. 'shell', 'browser', 'file_write')
            action_detail: The specific command or action description

        Returns:
            Tuple of (ApprovalTier, category)
        """
        # Tool-level overrides
        if action_type == "screenshot":
            return ApprovalTier.ASK, "screen_capture"
        if action_type == "clipboard_read":
            return ApprovalTier.AUTO, "clipboard"
        if action_type == "clipboard_write":
            return ApprovalTier.ASK, "clipboard"
        if action_type == "system_info":
            return ApprovalTier.AUTO, "safe_system"
        if action_type == "list_processes":
            return ApprovalTier.AUTO, "safe_process"
        if action_type == "kill_process":
            return ApprovalTier.ASK, "process_control"
        if action_type == "browser_navigate":
            return ApprovalTier.ASK, "browser"
        if action_type == "browser_click":
            return ApprovalTier.ASK, "browser"
        if action_type == "browser_type":
            return ApprovalTier.ASK, "browser"
        if action_type == "browser_screenshot":
            return ApprovalTier.ASK, "browser"
        if action_type == "type_text":
            return ApprovalTier.ASK, "input"
        if action_type == "click_position":
            return ApprovalTier.ASK, "input"
        if action_type == "press_key":
            return ApprovalTier.ASK, "input"
        if action_type == "launch_app":
            return ApprovalTier.ASK, "app_launch"

        # Shell commands - match against regex rules
        if action_type in ("shell", "shell_background"):
            for regex, tier, category in self._compiled:
                if regex.search(action_detail):
                    return tier, category
            # Default: ASK for unrecognized shell commands
            return ApprovalTier.ASK, "unknown_command"

        # File operations
        if action_type == "file_write":
            return ApprovalTier.ASK, "file_write"
        if action_type == "file_read":
            return ApprovalTier.AUTO, "file_read"

        # Default: ASK for anything unclassified
        return ApprovalTier.ASK, "unclassified"
