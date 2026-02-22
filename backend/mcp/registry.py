"""MCP server registry: connect to MCP servers and convert tools to LangChain format."""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import httpx
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """Represents a connection to a single MCP server."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self.url = config.get("url", "")  # For HTTP-based servers
        self.tools: list[dict[str, Any]] = []
        self.connected = False

    async def connect(self) -> bool:
        """Connect to the MCP server and discover tools."""
        if self.url:
            return await self._connect_http()
        return await self._connect_stdio()

    async def _connect_http(self) -> bool:
        """Connect via HTTP transport."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.url,
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.tools = data.get("result", {}).get("tools", [])
                    self.connected = True
                    logger.info(f"MCP server '{self.name}' connected: {len(self.tools)} tools")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.name}': {e}")
        return False

    async def _connect_stdio(self) -> bool:
        """Connect via stdio transport (spawn process)."""
        try:
            cmd = [self.command] + self.args
            # Send tools/list request
            request = json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}) + "\n"

            proc = subprocess.run(
                cmd,
                input=request,
                capture_output=True,
                text=True,
                timeout=15,
                env={**dict(__import__("os").environ), **self.env},
            )

            if proc.stdout:
                for line in proc.stdout.strip().split("\n"):
                    try:
                        data = json.loads(line)
                        if "result" in data and "tools" in data["result"]:
                            self.tools = data["result"]["tools"]
                            self.connected = True
                            logger.info(f"MCP server '{self.name}' connected: {len(self.tools)} tools")
                            return True
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.name}': {e}")
        return False

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": 2,
        }

        if self.url:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(self.url, json=request)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data.get("result", {}).get("content", [])
                        return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
            except Exception as e:
                return f"MCP tool call error: {e}"

        # stdio transport
        try:
            cmd = [self.command] + self.args
            proc = subprocess.run(
                cmd,
                input=json.dumps(request) + "\n",
                capture_output=True,
                text=True,
                timeout=60,
                env={**dict(__import__("os").environ), **self.env},
            )
            if proc.stdout:
                for line in proc.stdout.strip().split("\n"):
                    try:
                        data = json.loads(line)
                        if "result" in data:
                            content = data["result"].get("content", [])
                            return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return f"MCP tool call error: {e}"

        return "No response from MCP server"


class MCPRegistry:
    """Registry for MCP server connections."""

    def __init__(self, config_path: str | Path = "mcp_servers.json"):
        self.config_path = Path(config_path)
        self.servers: dict[str, MCPServerConnection] = {}

    async def load_config(self):
        """Load MCP server configurations from JSON file."""
        if not self.config_path.exists():
            logger.info("No mcp_servers.json found, MCP support disabled")
            return

        with open(self.config_path) as f:
            config = json.load(f)

        for name, server_config in config.get("servers", {}).items():
            self.servers[name] = MCPServerConnection(name, server_config)

    async def connect_all(self):
        """Connect to all configured MCP servers."""
        for name, server in self.servers.items():
            await server.connect()

    async def connect_server(self, name: str) -> bool:
        """Connect to a specific server."""
        server = self.servers.get(name)
        if not server:
            return False
        return await server.connect()

    def get_langchain_tools(self) -> list[StructuredTool]:
        """Convert all MCP tools to LangChain StructuredTool format."""
        lc_tools = []

        for server in self.servers.values():
            if not server.connected:
                continue

            for tool_def in server.tools:
                tool_name = tool_def.get("name", "unknown")
                description = tool_def.get("description", "MCP tool")
                schema = tool_def.get("inputSchema", {})

                # Create a closure to capture server and tool_name
                def _make_fn(srv: MCPServerConnection, tn: str):
                    async def _call(**kwargs) -> str:
                        return await srv.call_tool(tn, kwargs)
                    return _call

                lc_tool = StructuredTool.from_function(
                    coroutine=_make_fn(server, tool_name),
                    name=f"mcp_{server.name}_{tool_name}",
                    description=f"[MCP:{server.name}] {description}",
                )
                lc_tools.append(lc_tool)

        return lc_tools

    def get_server_status(self) -> list[dict[str, Any]]:
        """Get status of all servers."""
        return [
            {
                "name": s.name,
                "connected": s.connected,
                "tool_count": len(s.tools),
                "tools": [t.get("name") for t in s.tools],
            }
            for s in self.servers.values()
        ]
