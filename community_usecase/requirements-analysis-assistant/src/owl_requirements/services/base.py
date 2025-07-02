"""Base classes for services."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..core.config import SystemConfig


class ServiceError(Exception):
    """Base exception for service errors."""

    pass


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, config: Optional[SystemConfig] = None):
        """Initialize base service.

        Args:
            config: System configuration
        """
        self.config = config

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the service."""
        pass


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""

    pass


class InvalidParameterError(LLMServiceError):
    """Exception raised for invalid parameters."""

    pass


class BaseLLMService(BaseService):
    """Base class for LLM services."""

    def __init__(self, config: SystemConfig):
        """Initialize base LLM service.

        Args:
            config: System configuration
        """
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize the LLM service."""
        pass

    async def cleanup(self) -> None:
        """Clean up the LLM service."""
        pass

    def validate_parameters(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> None:
        """Validate LLM parameters.

        Args:
            temperature: Temperature parameter (0-1)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter (0-1)
            frequency_penalty: Frequency penalty parameter (-2 to 2)
            presence_penalty: Presence penalty parameter (-2 to 2)
            stop_sequences: Stop sequences

        Raises:
            InvalidParameterError: If any parameter is invalid
        """
        if temperature is not None:
            if not isinstance(temperature, (int, float)):
                raise InvalidParameterError("Temperature must be a number")
            if temperature < 0 or temperature > 1:
                raise InvalidParameterError("Temperature must be between 0 and 1")

        if max_tokens is not None:
            if not isinstance(max_tokens, int):
                raise InvalidParameterError("Max tokens must be an integer")
            if max_tokens < 1:
                raise InvalidParameterError("Max tokens must be positive")

        if top_p is not None:
            if not isinstance(top_p, (int, float)):
                raise InvalidParameterError("Top-p must be a number")
            if top_p < 0 or top_p > 1:
                raise InvalidParameterError("Top-p must be between 0 and 1")

        if frequency_penalty is not None:
            if not isinstance(frequency_penalty, (int, float)):
                raise InvalidParameterError("Frequency penalty must be a number")
            if frequency_penalty < -2 or frequency_penalty > 2:
                raise InvalidParameterError(
                    "Frequency penalty must be between -2 and 2"
                )

        if presence_penalty is not None:
            if not isinstance(presence_penalty, (int, float)):
                raise InvalidParameterError("Presence penalty must be a number")
            if presence_penalty < -2 or presence_penalty > 2:
                raise InvalidParameterError("Presence penalty must be between -2 and 2")

        if stop_sequences is not None:
            if not isinstance(stop_sequences, list):
                raise InvalidParameterError("Stop sequences must be a list")
            if not all(isinstance(s, str) for s in stop_sequences):
                raise InvalidParameterError("Stop sequences must be strings")

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        生成文本。

        Args:
            prompt: 提示词

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[list] = None,
        **kwargs,
    ) -> str:
        """Generate text using LLM with conversation history.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            stop: Stop sequences
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError
