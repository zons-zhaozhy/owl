from ..services.llm_manager import get_llm_manager

"""Base agent class for OWL Requirements Analysis system."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the requirements analysis system."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base agent.

        Args:
            name: Agent name
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.llm_manager = get_llm_manager()

        # 设置LLM提供商（如果配置中指定了）
        provider = self.config.get("llm_provider")
        if provider:
            try:
                self.llm_manager.set_provider(provider)
                logger.info(f"智能体 {name} 使用LLM提供商: {provider}")
            except Exception as e:
                logger.warning(f"设置LLM提供商失败，使用默认: {e}")

        logger.info(f"初始化智能体: {name}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results.

        Args:
            input_data: Input data to process

        Returns:
            Processing results
        """
        pass

    async def _call_llm(
        self,
        prompt: str,
        template_name: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Call LLM service with error handling.

        Args:
            prompt: User prompt or template parameters
            template_name: Optional template name to use
            provider: Optional provider override
            **kwargs: Additional arguments

        Returns:
            Generated text

        Raises:
            LLMServiceError: If LLM call fails
        """
        try:
            if template_name:
                response = await self.llm_manager.generate(
                    template_name=template_name,
                    provider=provider,
                    prompt=prompt,  # 传递原始prompt
                    **kwargs,
                )
            else:
                response = await self.llm_manager.generate(
                    prompt=prompt, provider=provider, **kwargs
                )

            logger.debug(f"LLM响应长度: {len(response.content)}")
            return response.content

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise LLMServiceError(f"LLM调用失败: {e}")

    async def _call_llm_with_template(self, template_name: str, **kwargs) -> str:
        """使用模板调用LLM"""
        try:
            # 如果是需求提取模板，将 input 映射到 input_text
            if template_name == "requirements_extraction" and "input" in kwargs:
                kwargs["input_text"] = kwargs.pop("input")

            response = await self.llm_manager.generate(
                _template_name=template_name, **kwargs
            )
            return response.content
        except Exception as e:
            logger.error(f"模板LLM调用失败: {e}")
            raise LLMServiceError(f"模板LLM调用失败: {e}")

    def _format_prompt(self, template: str, **kwargs) -> str:
        """Format prompt template with variables.

        Args:
            template: Prompt template
            **kwargs: Template variables

        Returns:
            Formatted prompt
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"提示模板格式化失败，缺少变量: {e}")
            raise
        except Exception as e:
            logger.error(f"提示模板格式化失败: {e}")
            raise

    def get_available_providers(self) -> List[str]:
        """获取可用的LLM提供商列表"""
        return self.llm_manager.get_available_providers()

    def set_provider(self, provider: str):
        """设置LLM提供商"""
        self.llm_manager.set_provider(provider)
        logger.info(f"智能体 {self.name} 切换到提供商: {provider}")

    async def close(self):
        """清理资源"""
        # 子类可以重写此方法来清理特定资源
        pass
