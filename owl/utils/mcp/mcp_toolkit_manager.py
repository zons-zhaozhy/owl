import json
import os
from typing import List, Optional, AsyncGenerator

from camel.toolkits import MCPToolkit
from contextlib import AsyncExitStack, asynccontextmanager


class MCPToolkitManager:
    r"""MCPToolkitManager is a class for managing multiple MCPToolkit
    instances and providing unified connection management.

    Attributes:
        toolkits (List[MCPToolkit]): A list of MCPToolkit instances to be
            managed.
    """

    def __init__(self, toolkits: List[MCPToolkit]):
        self.toolkits = toolkits
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected = False


    @staticmethod
    def from_config(config_path: str) -> "MCPToolkitManager":
        r"""Loads an MCPToolkit instance from a JSON configuration file and
        returns an MCPToolkitManager instance.

        Args:
            config_path (str): The path to the JSON configuration file.

        Returns:
            MCPToolkitManager: The MCPToolkitManager instance.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_toolkits = []

        # "mcpServers" is the MCP server configuration running as stdio mode
        mcp_servers = data.get("mcpServers", {})
        for name, cfg in mcp_servers.items():
            toolkit = MCPToolkit(
                command_or_url=cfg["command"],
                args=cfg.get("args", []),
                env={**os.environ, **cfg.get("env", {})},
                timeout=cfg.get("timeout", None),
            )
            all_toolkits.append(toolkit)

        # "mcpWebServers" is the MCP server configuration running as sse mode
        mcp_web_servers = data.get("mcpWebServers", {})
        for name, cfg in mcp_web_servers.items():
            toolkit = MCPToolkit(
                command_or_url=cfg["url"],
                timeout=cfg.get("timeout", None),
            )
            all_toolkits.append(toolkit)

        return MCPToolkitManager(all_toolkits)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator["MCPToolkitManager", None]:
        r"""Connect multiple MCPToolkit instances and close them when
        leaving"""
        self._exit_stack = AsyncExitStack()
        try:
            for tk in self.toolkits:
                await self._exit_stack.enter_async_context(tk.connection())
            self._connected = True
            yield self
        finally:
            self._connected = False
            await self._exit_stack.aclose()
            self._exit_stack = None

    def is_connected(self) -> bool:
        r"""Returns whether the MCPToolkitManager is connected."""
        return self._connected

    def get_all_tools(self):
        r"""Returns all tools from all MCPToolkit instances."""
        all_tools = []
        for tk in self.toolkits:
            all_tools.extend(tk.get_tools())
        return all_tools