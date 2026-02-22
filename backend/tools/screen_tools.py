"""Screen capture tools for agents with approval gating."""
from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def take_screenshot(filename: str = "screenshot.png") -> str:
    """Take a screenshot of the entire screen.

    Args:
        filename: Name of the file to save the screenshot as.

    Returns:
        Path to the saved screenshot or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "screenshot", f"Take screenshot: {filename}", "agent"
            )
            if not approved:
                return "Denied: screenshot was not approved."

        import pyautogui

        os.makedirs("logs", exist_ok=True)
        path = os.path.join("logs", filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        width, height = screenshot.size
        return f"Screenshot saved to: {path} ({width}x{height})"
    except Exception as e:
        return f"Error taking screenshot: {e}"
