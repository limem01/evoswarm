"""Telegram messaging channel using python-telegram-bot."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from backend.messaging.base import BaseChannel

logger = logging.getLogger(__name__)


class TelegramChannel(BaseChannel):
    """Telegram bot channel for EvoSwarm."""

    def __init__(self, token: str):
        super().__init__("telegram")
        self.token = token
        self.app: Application | None = None
        self._admin_chat_ids: set[int] = set()

    async def start(self):
        """Start the Telegram bot."""
        self.app = Application.builder().token(self.token).build()

        # Register handlers
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("approve", self._cmd_approve))
        self.app.add_handler(CommandHandler("deny", self._cmd_deny))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Telegram bot started")

    async def stop(self):
        """Stop the Telegram bot."""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    async def send_message(self, recipient: str, text: str):
        """Send message to a specific chat ID."""
        if self.app:
            await self.app.bot.send_message(chat_id=int(recipient), text=text)

    async def broadcast(self, text: str):
        """Broadcast to all known admin chats."""
        for chat_id in self._admin_chat_ids:
            try:
                await self.send_message(str(chat_id), text)
            except Exception as e:
                logger.error(f"Failed to send to {chat_id}: {e}")

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = update.effective_chat.id
        self._admin_chat_ids.add(chat_id)
        await update.message.reply_text(
            "EvoSwarm connected! Send me tasks or use /help for commands."
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if self._on_command:
            result = await self._on_command("/help", str(update.effective_user.id), [])
            await update.message.reply_text(result)

    async def _cmd_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /approve <id> command."""
        if context.args and self._on_command:
            result = await self._on_command("/approve", str(update.effective_user.id), context.args)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("Usage: /approve <request_id>")

    async def _cmd_deny(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deny <id> command."""
        if context.args and self._on_command:
            result = await self._on_command("/deny", str(update.effective_user.id), context.args)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("Usage: /deny <request_id>")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if self._on_command:
            result = await self._on_command("/status", str(update.effective_user.id), [])
            await update.message.reply_text(result)

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages as tasks."""
        chat_id = update.effective_chat.id
        self._admin_chat_ids.add(chat_id)

        if self._on_message:
            await update.message.reply_text("Processing your task...")
            result = await self._on_message(
                self.name,
                str(update.effective_user.id),
                update.message.text,
            )
            # Telegram has a 4096 char limit
            if len(result) > 4000:
                result = result[:4000] + "\n... [truncated]"
            await update.message.reply_text(result)
