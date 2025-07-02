"""LLM service factory."""

from typing import Dict, Any
from .base import BaseLLMService
from .llm.deepseek_provider import DeepSeekProvider
from .llm.openai_provider import OpenAIProvider
from ..core.config import SystemConfig

def create_llm_service(config: SystemConfig) -> BaseLLMService:
    """Create LLM service instance.
    
    Args:
        config: System configuration
        
    Returns:
        LLM service instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider = config.llm_provider.lower()
    
    if provider == "deepseek":
        return DeepSeekProvider(config)
    elif provider == "openai":
        return OpenAIProvider(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}") 