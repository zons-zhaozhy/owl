"""Main entry point for the requirements analysis assistant."""

import asyncio
import typer
import uvicorn
import logging
from pathlib import Path
from typing import Optional

from owl_requirements.core.config import SystemConfig
from owl_requirements.core.coordinator import RequirementsCoordinator
from owl_requirements.web.app import create_web_app
from owl_requirements.cli.app import create_cli_app
from ..core.coordinator import get_coordinator

# 创建CLI应用
app = typer.Typer()


@app.command()
def main(
    mode: str = typer.Option("web", help="运行模式: web, cli, once"),
    text: Optional[str] = typer.Option(None, help="需求文本（仅用于once模式）"),
    port: int = typer.Option(8082, help="Web服务端口"),
    host: str = typer.Option("0.0.0.0", help="Web服务主机"),
    provider: str = typer.Option("ollama", help="LLM提供商: ollama, openai"),
    config_file: Optional[str] = typer.Option(None, help="配置文件路径"),
):
    """OWL需求分析助手"""
    try:
        # 加载配置
        config = SystemConfig()
        if config_file:
            config = SystemConfig.from_yaml(Path(config_file))

        # 更新配置
        config.mode = mode
        config.port = port
        config.host = host
        config.llm.provider = provider

        if mode == "web":
            # Web模式
            app = create_web_app(config)
            uvicorn.run(app, host=host, port=port)
        elif mode == "cli":
            # CLI模式
            app = create_cli_app(config)
            app()
        elif mode == "once":
            # 单次执行模式
            if not text:
                raise ValueError("once模式需要提供需求文本")

            _coordinator = RequirementsCoordinator(config)
            result = asyncio.run(coordinator.process(text))
            print(result.json(indent=2, ensure_ascii=False))
        else:
            raise ValueError(f"不支持的运行模式: {mode}")

    except Exception as e:
        logging.error(f"程序运行错误: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
