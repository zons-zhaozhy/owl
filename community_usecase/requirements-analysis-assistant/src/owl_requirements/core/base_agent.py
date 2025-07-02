import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .exceptions import AgentError, ConfigurationError

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """智能体基类，定义了所有智能体的基本接口和共同功能。"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能体。

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
            self.state = {}

        except Exception as e:
            logger.error(f"智能体初始化失败: {str(e)}")
            raise ConfigurationError(f"智能体初始化失败: {str(e)}") from e

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据。

        Args:
            input_data: 输入数据

        Returns:
            Dict[str, Any]: 处理结果

        Raises:
            AgentError: 处理失败
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        验证配置的有效性。

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

    def get_required_config_fields(self) -> list[str]:
        """
        获取必需的配置字段列表。

        Returns:
            list[str]: 必需的配置字段列表
        """
        return []

    def get_state(self) -> Dict[str, Any]:
        """
        获取智能体当前状态。

        Returns:
            Dict[str, Any]: 当前状态
        """
        return self.state.copy()

    def set_state(self, state: Dict[str, Any]) -> None:
        """
        设置智能体状态。

        Args:
            state: 新的状态
        """
        self.state = state.copy()

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        更新智能体状态。

        Args:
            updates: 状态更新
        """
        self.state.update(updates)

    def clear_state(self) -> None:
        """清除智能体状态。"""
        self.state.clear()

    async def initialize(self) -> None:
        """
        初始化智能体。可以被子类重写以实现特定的初始化逻辑。

        Raises:
            AgentError: 初始化失败
        """
        try:
            logger.info(f"正在初始化智能体: {self.name}")
            # 子类可以在这里添加特定的初始化逻辑

        except Exception as e:
            logger.error(f"智能体初始化失败: {str(e)}")
            raise AgentError(f"智能体初始化失败: {str(e)}") from e

    async def cleanup(self) -> None:
        """
        清理智能体资源。可以被子类重写以实现特定的清理逻辑。

        Raises:
            AgentError: 清理失败
        """
        try:
            logger.info(f"正在清理智能体资源: {self.name}")
            # 子类可以在这里添加特定的清理逻辑

        except Exception as e:
            logger.error(f"智能体资源清理失败: {str(e)}")
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