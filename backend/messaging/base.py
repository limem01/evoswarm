"""Base channel interface for messaging integrations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine


class BaseChannel(ABC):
    """Abstract base class for messaging channels."""

    def __init__(self, name: str):
        self.name = name
        self._on_message: Callable[[str, str, str], Coroutine] | None = None
        self._on_command: Callable[[str, str, list[str]], Coroutine] | None = None

    def set_message_handler(self, handler: Callable[[str, str, str], Coroutine]):
        """Set handler for incoming messages: (channel, user_id, text) -> response."""
        self._on_message = handler

    def set_command_handler(self, handler: Callable[[str, str, list[str]], Coroutine]):
        """Set handler for commands: (command, user_id, args) -> response."""
        self._on_command = handler

    @abstractmethod
    async def start(self):
        """Start the channel (connect, start polling, etc.)."""
        ...

    @abstractmethod
    async def stop(self):
        """Stop the channel gracefully."""
        ...

    @abstractmethod
    async def send_message(self, recipient: str, text: str):
        """Send a message to a specific user/channel."""
        ...

    @abstractmethod
    async def broadcast(self, text: str):
        """Broadcast a message to all configured recipients."""
        ...
