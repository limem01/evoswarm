"""Application launching tools for agents with approval gating."""
from __future__ import annotations

import subprocess
from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def launch_app(app_path: str, args: str = "") -> str:
    """Launch an application (ASK tier, requires approval).

    Args:
        app_path: Path to the application executable.
        args: Optional command-line arguments.

    Returns:
        PID of launched process or an error message.
    """
    try:
        if _approval_manager:
            detail = f"Launch: {app_path}"
            if args:
                detail += f" {args}"
            approved = await _approval_manager.request_approval(
                "launch_app", detail, "agent"
            )
            if not approved:
                return f"Denied: launching '{app_path}' was not approved."

        cmd_parts = [app_path]
        if args:
            cmd_parts.extend(args.split())

        proc = subprocess.Popen(
            cmd_parts,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"Launched '{app_path}' with PID {proc.pid}"
    except FileNotFoundError:
        return f"Error: application not found: {app_path}"
    except PermissionError:
        return f"Error: permission denied launching: {app_path}"
    except Exception as e:
        return f"Error launching application: {e}"
