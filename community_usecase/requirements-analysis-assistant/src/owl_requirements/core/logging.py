"""Logging configuration and utilities for OWL Requirements Analysis system."""

import json
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        log_format: Optional custom log format
        enable_console: Whether to enable console logging
    """
    # 清除现有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # 默认日志格式
    if not log_format:
        _log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            _maxBytes=10 * 1024 * 1024,  # 10MB
            _backupCount=5,
            _encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成，级别: {level}")


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录请求日志"""
        self.logger.info(
            f"请求 {method} {url}",
            extra={
                "event_type": "request",
                "method": method,
                "url": url,
                "params": params,
                "headers": headers,
            },
        )

    def log_response(
        self,
        status_code: int,
        response_time: float,
        response_size: Optional[int] = None,
        response: Optional[str] = None,
    ) -> None:
        """记录响应日志"""
        self.logger.info(
            f"响应 {status_code} ({response_time:.3f}s)",
            extra={
                "event_type": "response",
                "status_code": status_code,
                "response_time": response_time,
                "response_size": response_size,
                "response": response[:200] if response else None,
            },
        )

    def log_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录错误日志"""
        self.logger.error(
            f"错误: {str(error)}",
            extra={
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
            },
            exc_info=True,
        )

    def log_performance(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录性能日志"""
        self.logger.info(
            f"性能: {operation} 耗时 {duration:.3f}s",
            extra={
                "event_type": "performance",
                "operation": operation,
                "duration": duration,
                "metadata": metadata,
            },
        )


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return StructuredLogger(name)


def log_json_data(
    logger: StructuredLogger, data_type: str, data: Dict[str, Any]
) -> None:
    """Log structured JSON data to a dedicated log file.

    Args:
        logger: Logger instance
        data_type: Type of data being logged (
            e.g.,
            'llm_response',
            'extracted_requirements'
        )
        data: The data to log
    """
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        logger.logger.debug(f"[{data_type}] {json_str}")
    except Exception as e:
        logger.logger.error(f"Failed to serialize {data_type} data: {e}")


def log_llm_interaction(
    logger: StructuredLogger,
    prompt: str,
    response: Optional[str] = None,
    error: Optional[Exception] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log LLM interaction details.

    Args:
        logger: Logger instance
        prompt: Prompt sent to LLM
        response: Response received from LLM (if any)
        error: Error encountered (if any)
        metadata: Additional metadata about the interaction
    """
    if error:
        logger.logger.error(f"LLM交互失败: {str(error)}", exc_info=True)
    else:
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        response_preview = (
            response[:100] + "..." if response and len(response) > 100 else response
        )
        logger.logger.debug(f"LLM交互: 提示={prompt_preview}, 响应={response_preview}")

    # 记录完整版本到专用日志文件
    try:
        interaction_log = {
            "prompt": prompt,
            "response": response,
            "error": str(error) if error else None,
            "metadata": metadata or {},
        }
        log_json = json.dumps(interaction_log, ensure_ascii=False, indent=2)
        logger.logger.debug(f"完整LLM交互:\n{log_json}")
    except Exception as e:
        logger.logger.error(f"无法序列化LLM交互日志: {e}")


def log_extraction_result(
    logger: StructuredLogger, result: Dict[str, Any], success: bool
) -> None:
    """Log requirements extraction result.

    Args:
        logger: Logger instance
        result: Extraction result
        success: Whether extraction was successful
    """
    if success:
        logger.logger.info(
            f"需求提取成功: 找到 {len(result.get('requirements', []))} 条需求"
        )
        log_json_data(logger, "extraction_result", result)
    else:
        logger.logger.warning("需求提取失败")
        if result:
            log_json_data(logger, "invalid_extraction_result", result)
