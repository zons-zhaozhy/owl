"""Logging configuration for the OWL Requirements Analysis system."""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

def setup_logging(config: Dict[str, Any]) -> None:
    """Setup logging configuration.
    
    Args:
        config: Logging configuration dictionary containing:
            - log_level: Logging level (DEBUG, INFO, etc.)
            - log_file: Path to log file
            - log_format: Log message format
            - log_rotation: Log rotation interval
            - log_retention: Log retention period
            - log_compression: Log compression format
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(config["log_file"]).parent
    os.makedirs(log_dir, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with detailed formatting
    logger.add(
        sys.stderr,
        format=config.get("log_format", "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"),
        level=config.get("log_level", "DEBUG"),
        colorize=True
    )
    
    # Add file handler with rotation and compression
    logger.add(
        config["log_file"],
        format=config.get("log_format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
        level=config.get("log_level", "DEBUG"),
        rotation=config.get("log_rotation", "1 day"),
        retention=config.get("log_retention", "7 days"),
        compression=config.get("log_compression", "zip"),
        backtrace=True,
        diagnose=True,
        enqueue=True
    )
    
    # Configure exception handling
    logger.add(
        Path(log_dir) / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        filter=lambda record: record["level"].name == "ERROR"
    )

def get_logger(name: str) -> "logger":
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)

def log_llm_interaction(
    logger: "logger",
    prompt: str,
    response: Optional[str] = None,
    error: Optional[Exception] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Log LLM interaction details.
    
    Args:
        logger: Logger instance
        prompt: Prompt sent to LLM
        response: Response received from LLM (if any)
        error: Error encountered (if any)
        metadata: Additional metadata about the interaction
    """
    interaction_log = {
        "prompt": prompt,
        "response": response,
        "error": str(error) if error else None,
        "metadata": metadata or {}
    }
    
    if error:
        logger.error(f"LLM交互失败:\n{interaction_log}", exc_info=True)
    else:
        logger.debug(f"LLM交互详情:\n{interaction_log}") 