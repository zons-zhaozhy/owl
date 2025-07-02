"""Deepseek LLM service implementation."""

import os
from typing import Dict, Any, List, Optional
import openai
from openai import OpenAI

from .. import LLMService, LLMResponse, LLMProvider, LLMConfig

class DeepseekLLMService(LLMService):
    """Deepseek LLM service implementation using OpenAI compatible API."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        super().__init__(config)
        
        # Initialize API client
        api_key = config.api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Missing API key for Deepseek LLM service")
            
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"  # OpenAI 兼容接口
        )
        
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text using LLM.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model or "deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature or 0.1,
                max_tokens=self.config.max_tokens or 4000,
                stop=self.config.stop_sequences
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.config.model,
                provider=LLMProvider.DEEPSEEK
            )
            
        except Exception as e:
            raise RuntimeError(f"Deepseek LLM generation failed: {e}") from e
            
    async def generate_with_history(
        self,
        prompt: str,
        history: List[Dict[str, str]]
    ) -> LLMResponse:
        """Generate text using LLM with conversation history.
        
        Args:
            prompt: Current prompt
            history: Conversation history
            
        Returns:
            Generated response
        """
        try:
            messages = history + [{"role": "user", "content": prompt}]
            response = self.client.chat.completions.create(
                model=self.config.model or "deepseek-chat",
                messages=messages,
                temperature=self.config.temperature or 0.1,
                max_tokens=self.config.max_tokens or 4000,
                stop=self.config.stop_sequences
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.config.model,
                provider=LLMProvider.DEEPSEEK
            )
            
        except Exception as e:
            raise RuntimeError(f"Deepseek LLM generation failed: {e}") from e