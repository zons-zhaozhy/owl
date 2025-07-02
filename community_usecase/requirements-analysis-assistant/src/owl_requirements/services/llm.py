"""LLM service implementation."""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI

from .base import BaseLLMService

logger = logging.getLogger(__name__)

class DeepseekLLMService(BaseLLMService):
    """Deepseek LLM service implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.provider = config.get("provider", "deepseek")
        self.model = config.get("model", "deepseek-chat")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4000)
        
        # Initialize API client
        api_key = config.get("api_key") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Missing API key for LLM service")
            
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text using LLM.
        
        Args:
            prompt: Input prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            top_p: Optional top-p sampling parameter
            frequency_penalty: Optional frequency penalty
            presence_penalty: Optional presence penalty
            stop_sequences: Optional stop sequences
            
        Returns:
            Generated text
        """
        try:
            # Build parameters dict with only supported parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
            
            # Only add optional parameters if they are provided and supported
            if stop_sequences:
                params["stop"] = stop_sequences
                
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise
            
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text using LLM with conversation history.
        
        Args:
            messages: List of conversation messages
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            top_p: Optional top-p sampling parameter
            frequency_penalty: Optional frequency penalty
            presence_penalty: Optional presence penalty
            stop_sequences: Optional stop sequences
            
        Returns:
            Generated text
        """
        try:
            # Build parameters dict with only supported parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
            
            # Only add optional parameters if they are provided and supported
            if stop_sequences:
                params["stop"] = stop_sequences
                
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise
            
class OpenAILLMService(BaseLLMService):
    """OpenAI LLM service implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4000)
        self.top_p = config.get("top_p", 0.1)
        self.frequency_penalty = config.get("frequency_penalty", 0.1)
        self.presence_penalty = config.get("presence_penalty", 0.1)
        
        # Initialize API client
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing API key for LLM service")
            
        self.client = OpenAI(api_key=api_key)
        
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text using LLM.
        
        Args:
            prompt: Input prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            top_p: Optional top-p sampling parameter
            frequency_penalty: Optional frequency penalty
            presence_penalty: Optional presence penalty
            stop_sequences: Optional stop sequences
            
        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                top_p=top_p or self.top_p,
                frequency_penalty=frequency_penalty or self.frequency_penalty,
                presence_penalty=presence_penalty or self.presence_penalty,
                stop=stop_sequences
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise
            
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text using LLM with conversation history.
        
        Args:
            messages: List of conversation messages
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            top_p: Optional top-p sampling parameter
            frequency_penalty: Optional frequency penalty
            presence_penalty: Optional presence penalty
            stop_sequences: Optional stop sequences
            
        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                top_p=top_p or self.top_p,
                frequency_penalty=frequency_penalty or self.frequency_penalty,
                presence_penalty=presence_penalty or self.presence_penalty,
                stop=stop_sequences
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise
            
def create_llm_service(config: Dict[str, Any]) -> BaseLLMService:
    """Create LLM service instance.
    
    Args:
        config: LLM configuration
        
    Returns:
        LLM service instance
    """
    provider = config.get("provider", "openai").lower()
    
    if provider == "openai":
        return OpenAILLMService(config)
    elif provider == "deepseek":
        return DeepseekLLMService(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}") 