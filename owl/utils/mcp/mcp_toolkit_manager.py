import json
import os
from typing import List, Optional, AsyncGenerator

from camel.toolkits import MCPToolkit
from contextlib import AsyncExitStack, asynccontextmanager


class MCPToolkitManager:
    """
    负责管理多个 MCPToolkit 实例，并提供统一的连接管理。
    """

    def __init__(self, toolkits: List[MCPToolkit]):
        self.toolkits = toolkits
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected = False


    @staticmethod
    def from_config(config_path: str) -> "MCPToolkitManager":
        """从 JSON 配置文件加载 MCPToolkit 实例，并返回 MCPToolkitManager 实例。

        :param config_path: JSON 配置文件路径
        :return: MCPToolkitManager 实例
        """
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_toolkits = []

        # 处理本地 MCP 服务器
        mcp_servers = data.get("mcpServers", {})
        for name, cfg in mcp_servers.items():
            toolkit = MCPToolkit(
                command_or_url=cfg["command"],
                args=cfg.get("args", []),
                env={**os.environ, **cfg.get("env", {})},
                timeout=cfg.get("timeout", None),
            )
            all_toolkits.append(toolkit)

        # 处理远程 MCP Web 服务器
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
        """统一打开多个 MCPToolkit 的连接，并在离开上下文时关闭。"""
        self._exit_stack = AsyncExitStack()
        try:
            # 顺序进入每个 toolkit 的 async context
            for tk in self.toolkits:
                await self._exit_stack.enter_async_context(tk.connection())
            self._connected = True
            yield self
        finally:
            self._connected = False
            await self._exit_stack.aclose()
            self._exit_stack = None

    def is_connected(self) -> bool:
        return self._connected

    def get_all_tools(self):
        """合并所有 MCPToolkit 提供的工具"""
        all_tools = []
        for tk in self.toolkits:
            all_tools.extend(tk.get_tools())
        return all_tools