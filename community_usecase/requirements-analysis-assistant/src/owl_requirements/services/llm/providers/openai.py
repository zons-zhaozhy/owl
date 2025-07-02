"""OpenAI LLM service implementation."""

import os
from typing import Dict, Any, List, Optional
from openai import OpenAI

from .. import LLMService, LLMResponse, LLMProvider, LLMConfig

class OpenAILLMService(LLMService):
    """OpenAI LLM service implementation."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        super().__init__(config)
        
        # Initialize API client
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing API key for OpenAI LLM service")
            
        self.client = OpenAI(api_key=api_key)
        
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text using LLM.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stop=self.config.stop_sequences
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.config.model,
                provider=LLMProvider.OPENAI
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI LLM generation failed: {e}") from e
            
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
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stop=self.config.stop_sequences
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.config.model,
                provider=LLMProvider.OPENAI
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI LLM generation failed: {e}") from e 