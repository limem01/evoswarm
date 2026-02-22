"""WhatsApp messaging channel via Node.js Baileys bridge."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx

from backend.messaging.base import BaseChannel

logger = logging.getLogger(__name__)

# The WhatsApp bridge runs as a separate Node.js process using Baileys
# It exposes a simple HTTP API for sending/receiving messages
BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001")


class WhatsAppChannel(BaseChannel):
    """WhatsApp channel via Baileys Node.js bridge.

    Requires the whatsapp-bridge/ Node.js service to be running.
    The bridge handles the WhatsApp Web connection and exposes:
      POST /send  {to: "number@s.whatsapp.net", text: "..."}
      GET  /status
      Webhooks incoming messages to our callback URL.
    """

    def __init__(self):
        super().__init__("whatsapp")
        self.bridge_url = BRIDGE_URL
        self._admin_numbers: set[str] = set()
        self._poll_task: asyncio.Task | None = None

    async def start(self):
        """Start polling the bridge for incoming messages."""
        # Verify bridge is running
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.bridge_url}/status")
                if resp.status_code != 200:
                    logger.warning("WhatsApp bridge not responding")
                    return
        except Exception as e:
            logger.warning(f"WhatsApp bridge unavailable: {e}")
            return

        self._poll_task = asyncio.create_task(self._poll_messages())
        logger.info("WhatsApp channel started (polling mode)")

    async def stop(self):
        """Stop polling."""
        if self._poll_task:
            self._poll_task.cancel()

    async def send_message(self, recipient: str, text: str):
        """Send a WhatsApp message via the bridge."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.bridge_url}/send",
                    json={"to": recipient, "text": text},
                )
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")

    async def broadcast(self, text: str):
        """Broadcast to all known admin numbers."""
        for number in self._admin_numbers:
            await self.send_message(number, text)

    async def _poll_messages(self):
        """Poll the bridge for new incoming messages."""
        while True:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(f"{self.bridge_url}/messages")
                    if resp.status_code == 200:
                        messages = resp.json().get("messages", [])
                        for msg in messages:
                            sender = msg.get("from", "")
                            text = msg.get("text", "")
                            self._admin_numbers.add(sender)

                            if self._on_message and text:
                                result = await self._on_message(
                                    self.name, sender, text
                                )
                                await self.send_message(sender, result)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WhatsApp poll error: {e}")

            await asyncio.sleep(2)
