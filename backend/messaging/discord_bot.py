"""Discord messaging channel using discord.py."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord
from discord.ext import commands

from backend.messaging.base import BaseChannel

logger = logging.getLogger(__name__)


class DiscordChannel(BaseChannel):
    """Discord bot channel for EvoSwarm."""

    def __init__(self, token: str):
        super().__init__("discord")
        self.token = token
        self._admin_channel_ids: set[int] = set()

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="/", intents=intents)

        self._setup_handlers()

    def _setup_handlers(self):
        """Register Discord event handlers."""

        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot connected as {self.bot.user}")

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author == self.bot.user:
                return

            text = message.content.strip()
            self._admin_channel_ids.add(message.channel.id)

            # Handle commands
            if text.startswith("/"):
                parts = text.split()
                command = parts[0].lower()
                args = parts[1:]

                if command in ("/approve", "/deny", "/status", "/help"):
                    if self._on_command:
                        result = await self._on_command(command, str(message.author.id), args)
                        await message.channel.send(result)
                    return

            # Handle as task
            if self._on_message:
                await message.channel.send("Processing your task...")
                result = await self._on_message(
                    self.name,
                    str(message.author.id),
                    text,
                )
                # Discord has a 2000 char limit
                if len(result) > 1900:
                    result = result[:1900] + "\n... [truncated]"
                await message.channel.send(result)

    async def start(self):
        """Start the Discord bot in background."""
        asyncio.create_task(self.bot.start(self.token))
        logger.info("Discord bot starting...")

    async def stop(self):
        """Stop the Discord bot."""
        await self.bot.close()

    async def send_message(self, recipient: str, text: str):
        """Send message to a specific channel ID."""
        channel = self.bot.get_channel(int(recipient))
        if channel:
            if len(text) > 1900:
                text = text[:1900] + "\n... [truncated]"
            await channel.send(text)

    async def broadcast(self, text: str):
        """Broadcast to all known admin channels."""
        for channel_id in self._admin_channel_ids:
            try:
                await self.send_message(str(channel_id), text)
            except Exception as e:
                logger.error(f"Failed to send to Discord channel {channel_id}: {e}")
