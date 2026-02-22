"""Clipboard tools for agents with approval gating."""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def read_clipboard() -> str:
    """Read the current contents of the system clipboard.

    AUTO tier - no approval needed.

    Returns:
        Clipboard contents or an error message.
    """
    try:
        if _approval_manager:
            await _approval_manager.request_approval(
                "clipboard_read", "Read clipboard contents", "agent"
            )

        import pyperclip

        content = pyperclip.paste()
        if not content:
            return "(clipboard is empty)"
        if len(content) > 50000:
            content = content[:50000] + "\n... [truncated]"
        return content
    except Exception as e:
        return f"Error reading clipboard: {e}"


@tool
async def write_clipboard(text: str) -> str:
    """Write text to the system clipboard (ASK tier, requires approval).

    Args:
        text: The text to copy to the clipboard.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            preview = text[:100] + ("..." if len(text) > 100 else "")
            approved = await _approval_manager.request_approval(
                "clipboard_write", f"Write to clipboard: {preview}", "agent"
            )
            if not approved:
                return "Denied: writing to clipboard was not approved."

        import pyperclip

        pyperclip.copy(text)
        return f"Copied {len(text)} characters to clipboard."
    except Exception as e:
        return f"Error writing to clipboard: {e}"
