"""Process management tools for agents with approval gating."""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def list_processes(filter_name: str = "") -> str:
    """List running processes, optionally filtered by name.

    This is an AUTO-tier action (no approval required).

    Args:
        filter_name: Optional substring to filter process names.

    Returns:
        Formatted process list or an error message.
    """
    try:
        if _approval_manager:
            await _approval_manager.request_approval(
                "list_processes",
                f"List processes (filter: '{filter_name}')" if filter_name else "List all processes",
                "agent",
            )
            # AUTO tier: proceeds regardless; BLOCK would deny

        import psutil

        processes: list[str] = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = proc.info
                name = info.get("name", "")
                if filter_name and filter_name.lower() not in name.lower():
                    continue

                mem = info.get("memory_info")
                mem_mb = f"{mem.rss / (1024 * 1024):.1f}MB" if mem else "N/A"
                cpu = info.get("cpu_percent", 0)
                processes.append(f"PID {info['pid']:>6}  {name:<30}  CPU: {cpu:>5.1f}%  MEM: {mem_mb}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not processes:
            return "No matching processes found."

        # Sort by PID and limit output
        header = f"{'PID':>9}  {'Name':<30}  {'CPU':>8}  {'MEM':>10}"
        output = header + "\n" + "-" * 65 + "\n" + "\n".join(processes[:100])
        if len(processes) > 100:
            output += f"\n... and {len(processes) - 100} more"

        return output
    except Exception as e:
        return f"Error listing processes: {e}"


@tool
async def kill_process(pid: int) -> str:
    """Kill a process by PID (ASK-tier, requires approval).

    Args:
        pid: Process ID to terminate.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "kill_process", f"Kill process PID {pid}", "agent"
            )
            if not approved:
                return f"Denied: killing process {pid} was not approved."

        import psutil

        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.terminate()

        # Wait up to 5 seconds for graceful termination
        try:
            proc.wait(timeout=5)
            return f"Process {pid} ({proc_name}) terminated successfully."
        except psutil.TimeoutExpired:
            proc.kill()
            return f"Process {pid} ({proc_name}) force-killed after timeout."
    except psutil.NoSuchProcess:
        return f"Error: no process with PID {pid} found."
    except psutil.AccessDenied:
        return f"Error: access denied when trying to kill PID {pid}."
    except Exception as e:
        return f"Error killing process {pid}: {e}"


@tool
async def get_system_info() -> str:
    """Get basic system resource information (CPU, memory, disk).

    Returns:
        Formatted system information or an error message.
    """
    try:
        import psutil

        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return (
            f"CPU: {cpu_count} cores, {cpu_percent:.1f}% usage\n"
            f"Memory: {mem.used / (1024**3):.1f}GB / {mem.total / (1024**3):.1f}GB "
            f"({mem.percent}% used)\n"
            f"Disk: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB "
            f"({disk.percent}% used)"
        )
    except Exception as e:
        return f"Error getting system info: {e}"
