"""Logging configuration for the OWL Requirements Analysis system."""

import os
import sys
import json
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
        format=config.get("log_format", "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"),
        level=config.get("console_log_level", "INFO"),  # 控制台默认使用INFO级别，减少输出量
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add detailed file handler with rotation and compression
    logger.add(
        config["log_file"],
        format=config.get("log_format", "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"),
        level=config.get("log_level", "DEBUG"),  # 文件日志使用DEBUG级别，记录所有详细信息
        rotation=config.get("log_rotation", "1 day"),
        retention=config.get("log_retention", "7 days"),
        compression=config.get("log_compression", "zip"),
        backtrace=True,
        diagnose=True,
        enqueue=True
    )
    
    # 添加专门的JSON日志文件，记录结构化数据
    logger.add(
        Path(log_dir) / "json_data.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record: "json_data" in record["extra"],
        enqueue=True
    )
    
    # Configure exception handling
    logger.add(
        Path(log_dir) / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        filter=lambda record: record["level"].name == "ERROR"
    )
    
    # 添加专门的LLM交互日志文件
    logger.add(
        Path(log_dir) / "llm_interactions.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record: "llm_interaction" in record["extra"],
        enqueue=True
    )

def get_logger(name: str) -> "logger":
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)

def log_json_data(logger: "logger", data_type: str, data: Dict[str, Any]) -> None:
    """Log structured JSON data to a dedicated log file.
    
    Args:
        logger: Logger instance
        data_type: Type of data being logged (e.g., 'llm_response', 'extracted_requirements')
        data: The data to log
    """
    json_logger = logger.bind(json_data=True)
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        json_logger.debug(f"[{data_type}] {json_str}")
    except Exception as e:
        json_logger.error(f"Failed to serialize {data_type} data: {e}")

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
    llm_logger = logger.bind(llm_interaction=True)
    
    # 创建结构化的交互日志
    interaction_log = {
        "prompt": prompt,
        "response": response,
        "error": str(error) if error else None,
        "metadata": metadata or {}
    }
    
    # 记录简短版本到主日志
    if error:
        logger.error(f"LLM交互失败: {str(error)}", exc_info=True)
    else:
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        response_preview = response[:100] + "..." if response and len(response) > 100 else response
        logger.debug(f"LLM交互: 提示={prompt_preview}, 响应={response_preview}")
    
    # 记录完整版本到专用日志文件
    try:
        log_json = json.dumps(interaction_log, ensure_ascii=False, indent=2)
        llm_logger.debug(f"完整LLM交互:\n{log_json}")
    except Exception as e:
        llm_logger.error(f"无法序列化LLM交互日志: {e}")

def log_extraction_result(logger: "logger", result: Dict[str, Any], success: bool) -> None:
    """Log requirements extraction result.
    
    Args:
        logger: Logger instance
        result: Extraction result
        success: Whether extraction was successful
    """
    if success:
        logger.info(f"需求提取成功: 找到 {len(result.get('requirements', []))} 条需求")
        log_json_data(logger, "extraction_result", result)
    else:
        logger.warning("需求提取失败")
        if result:
            log_json_data(logger, "invalid_extraction_result", result) 