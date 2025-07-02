"""DeepSeek LLM service provider implementation."""

import json
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from loguru import logger

from ..base import BaseLLMService
from ...core.logging import log_llm_interaction
from ...core.config import SystemConfig

class DeepSeekProvider(BaseLLMService):
    """DeepSeek LLM service provider implementation."""
    
    def __init__(self, config: SystemConfig):
        """Initialize DeepSeek provider.
        
        Args:
            config: System configuration
        """
        super().__init__(config)
        
        self.client = AsyncOpenAI(
            api_key=config.llm_api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        self.logger = logger.bind(name="owl.llm.deepseek")
        self.logger.debug(f"初始化DeepSeek提供者: {json.dumps(config.__dict__, indent=2)}")
        
    async def generate(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """Generate text using DeepSeek API.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (uses config if None)
            max_tokens: Maximum number of tokens to generate (uses config if None)
            stop: Stop sequences
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            self.logger.debug("准备发送请求到DeepSeek API")
            temperature_to_use = temperature if temperature is not None else self.config.llm_temperature
            max_tokens_to_use = max_tokens if max_tokens is not None else self.config.llm_max_tokens
            self.logger.debug(f"请求参数:\n{json.dumps({'prompt': prompt, 'temperature': temperature_to_use, 'max_tokens': max_tokens_to_use, 'stop': stop, **kwargs}, indent=2, ensure_ascii=False)}")
            
            response = await self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature_to_use,
                max_tokens=max_tokens_to_use,
                stop=stop,
                **kwargs
            )
            
            generated_text = response.choices[0].message.content
            
            # Log the interaction
            log_llm_interaction(
                logger=self.logger,
                prompt=prompt,
                response=generated_text,
                metadata={
                    "temperature": temperature_to_use,
                    "max_tokens": max_tokens_to_use,
                    "stop": stop,
                    "model": self.config.llm_model,
                    "response_metadata": {
                        "finish_reason": response.choices[0].finish_reason,
                        "usage": response.usage.model_dump() if response.usage else None
                    }
                }
            )
            
            return generated_text
            
        except Exception as e:
            # Log the error
            log_llm_interaction(
                logger=self.logger,
                prompt=prompt,
                error=e,
                metadata={
                    "temperature": temperature_to_use,
                    "max_tokens": max_tokens_to_use,
                    "stop": stop,
                    "model": self.config.llm_model
                }
            )
            raise
            
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """Generate text using DeepSeek API with conversation history.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (uses config if None)
            max_tokens: Maximum number of tokens to generate (uses config if None)
            stop: Stop sequences
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            self.logger.debug("准备发送带历史记录的请求到DeepSeek API")
            temperature_to_use = temperature if temperature is not None else self.config.llm_temperature
            max_tokens_to_use = max_tokens if max_tokens is not None else self.config.llm_max_tokens
            self.logger.debug(f"请求参数:\n{json.dumps({'messages': messages, 'temperature': temperature_to_use, 'max_tokens': max_tokens_to_use, 'stop': stop, **kwargs}, indent=2, ensure_ascii=False)}")
            
            response = await self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=messages,
                temperature=temperature_to_use,
                max_tokens=max_tokens_to_use,
                stop=stop,
                **kwargs
            )
            
            generated_text = response.choices[0].message.content
            
            # Log the interaction
            log_llm_interaction(
                logger=self.logger,
                prompt=str(messages),
                response=generated_text,
                metadata={
                    "temperature": temperature_to_use,
                    "max_tokens": max_tokens_to_use,
                    "stop": stop,
                    "model": self.config.llm_model,
                    "response_metadata": {
                        "finish_reason": response.choices[0].finish_reason,
                        "usage": response.usage.model_dump() if response.usage else None
                    }
                }
            )
            
            return generated_text
            
        except Exception as e:
            # Log the error
            log_llm_interaction(
                logger=self.logger,
                prompt=str(messages),
                error=e,
                metadata={
                    "temperature": temperature_to_use,
                    "max_tokens": max_tokens_to_use,
                    "stop": stop,
                    "model": self.config.llm_model
                }
            )
            raise 