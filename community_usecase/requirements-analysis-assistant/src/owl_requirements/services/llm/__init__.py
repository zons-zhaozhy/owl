"""LLM service interface and base types for the OWL Requirements Analysis system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

@dataclass
class LLMResponse:
    """Response from an LLM model."""
    text: str
    tokens_used: int
    model: str
    provider: LLMProvider
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class LLMConfig:
    """Configuration for LLM service."""
    provider: LLMProvider
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stop_sequences: Optional[List[str]] = None
    extra_config: Optional[Dict[str, Any]] = None

class LLMService(ABC):
    """Base class for LLM services."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the LLM service.
        
        Args:
            config: Configuration for this LLM service
        """
        self.config = config
        
    @abstractmethod
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response
        """
        raise NotImplementedError
        
    @abstractmethod
    async def generate_with_history(
        self, 
        prompt: str,
        history: List[Dict[str, str]]
    ) -> LLMResponse:
        """Generate a response considering conversation history.
        
        Args:
            prompt: The current prompt
            history: List of previous exchanges in [{"role": "...", "content": "..."}] format
            
        Returns:
            The LLM's response
        """
        raise NotImplementedError

# Import and expose factory function
from .factory import create_llm_service

__all__ = [
    'LLMProvider',
    'LLMResponse',
    'LLMConfig',
    'LLMService',
    'create_llm_service'
]