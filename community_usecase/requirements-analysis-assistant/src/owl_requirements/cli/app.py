"""CLI application for the requirements analysis system."""

import json
from pathlib import Path
from typing import Optional, Callable, Awaitable
import typer
import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.coordinator import AgentCoordinator
from ..core.config import SystemConfig

console = Console()

class CLISession:
    """CLI session state."""
    
    def __init__(self, console: Console):
        """Initialize CLI session.
        
        Args:
            console: Rich console instance
        """
        self.console = console
        self.requirements = None
        self.analysis = None
        self.documentation = None
        
    def display_requirements(self):
        """Display current requirements."""
        if self.requirements:
            self.console.print("\n[bold]当前需求:[/bold]")
            self.console.print_json(data=self.requirements)
            
    def display_analysis(self):
        """Display current analysis."""
        if self.analysis:
            self.console.print("\n[bold]分析结果:[/bold]")
            self.console.print_json(data=self.analysis)
            
    def display_documentation(self):
        """Display current documentation."""
        if self.documentation:
            self.console.print("\n[bold]生成的文档:[/bold]")
            self.console.print_json(data=self.documentation)

def create_cli_app(coordinator: AgentCoordinator, config: SystemConfig) -> Callable[[], Awaitable[None]]:
    """Create CLI application.
    
    Args:
        coordinator: Agent coordinator instance
        config: System configuration
        
    Returns:
        Async function that runs the CLI application
    """
    async def run_cli():
        """Run the CLI application."""
        session = CLISession(console)
        text = None
        
        try:
            while True:
                # Get input text
                if not text:
                    text = Prompt.ask("\n请输入需求描述")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    # Create a new session
                    session_id = coordinator.create_dialogue_session()
                    
                    # Process input
                    task = progress.add_task("正在处理需求...", total=None)
                    result = await coordinator.process_input(session_id, text)
                    progress.remove_task(task)
                    
                    # Display results
                    if result.get("needs_clarification"):
                        clarification = result["clarification"]
                        answer = Prompt.ask(
                            f"\n[bold]需求澄清[/bold]\n{clarification['question']}\n" +
                            (f"背景: {clarification['context']}\n" if clarification.get("context") else "") +
                            (f"选项:\n" + "\n".join(f"- {opt}" for opt in clarification["options"]) if clarification.get("options") else "")
                        )
                        
                        # Process clarification
                        task = progress.add_task("正在更新需求...", total=None)
                        result = await coordinator.process_input(session_id, answer)
                        progress.remove_task(task)
                    
                    # Display final results
                    if result.get("is_complete"):
                        console.print("\n[bold green]需求分析完成[/bold green]")
                        console.print("\n[bold]分析结果:[/bold]")
                        console.print_json(data=result["analysis"])
                        
                        if result.get("documentation"):
                            console.print("\n[bold]生成的文档:[/bold]")
                            console.print_json(data=result["documentation"])
                            
                            # Ask if user wants to save to file
                            if Confirm.ask("\n是否保存文档到文件？"):
                                output_path = Prompt.ask("请输入保存路径", default="output/requirements_doc.json")
                                output_file = Path(output_path)
                                output_file.parent.mkdir(parents=True, exist_ok=True)
                                output_file.write_text(
                                    json.dumps(result["documentation"], ensure_ascii=False, indent=2),
                                    encoding="utf-8"
                                )
                                console.print(f"\n文档已保存到: {output_file}")
                    else:
                        console.print("\n[bold yellow]需求收集中...[/bold yellow]")
                        console.print_json(data=result["context"])
                
                # Ask if continue with new requirements
                if not Confirm.ask("\n是否继续分析新的需求？"):
                    break
                    
                text = None  # Reset text for next iteration
                
        except Exception as e:
            console.print(f"\n[bold red]错误: {str(e)}[/bold red]")
            raise typer.Exit(code=1)
    
    return run_cli

if __name__ == "__main__":
    # This block is for direct execution of this file during development/testing
    # It should not be called when run via main.py
    app() 