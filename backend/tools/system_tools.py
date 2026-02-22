"""System information tools for agents (AUTO tier, no approval needed)."""
from __future__ import annotations

import platform
from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def system_info() -> str:
    """Get detailed system information (OS, hardware, resources).

    AUTO tier - no approval needed.

    Returns:
        Formatted system info string or an error message.
    """
    try:
        if _approval_manager:
            await _approval_manager.request_approval(
                "system_info", "Gather system information", "agent"
            )

        import psutil

        uname = platform.uname()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        lines = [
            "=== System Information ===",
            f"OS:         {uname.system} {uname.release} ({uname.version})",
            f"Machine:    {uname.machine}",
            f"Hostname:   {uname.node}",
            f"Processor:  {uname.processor}",
            f"Python:     {platform.python_version()}",
            "",
            "=== CPU ===",
            f"Cores:      {cpu_physical} physical, {cpu_count} logical",
            f"Usage:      {cpu_percent}%",
            "",
            "=== Memory ===",
            f"Total:      {mem.total / (1024**3):.1f} GB",
            f"Used:       {mem.used / (1024**3):.1f} GB ({mem.percent}%)",
            f"Available:  {mem.available / (1024**3):.1f} GB",
            "",
            "=== Disk ===",
            f"Total:      {disk.total / (1024**3):.1f} GB",
            f"Used:       {disk.used / (1024**3):.1f} GB ({disk.percent}%)",
            f"Free:       {disk.free / (1024**3):.1f} GB",
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting system info: {e}"
