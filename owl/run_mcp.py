# run_mcp.py

import asyncio
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import MCPToolkit, FunctionTool
from camel.types import ModelPlatformType, ModelType
from camel.logger import set_log_level

from utils.async_role_playing import OwlRolePlaying, run_society

from utils.mcp.mcp_toolkit_manager import MCPToolkitManager


load_dotenv()
set_log_level(level="DEBUG")


async def construct_society(
    question: str,
    tools: List[FunctionTool],
) -> OwlRolePlaying:
    """
    构建一个多Agent的OwlRolePlaying实例。
    这里的tools已经是用户想交给assistant使用的全部Tool集合。
    """
    # 1. 创建模型
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

    # 2. 配置User和Assistant
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {
        "model": models["assistant"],
        "tools": tools,  # 直接使用外部提供的全部tools
    }

    # 3. 设置任务参数
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # 4. 构造并返回OwlRolePlaying
    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
    )
    return society


async def main():
    # 准备MCP Servers
    config_path = str(
        Path(__file__).parent / "utils/mcp/mcp_servers_config.json"
    )

    manager = MCPToolkitManager.from_config(config_path)

    # 示例问题
    question = (
        "I'd like a academic report about Guohao Li, including his research "
        "direction, published papers (up to 20), institutions, etc." 
        "Then organize the report in Markdown format and save it to my desktop"
    )

    # 在main中统一用async with把所有MCP连接打开
    async with manager.connection():
        # 这里 manager.is_connected() = True
        # 获取合并后的tools
        tools = manager.get_all_tools()

        # 构造Society
        society = await construct_society(question, tools)

        # 运行对话
        answer, chat_history, token_count = await run_society(society)

    # 出了 with 块，这些toolkit就全部关闭
    # manager.is_connected() = False

    # 打印结果
    print(f"\033[94mAnswer: {answer}\033[0m")
    print("Chat History:", chat_history)
    print("Token Count:", token_count)


if __name__ == "__main__":
    asyncio.run(main())