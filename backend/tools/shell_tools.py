"""Shell execution tools for agents with approval gating."""
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None
_background_processes: dict[int, asyncio.subprocess.Process] = {}


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def execute_shell(command: str) -> str:
    """Execute a shell command and return its output.

    Args:
        command: The shell command to execute.

    Returns:
        stdout/stderr output or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "shell", f"Execute: {command}", "agent"
            )
            if not approved:
                return f"Denied: shell command '{command}' was not approved."

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        output_parts: list[str] = []
        if stdout:
            output_parts.append(stdout.decode(errors="replace"))
        if stderr:
            output_parts.append(f"[stderr] {stderr.decode(errors='replace')}")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        # Truncate very long output
        if len(output) > 50000:
            output = output[:50000] + "\n... [truncated]"

        return f"Exit code: {proc.returncode}\n{output}"
    except asyncio.TimeoutError:
        return f"Error: command timed out after 120 seconds: {command}"
    except Exception as e:
        return f"Error executing command: {e}"


@tool
async def execute_shell_background(command: str) -> str:
    """Execute a shell command in the background and return its PID.

    Args:
        command: The shell command to run in the background.

    Returns:
        The PID of the background process or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "shell_background", f"Background: {command}", "agent"
            )
            if not approved:
                return f"Denied: background command '{command}' was not approved."

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _background_processes[proc.pid] = proc
        return f"Background process started with PID {proc.pid}"
    except Exception as e:
        return f"Error starting background process: {e}"


@tool
async def get_process_output(pid: int) -> str:
    """Get the output of a background process by PID.

    Args:
        pid: Process ID of the background process.

    Returns:
        Process output or status information.
    """
    try:
        proc = _background_processes.get(pid)
        if proc is None:
            return f"Error: no tracked background process with PID {pid}"

        if proc.returncode is None:
            # Still running — try to read what's available without blocking
            return f"Process {pid} is still running."

        stdout, stderr = await proc.communicate()
        output_parts: list[str] = []
        if stdout:
            output_parts.append(stdout.decode(errors="replace"))
        if stderr:
            output_parts.append(f"[stderr] {stderr.decode(errors='replace')}")

        output = "\n".join(output_parts) if output_parts else "(no output)"
        if len(output) > 50000:
            output = output[:50000] + "\n... [truncated]"

        # Clean up
        del _background_processes[pid]
        return f"Process {pid} finished (exit {proc.returncode}):\n{output}"
    except Exception as e:
        return f"Error getting process output: {e}"
