"""CLI interface for the requirements analysis system."""

import typer
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from dataclasses import asdict

from owl_requirements.core.coordinator import AgentCoordinator
from owl_requirements.core.config import load_config, SystemConfig
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.services.llm import create_llm_service, LLMConfig, LLMProvider
from owl_requirements.services.prompts import PromptManager
from owl_requirements.utils.exceptions import (
    RequirementsError,
    AnalysisError,
    QualityCheckError,
    DocumentationError
)
from owl_requirements.utils.enums import AgentRole

# Create CLI app
app = typer.Typer(
    name="需求分析助手",
    help="基于OWL框架的需求分析系统",
    add_completion=False
)

def get_cli_app(coordinator: AgentCoordinator, system_config: SystemConfig) -> typer.Typer:
    # Create console
    console = Console()

    @app.command()
    def analyze(
        text: str = typer.Argument(..., help="需求文本"),
        output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径")
    ):
        """分析需求文本。"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Process requirements
                task = progress.add_task("正在分析需求...", total=None)
                result = coordinator.analyze(text)
                progress.remove_task(task)
                
            # Output result
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                console.print(f"结果已保存到: {output_file}")
            else:
                console.print_json(json.dumps(result, indent=2, ensure_ascii=False))
                
        except (RequirementsError, AnalysisError, QualityCheckError, DocumentationError) as e:
            console.print(f"[red]错误: {str(e)}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]发生未知错误: {str(e)}[/red]")
            raise typer.Exit(1)

    return app

if __name__ == "__main__":
    # This block is for direct execution of this file during development/testing
    # It should not be called when run via main.py
    app() 