"""Enum definitions for the system."""

from enum import Enum, auto

class AgentRole(str, Enum):
    """Agent role enum."""
    
    REQUIREMENTS_EXTRACTOR = "REQUIREMENTS_EXTRACTOR"
    REQUIREMENTS_ANALYZER = "REQUIREMENTS_ANALYZER"
    QUALITY_CHECKER = "QUALITY_CHECKER"
    DOCUMENTATION_GENERATOR = "DOCUMENTATION_GENERATOR"
    
    def __str__(self) -> str:
        """Return string representation.
        
        Returns:
            String representation
        """
        return self.value

class LLMProvider(str, Enum):
    """LLM provider enum."""
    
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    
    def __str__(self) -> str:
        """Return string representation.
        
        Returns:
            String representation
        """
        return self.value

class Priority(str, Enum):
    """Priority level enum."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    def __str__(self) -> str:
        return self.value

class RequirementType(str, Enum):
    """Requirement type enum."""
    
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    
    def __str__(self) -> str:
        return self.value

class QualityLevel(str, Enum):
    """Quality level enum."""
    
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    
    def __str__(self) -> str:
        return self.value 