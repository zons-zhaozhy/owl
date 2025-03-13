"""MCP Multi-Agent System Example

This example demonstrates how to use MCP (Model Context Protocol) with CAMEL agents
for advanced information retrieval and processing tasks.

Environment Setup:
1. Configure the required dependencies of owl library.

2. Go Environment (v1.23.2+):
   ```bash
   # Verify Go installation
   go version
   
   # Add Go binary path to PATH
   export PATH=$PATH:~/go/bin
   # Note: Add to ~/.bashrc or ~/.zshrc for persistence
   ```

3. Playwright Setup:
   ```bash
   # Install Node.js and npm first
   npm install -g @executeautomation/playwright-mcp-server
   npx playwright install-deps
   
   # Configure in mcp_servers_config.json:
   {
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["-y", "@executeautomation/playwright-mcp-server"]
       }
     }
   }
   ```

4. MCP Filesystem Server Setup:
   ```bash
   # Install MCP filesystem server
   go install github.com/mark3labs/mcp-filesystem-server@latest
   npm install -g @modelcontextprotocol/server-filesystem
   
   # Configure mcp_servers_config.json in owl/utils/mcp/
   {
     "mcpServers": {
       "filesystem": {
         "command": "mcp-filesystem-server",
         "args": [
           "/home/your_path",
           "/home/your_path"
         ],
         "type": "filesystem"
       }
     }
   }
   ```

Usage:
1. Ensure all MCP servers are properly configured in mcp_servers_config.json
2. Run this script to create a multi-agent system that can:
   - Access and manipulate files through MCP filesystem server
   - Perform web automation tasks using Playwright
   - Process and generate information using GPT-4o
3. The system will execute the specified task while maintaining security through
   relative paths and controlled access

Note:
- All file operations are restricted to configured directories
- System uses GPT-4o for both user and assistant roles
- Supports asynchronous operations for efficient processing
"""

import asyncio
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level
from camel.toolkits import MCPToolkit

from utils.enhanced_role_playing import OwlRolePlaying, run_society



load_dotenv()
set_log_level(level="DEBUG")


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    r"""build a multi-agent OwlRolePlaying instance.

    Args:
        question (str): The question to ask.
        tools (List[FunctionTool]): The MCP tools to use.
    """
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict={"temperature": 0},
        ),
    }

    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,
    }

    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


async def main():
    config_path = str(
        Path(__file__).parent / "utils/mcp/mcp_servers_config.json"
    )

    mcp_toolkit = MCPToolkit(config_path=config_path)

    question = (
        "I'd like a academic report about Guohao Li, including his research "
        "direction, published papers (At least 3), institutions, etc." 
        "Then organize the report in Markdown format and save it to my desktop"
    )

    await mcp_toolkit.connect()

    # # Connect to all MCP toolkits
    tools = [*mcp_toolkit.get_tools()]

    society = await construct_society(question, tools)

    answer, chat_history, token_count = await run_society(society)

    print(f"\033[94mAnswer: {answer}\033[0m")

    await mcp_toolkit.disconnect()

if __name__ == "__main__":
    asyncio.run(main())