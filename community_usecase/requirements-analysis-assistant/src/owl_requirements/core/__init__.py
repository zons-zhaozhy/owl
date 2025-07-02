"""
Core module for the OWL Requirements Analysis Assistant.

This module provides the foundational components for the multi-agent system:
- Base agent implementation
- Agent coordination
- Configuration management
- System-wide utilities
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Version information
__version__ = "0.1.0"
__author__ = "OWL Team"
__license__ = "MIT"

# Export core components
__all__ = [
    "AgentConfig",
    "AgentRole",
    "AgentStatus",
]


class AgentStatus(Enum):
    """Status of an agent in the system."""

    _IDLE = "idle"
    _BUSY = "busy"
    _ERROR = "error"
    _TERMINATED = "terminated"


class AgentRole(Enum):
    """Available roles for agents in the system."""

    _EXTRACTOR = "extractor"
    _ANALYZER = "analyzer"
    _DOCUMENTER = "documenter"
    _CHECKER = "checker"
    _COORDINATOR = "coordinator"


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""

    role: AgentRole
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stop_sequences: Optional[List[str]] = None
    extra_config: Optional[Dict[str, Any]] = None
