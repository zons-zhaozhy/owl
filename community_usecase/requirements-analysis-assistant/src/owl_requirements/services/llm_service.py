"""LLM服务，负责与语言模型交互。"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
import httpx

from ..core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务，负责与语言模型交互。"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM服务。

        Args:
            config: 配置字典，包含LLM服务相关设置
        """
        self.config = config
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4000)
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        self.timeout = config.get("timeout", 60)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1)

        if not self.api_key:
            logger.warning("未配置API密钥")

        # 初始化HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def generate(
        self,
        template: str,
        input_data: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        使用LLM生成内容。

        Args:
            template: 提示模板
            input_data: 输入数据
            **kwargs: 其他参数

        Returns:
            str: 生成的内容

        Raises:
            LLMServiceError: LLM服务调用失败
        """
        try:
            # 准备提示
            prompt = self._prepare_prompt(template, input_data or {})

            # 设置生成参数
            params = {
                "model": kwargs.get("model", self.model),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "messages": [
                    {"role": "system", "content": "你是一个专业的需求分析和文档生成助手。"},
                    {"role": "user", "content": prompt}
                ]
            }

            # 调用LLM服务
            response = await self._call_llm(params)

            # 处理响应
            return self._process_response(response)

        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}")
            raise LLMServiceError(f"LLM生成失败: {str(e)}") from e

    def _prepare_prompt(
        self,
        template: str,
        input_data: Dict[str, Any]
    ) -> str:
        """
        准备LLM提示。

        Args:
            template: 提示模板
            input_data: 输入数据

        Returns:
            str: 准备好的提示
        """
        try:
            # 处理输入数据
            processed_data = {
                key: self._format_value(value)
                for key, value in input_data.items()
            }

            # 格式化模板
            return template.format(**processed_data)

        except Exception as e:
            logger.error(f"提示准备失败: {str(e)}")
            raise LLMServiceError(f"提示准备失败: {str(e)}") from e

    def _format_value(self, value: Any) -> str:
        """
        格式化值为字符串。

        Args:
            value: 要格式化的值

        Returns:
            str: 格式化后的字符串
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

    async def _call_llm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用LLM服务。

        Args:
            params: 调用参数

        Returns:
            Dict[str, Any]: LLM响应

        Raises:
            LLMServiceError: 调用失败
        """
        endpoint = f"{self.api_base}/chat/completions"
        
        for attempt in range(self.retry_attempts):
            try:
                async with self.client as client:
                    response = await client.post(
                        endpoint,
                        json=params
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                        
                    # 处理错误响应
                    error_msg = f"LLM调用失败: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
                    except:
                        pass
                        
                    logger.error(error_msg)
                    
                    # 如果是最后一次尝试，抛出异常
                    if attempt == self.retry_attempts - 1:
                        raise LLMServiceError(error_msg)
                        
                    # 否则等待后重试
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    
            except httpx.TimeoutException as e:
                logger.warning(f"LLM调用超时 (尝试 {attempt + 1}/{self.retry_attempts})")
                if attempt == self.retry_attempts - 1:
                    raise LLMServiceError(f"LLM调用超时: {str(e)}") from e
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                logger.error(f"LLM调用失败: {str(e)}")
                raise LLMServiceError(f"LLM调用失败: {str(e)}") from e

    def _process_response(self, response: Dict[str, Any]) -> str:
        """
        处理LLM响应。

        Args:
            response: LLM响应

        Returns:
            str: 处理后的内容

        Raises:
            LLMServiceError: 响应处理失败
        """
        try:
            if not response.get("choices"):
                raise LLMServiceError("LLM响应中没有内容")
                
            message = response["choices"][0].get("message", {})
            if not message or "content" not in message:
                raise LLMServiceError("LLM响应格式无效")
                
            return message["content"].strip()

        except Exception as e:
            logger.error(f"响应处理失败: {str(e)}")
            raise LLMServiceError(f"响应处理失败: {str(e)}") from e

    async def close(self):
        """关闭HTTP客户端。"""
        await self.client.aclose() 