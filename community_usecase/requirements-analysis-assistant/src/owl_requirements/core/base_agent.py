import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from .config import AgentConfig, AgentStatus, AgentRole
from .exceptions import AgentError, ConfigurationError

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """智能体基类，定义了所有智能体的基本接口和共同功能。
    
    提供核心功能：
    - 配置管理
    - 状态跟踪
    - 基础通信
    - 错误处理
    - 资源管理
    - 指标收集
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化智能体。

        Args:
            config: 配置字典，包含智能体所需的配置参数

        Raises:
            ConfigurationError: 配置无效
        """
        try:
            self.validate_config(config)
            self.config = config
            self.name = config.get("name", self.__class__.__name__)
            self.description = config.get("description", "")
            self.version = config.get("version", "1.0.0")
            
            # 状态管理
            self.status = AgentStatus.IDLE
            self.last_error: Optional[Exception] = None
            self.start_time: Optional[datetime] = None
            self.end_time: Optional[datetime] = None
            
            # 日志记录器
            self.logger = logging.getLogger(f"owl.agent.{self.name}")
            
            # 性能指标
            self.metrics = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_processing_time": 0.0,
                "average_processing_time": 0.0,
                "last_call_timestamp": None
            }
            
            # 状态存储
            self.state = {}

        except Exception as e:
            logger.error(f"智能体初始化失败: {str(e)}")
            raise ConfigurationError(f"智能体初始化失败: {str(e)}") from e

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据。

        这是智能体的主要入口点，必须由子类实现。

        Args:
            input_data: 输入数据

        Returns:
            Dict[str, Any]: 处理结果

        Raises:
            AgentError: 处理失败
        """
        raise NotImplementedError

    def validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置的有效性。

        Args:
            config: 要验证的配置

        Raises:
            ConfigurationError: 配置无效
        """
        if not isinstance(config, dict):
            raise ConfigurationError("配置必须是字典类型")

        required_fields = self.get_required_config_fields()
        missing_fields = [
            field for field in required_fields
            if field not in config
        ]

        if missing_fields:
            raise ConfigurationError(
                f"配置缺少必要字段: {', '.join(missing_fields)}"
            )

    def get_required_config_fields(self) -> List[str]:
        """获取必需的配置字段列表。

        Returns:
            List[str]: 必需的配置字段列表
        """
        return ["name"]  # 基类要求的最小配置

    async def start(self) -> None:
        """启动智能体。"""
        self.status = AgentStatus.BUSY
        self.start_time = datetime.now()
        self.logger.info(f"智能体 {self.name} 已启动")

    async def stop(self) -> None:
        """停止智能体。"""
        self.status = AgentStatus.TERMINATED
        self.end_time = datetime.now()
        self.logger.info(f"智能体 {self.name} 已停止")

    def get_status(self) -> Dict[str, Any]:
        """获取智能体当前状态和指标。

        Returns:
            Dict[str, Any]: 状态信息和指标
        """
        return {
            "name": self.name,
            "role": self.config.get("role", "unknown"),
            "status": self.status.value,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "metrics": self.metrics,
            "last_error": str(self.last_error) if self.last_error else None,
            "config": self.config
        }

    async def handle_error(self, error: Exception) -> None:
        """处理处理过程中的错误。

        Args:
            error: 发生的异常
        """
        self.last_error = error
        self.metrics["failed_calls"] += 1
        self.status = AgentStatus.ERROR
        self.logger.error(f"智能体 {self.name} 错误: {error}", exc_info=True)

    def _update_metrics(self, success: bool, processing_time: float) -> None:
        """更新智能体指标。

        Args:
            success: 调用是否成功
            processing_time: 处理时间（秒）
        """
        self.metrics["total_calls"] += 1
        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1

        self.metrics["total_processing_time"] += processing_time
        self.metrics["average_processing_time"] = (
            self.metrics["total_processing_time"] /
            self.metrics["total_calls"]
        )
        self.metrics["last_call_timestamp"] = datetime.now().isoformat()

    def get_state(self) -> Dict[str, Any]:
        """获取智能体当前状态。

        Returns:
            Dict[str, Any]: 当前状态
        """
        return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """设置智能体状态。

        Args:
            state: 新的状态
        """
        self.state = state.copy()

    def update_state(self, updates: Dict[str, Any]) -> None:
        """更新智能体状态。

        Args:
            updates: 状态更新
        """
        self.state.update(updates)

    def clear_state(self) -> None:
        """清除智能体状态。"""
        self.state.clear()

    async def initialize(self) -> None:
        """初始化智能体。可以被子类重写以实现特定的初始化逻辑。

        Raises:
            AgentError: 初始化失败
        """
        try:
            self.logger.info(f"正在初始化智能体: {self.name}")
            # 子类可以在这里添加特定的初始化逻辑

        except Exception as e:
            self.logger.error(f"智能体初始化失败: {str(e)}")
            raise AgentError(f"智能体初始化失败: {str(e)}") from e

    async def cleanup(self) -> None:
        """清理智能体资源。可以被子类重写以实现特定的清理逻辑。

        Raises:
            AgentError: 清理失败
        """
        try:
            self.logger.info(f"正在清理智能体资源: {self.name}")
            # 子类可以在这里添加特定的清理逻辑

        except Exception as e:
            self.logger.error(f"智能体资源清理失败: {str(e)}")
            raise AgentError(f"智能体资源清理失败: {str(e)}") from e

    def __str__(self) -> str:
        """返回智能体的字符串表示。"""
        return f"{self.name} (v{self.version})"

    def __repr__(self) -> str:
        """返回智能体的详细字符串表示。"""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"description='{self.description}')"
        ) 