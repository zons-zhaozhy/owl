"""Main entry point for the requirements analysis system."""

import typer
import asyncio
import logging
from pathlib import Path
from typing import Optional
from enum import Enum
from rich.console import Console

from owl_requirements.core.config import SystemConfig, load_config, AgentRole
from owl_requirements.core.coordinator import AgentCoordinator
from owl_requirements.services.llm import create_llm_service, LLMConfig, LLMProvider
from owl_requirements.cli.app import get_cli_app
from owl_requirements.web.app import create_web_app
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.core.logging import setup_logging

logger = logging.getLogger(__name__)

app = typer.Typer()

class Mode(str, Enum):
    """运行模式"""
    CLI = "cli"
    WEB = "web"
    ONCE = "once"

def initialize_coordinator(system_config: SystemConfig) -> AgentCoordinator:
    """Initializes the LLM service and AgentCoordinator with all agents."""
    # 创建LLM配置和服务
    llm_config = LLMConfig(
        provider=LLMProvider(system_config.llm_provider),  # 将字符串转换为枚举
        model=system_config.llm_model,
        api_key=system_config.llm_api_key,
        temperature=system_config.llm_temperature,
        max_tokens=system_config.llm_max_tokens
    )
    llm_service = create_llm_service(llm_config)

    # 直接传递system_config给智能体构造函数
    extractor = RequirementsExtractor(llm_service=llm_service, config=system_config)
    analyzer = RequirementsAnalyzer(llm_service=llm_service, config=system_config)
    checker = QualityChecker(llm_service=llm_service, config=system_config)
    generator = DocumentationGenerator(llm_service=llm_service, config=system_config)

    coordinator = AgentCoordinator(
        extractor=extractor,
        analyzer=analyzer,
        checker=checker,
        generator=generator
    )
    return coordinator

@app.command("run")
def run_app(
    mode: Mode = typer.Option(Mode.WEB, "--mode", "-m", help="运行模式：cli, web, once"),
    text: str = typer.Option(None, "--text", "-t", help="单次模式下的需求文本"),
    config_path: str = typer.Option("config.yaml", "--config", "-c", help="配置文件路径"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Web服务器端口 (仅用于web模式)"),
):
    """运行需求分析助手。"""
    console = Console()

    try:
        # 加载配置
        system_config = load_config(config_path)
        
        # 设置日志
        setup_logging({
            "log_level": system_config.log_level,
            "log_file": system_config.log_file,
            "log_format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "log_rotation": "1 day",
            "log_retention": "7 days",
            "log_compression": "zip"
        })

        coordinator = initialize_coordinator(system_config)
        logger.info(f"启动需求分析助手 - 模式: {mode.value}")

        if mode == Mode.WEB:
            if port:
                system_config.web_port = port
            console.print("[bold green]启动Web界面...[/bold green]")
            import uvicorn
            uvicorn.run(create_web_app(coordinator, system_config), host=system_config.web_host, port=system_config.web_port)
        elif mode == Mode.CLI:
            console.print("[bold green]启动CLI交互模式...[/bold green]")
            cli_app = get_cli_app(coordinator, system_config)
            cli_app()  # 直接调用CLI应用
        elif mode == Mode.ONCE:
            if not text:
                console.print("[bold red]错误：单次模式需要通过 --text 或 -t 提供需求文本。[/bold red]\n")
                raise typer.Exit(code=1)
            console.print(f"[bold green]处理单次需求: {text}[/bold green]")
            result = asyncio.run(coordinator.process_input(session_id="once_session", input_text=text))
            console.print("[bold yellow]分析结果:[/bold yellow]")
            console.print(result)
            if result.get("needs_clarification"):
                console.print("[bold red]注意：单次模式下无法进行澄清，请修改需求描述使其更清晰。[/bold red]")
        else:
            console.print(f"[bold red]不支持的运行模式: {mode}[/bold red]\n")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("应用运行失败")
        console.print(f"[bold red]应用运行失败: {e}[/bold red]\n")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app() 