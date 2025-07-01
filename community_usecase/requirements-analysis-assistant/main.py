import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import config
from src.owl_requirements.agents.requirements import RequirementsAgent
from src.owl_requirements.web.web_app import app as web_app
from src.owl_requirements.cli.cli_app import CLIApp
from src.owl_requirements.utils.exceptions import RequirementsAnalysisError

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_web_mode() -> None:
    """运行Web界面模式"""
    try:
        logger.info(f"Starting web server at http://{config.web.host}:{config.web.port}")
        import uvicorn
        uvicorn.run(
            web_app,
            host=config.web.host,
            port=config.web.port,
            debug=config.web.debug,
            allowed_hosts=config.web.allowed_hosts
        )
    except Exception as e:
        logger.error(f"Web server error: {str(e)}")
        raise

async def run_cli_mode() -> None:
    """运行CLI交互模式"""
    try:
        cli = CLIApp()
        await cli.run()
    except Exception as e:
        logger.error(f"CLI interface error: {str(e)}")
        raise

async def run_once_mode(requirements: str) -> None:
    """运行单次执行模式
    
    Args:
        requirements: Requirements to analyze
    """
    try:
        analyzer = RequirementsAgent()
        result = await analyzer.analyze(requirements)
        print(result)
    except RequirementsAnalysisError as e:
        logger.error(f"Requirements analysis error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

async def main(mode: str = "web", requirements: Optional[str] = None) -> None:
    """主函数
    
    Args:
        mode: Running mode (web, cli, once)
        requirements: Requirements for once mode
    """
    try:
        if mode == "web":
            await run_web_mode()
        elif mode == "cli":
            await run_cli_mode()
        elif mode == "once":
            if not requirements:
                logger.error("Requirements must be provided in once mode")
                sys.exit(1)
            await run_once_mode(requirements)
        else:
            logger.error(f"Unsupported mode: {mode}")
            sys.exit(1)
            
    except RequirementsAnalysisError as e:
        logger.error(f"Requirements analysis failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OWL Requirements Analysis Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run web interface:
    python main.py
    python main.py --mode web
    
  Run CLI interface:
    python main.py --mode cli
    
  Run once and exit:
    python main.py --mode once "Your requirements here"
"""
    )
    
    parser.add_argument(
        "--mode",
        choices=["web", "cli", "once"],
        default="web",
        help="Running mode: web (default), cli, once"
    )
    
    parser.add_argument(
        "requirements",
        nargs="?",
        help="Requirements for once mode"
    )
    
    args = parser.parse_args()
    
    if args.mode == "once" and not args.requirements:
        parser.error("Requirements must be provided in once mode")
        
    try:
        asyncio.run(main(args.mode, args.requirements))
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0) 