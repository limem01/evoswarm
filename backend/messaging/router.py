"""MessageRouter: routes messages between channels and the swarm."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Callable, Coroutine

from backend.messaging.base import BaseChannel

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes incoming messages to the swarm and responses back to channels.

    Supports /approve <id> and /deny <id> commands from any channel.
    """

    def __init__(self):
        self.channels: dict[str, BaseChannel] = {}
        self._task_handler: Callable[[str], Coroutine] | None = None
        self._approval_handler: Callable[[str, bool, str], Coroutine] | None = None

    def set_task_handler(self, handler: Callable[[str], Coroutine]):
        """Set the handler for running tasks: (task_text) -> result_text."""
        self._task_handler = handler

    def set_approval_handler(self, handler: Callable[[str, bool, str], Coroutine]):
        """Set the handler for approval commands: (request_id, approved, resolved_by) -> None."""
        self._approval_handler = handler

    def register_channel(self, channel: BaseChannel):
        """Register a messaging channel."""
        channel.set_message_handler(self._handle_message)
        channel.set_command_handler(self._handle_command)
        self.channels[channel.name] = channel

    async def start_all(self):
        """Start all registered channels."""
        for name, channel in self.channels.items():
            try:
                await channel.start()
                logger.info(f"Started messaging channel: {name}")
            except Exception as e:
                logger.error(f"Failed to start channel {name}: {e}")

    async def stop_all(self):
        """Stop all channels."""
        for name, channel in self.channels.items():
            try:
                await channel.stop()
            except Exception as e:
                logger.error(f"Error stopping channel {name}: {e}")

    async def broadcast_to_all(self, text: str):
        """Broadcast a message to all channels."""
        for channel in self.channels.values():
            try:
                await channel.broadcast(text)
            except Exception as e:
                logger.error(f"Broadcast error on {channel.name}: {e}")

    async def _handle_message(self, channel_name: str, user_id: str, text: str) -> str:
        """Handle an incoming message from any channel."""
        text = text.strip()

        # Check for commands
        if text.startswith("/"):
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:]
            return await self._handle_command(command, user_id, args)

        # Route to task handler
        if self._task_handler:
            try:
                result = await self._task_handler(text)
                return result
            except Exception as e:
                return f"Error running task: {e}"

        return "No task handler configured."

    async def _handle_command(self, command: str, user_id: str, args: list[str]) -> str:
        """Handle /commands from messaging channels."""
        if command in ("/approve", "/yes", "/ok"):
            if not args:
                return "Usage: /approve <request_id>"
            if self._approval_handler:
                await self._approval_handler(args[0], True, f"messaging:{user_id}")
                return f"Approved request {args[0]}"
            return "Approval system not connected."

        if command in ("/deny", "/no", "/reject"):
            if not args:
                return "Usage: /deny <request_id>"
            if self._approval_handler:
                await self._approval_handler(args[0], False, f"messaging:{user_id}")
                return f"Denied request {args[0]}"
            return "Approval system not connected."

        if command == "/status":
            return f"EvoSwarm is running. {len(self.channels)} channel(s) active."

        if command == "/help":
            return (
                "EvoSwarm Commands:\n"
                "/approve <id> - Approve a pending action\n"
                "/deny <id> - Deny a pending action\n"
                "/status - Check system status\n"
                "Or just send a message to run it as a task."
            )

        return f"Unknown command: {command}. Try /help"


def create_router_from_env() -> MessageRouter:
    """Create a MessageRouter with channels configured from environment variables."""
    router = MessageRouter()

    # Telegram
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        try:
            from backend.messaging.telegram_bot import TelegramChannel
            channel = TelegramChannel(telegram_token)
            router.register_channel(channel)
            logger.info("Telegram channel registered")
        except ImportError:
            logger.warning("python-telegram-bot not installed, skipping Telegram")

    # Discord
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if discord_token:
        try:
            from backend.messaging.discord_bot import DiscordChannel
            channel = DiscordChannel(discord_token)
            router.register_channel(channel)
            logger.info("Discord channel registered")
        except ImportError:
            logger.warning("discord.py not installed, skipping Discord")

    # WhatsApp
    if os.getenv("WHATSAPP_ENABLED", "false").lower() == "true":
        try:
            from backend.messaging.whatsapp_bot import WhatsAppChannel
            channel = WhatsAppChannel()
            router.register_channel(channel)
            logger.info("WhatsApp channel registered")
        except ImportError:
            logger.warning("WhatsApp bridge not configured, skipping")

    return router
