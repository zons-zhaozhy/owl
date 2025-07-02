"""OpenAI LLM service provider implementation."""

import json
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from loguru import logger

from ..base import BaseLLMService
from ...core.logging import log_llm_interaction

class OpenAIProvider(BaseLLMService):
    """OpenAI LLM service provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider.
        
        Args:
            config: Provider configuration
        """
        super().__init__(config)
        
        self.client = AsyncOpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("api_base", "https://api.openai.com/v1")
        )
        
        self.logger = logger.bind(name="owl.llm.openai")
        self.logger.debug(f"初始化OpenAI提供者: {json.dumps(config, indent=2)}")
        
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stop: Stop sequences
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            self.logger.debug("准备发送请求到OpenAI API")
            self.logger.debug(f"请求参数:\n{json.dumps({'prompt': prompt, 'temperature': temperature, 'max_tokens': max_tokens, 'stop': stop, **kwargs}, indent=2, ensure_ascii=False)}")
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4-turbo-preview"),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
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
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stop": stop,
                    "model": self.config.get("model"),
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
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stop": stop,
                    "model": self.config.get("model")
                }
            )
            raise
            
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """Generate text using OpenAI API with conversation history.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stop: Stop sequences
            **kwargs: Additional parameters
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            self.logger.debug("准备发送带历史记录的请求到OpenAI API")
            self.logger.debug(f"请求参数:\n{json.dumps({'messages': messages, 'temperature': temperature, 'max_tokens': max_tokens, 'stop': stop, **kwargs}, indent=2, ensure_ascii=False)}")
            
            response = await self.client.chat.completions.create(
                model=self.config.get("model", "gpt-4-turbo-preview"),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
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
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stop": stop,
                    "model": self.config.get("model"),
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
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stop": stop,
                    "model": self.config.get("model")
                }
            )
            raise