"""Browser automation tools for agents using Playwright, with approval gating."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

_approval_manager: Any = None
_browser: Any = None
_page: Any = None


def set_approval_manager(manager: Any) -> None:
    """Set the approval manager instance for this module."""
    global _approval_manager
    _approval_manager = manager


async def _ensure_browser():
    """Lazily initialize the Playwright browser and page."""
    global _browser, _page
    if _page is not None:
        return

    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    _browser = await pw.chromium.launch(headless=False)
    _page = await _browser.new_page()


@tool
async def browser_navigate(url: str) -> str:
    """Navigate the browser to a URL.

    Args:
        url: The URL to navigate to.

    Returns:
        Page title and URL, or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_navigate", f"Navigate to: {url}", "agent"
            )
            if not approved:
                return f"Denied: navigation to '{url}' was not approved."

        await _ensure_browser()
        await _page.goto(url, wait_until="domcontentloaded", timeout=30000)
        title = await _page.title()
        return f"Navigated to: {_page.url}\nTitle: {title}"
    except Exception as e:
        return f"Error navigating to {url}: {e}"


@tool
async def browser_click(selector: str) -> str:
    """Click an element on the page by CSS selector.

    Args:
        selector: CSS selector for the element to click.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_click", f"Click: {selector}", "agent"
            )
            if not approved:
                return f"Denied: click on '{selector}' was not approved."

        await _ensure_browser()
        await _page.click(selector, timeout=10000)
        return f"Clicked element: {selector}"
    except Exception as e:
        return f"Error clicking '{selector}': {e}"


@tool
async def browser_type(selector: str, text: str) -> str:
    """Type text into an element on the page.

    Args:
        selector: CSS selector for the input element.
        text: The text to type.

    Returns:
        Success or error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_type", f"Type into '{selector}': {text[:100]}", "agent"
            )
            if not approved:
                return f"Denied: typing into '{selector}' was not approved."

        await _ensure_browser()
        await _page.fill(selector, text, timeout=10000)
        return f"Typed {len(text)} characters into: {selector}"
    except Exception as e:
        return f"Error typing into '{selector}': {e}"


@tool
async def browser_screenshot(filename: str = "screenshot.png") -> str:
    """Take a screenshot of the current page.

    Args:
        filename: Name of the file to save the screenshot as.

    Returns:
        Path to the saved screenshot or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_screenshot", f"Screenshot: {filename}", "agent"
            )
            if not approved:
                return f"Denied: browser screenshot was not approved."

        await _ensure_browser()
        import os
        os.makedirs("logs", exist_ok=True)
        path = os.path.join("logs", filename)
        await _page.screenshot(path=path, full_page=True)
        return f"Screenshot saved to: {path}"
    except Exception as e:
        return f"Error taking screenshot: {e}"


@tool
async def browser_extract_text() -> str:
    """Extract all visible text from the current page.

    Returns:
        The visible text content of the page or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_extract_text", "Extract text from current page", "agent"
            )
            if not approved:
                return "Denied: text extraction was not approved."

        await _ensure_browser()
        text = await _page.inner_text("body")
        if len(text) > 50000:
            text = text[:50000] + "\n... [truncated]"
        return text if text.strip() else "(page has no visible text)"
    except Exception as e:
        return f"Error extracting text: {e}"


@tool
async def browser_get_links() -> str:
    """Get all links (anchor tags) from the current page.

    Returns:
        JSON list of links with href and text, or an error message.
    """
    try:
        if _approval_manager:
            approved = await _approval_manager.request_approval(
                "browser_get_links", "Get links from current page", "agent"
            )
            if not approved:
                return "Denied: getting links was not approved."

        await _ensure_browser()
        links = await _page.eval_on_selector_all(
            "a[href]",
            """elements => elements.map(el => ({
                href: el.href,
                text: el.innerText.trim().substring(0, 200)
            }))""",
        )
        if not links:
            return "No links found on the page."

        # Limit output size
        if len(links) > 200:
            links = links[:200]

        return json.dumps(links, indent=2)
    except Exception as e:
        return f"Error getting links: {e}"
