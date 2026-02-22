"""Keyboard and mouse input tools for agents with approval gating."""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


@tool
async def type_text(text: str) -> str:
    """Type text using the keyboard (simulates keypresses).

    Args:
        text: The text to type.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            preview = text[:100] + ("..." if len(text) > 100 else "")
            approved = await _approval_manager.request_approval(
                "type_text", f"Type: {preview}", "agent"
            )
            if not approved:
                return "Denied: typing was not approved."

        import pyautogui

        pyautogui.typewrite(text, interval=0.02)
        return f"Typed {len(text)} characters."
    except Exception as e:
        return f"Error typing text: {e}"


@tool
async def click_position(x: int, y: int) -> str:
    """Click the mouse at a specific screen position.

    Args:
        x: X coordinate on screen.
        y: Y coordinate on screen.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "click_position", f"Click at ({x}, {y})", "agent"
            )
            if not approved:
                return f"Denied: click at ({x}, {y}) was not approved."

        import pyautogui

        pyautogui.click(x, y)
        return f"Clicked at position ({x}, {y})."
    except Exception as e:
        return f"Error clicking at ({x}, {y}): {e}"


@tool
async def press_key(key: str) -> str:
    """Press a keyboard key or key combination (e.g. 'enter', 'ctrl+c').

    Args:
        key: Key name or combination to press (e.g. 'enter', 'tab', 'ctrl+s').

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "press_key", f"Press key: {key}", "agent"
            )
            if not approved:
                return f"Denied: pressing '{key}' was not approved."

        import pyautogui

        # Handle key combinations like 'ctrl+c'
        if "+" in key:
            keys = [k.strip() for k in key.split("+")]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)

        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {e}"
