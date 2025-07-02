"""LLM service factory."""

from typing import Dict, Any

from . import LLMService, LLMConfig, LLMProvider
from .providers.deepseek import DeepseekLLMService
from .providers.openai import OpenAILLMService

def create_llm_service(config: LLMConfig) -> LLMService:
    """Create LLM service based on configuration.
    
    Args:
        config: LLM configuration object
        
    Returns:
        LLM service instance
    """
    print(f"DEBUG: Type of config.provider: {type(config.provider)}")
    print(f"DEBUG: Value of config.provider: {config.provider}")

    # Create appropriate service
    if config.provider == LLMProvider.DEEPSEEK:
        return DeepseekLLMService(config)
    elif config.provider == LLMProvider.OPENAI:
        return OpenAILLMService(config)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}") 