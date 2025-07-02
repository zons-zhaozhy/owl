from enum import Enum

"""Enum definitions for the system."""


class AgentStatus(str, Enum):
    """Agent status enum."""

    _IDLE = "idle"
    _PROCESSING = "processing"
    _COMPLETED = "completed"
    _ERROR = "error"
    _WAITING = "waiting"

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation
        """
        return self.value


class AgentRole(str, Enum):
    """Agent role enum."""

    _REQUIREMENTS_EXTRACTOR = "REQUIREMENTS_EXTRACTOR"
    _REQUIREMENTS_ANALYZER = "REQUIREMENTS_ANALYZER"
    _QUALITY_CHECKER = "QUALITY_CHECKER"
    _DOCUMENTATION_GENERATOR = "DOCUMENTATION_GENERATOR"

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation
        """
        return self.value


class LLMProvider(str, Enum):
    """LLM provider enum."""

    _DEEPSEEK = "deepseek"
    _OPENAI = "openai"
    _OLLAMA = "ollama"
    _ANTHROPIC = "anthropic"

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation
        """
        return self.value


class DocumentFormat(str, Enum):
    """Document format enum."""

    _MARKDOWN = "markdown"
    _JSON = "json"
    _HTML = "html"
    _PDF = "pdf"
    _DOCX = "docx"

    def __str__(self) -> str:
        return self.value


class QualityMetric(str, Enum):
    """Quality metric enum."""

    _COMPLETENESS = "completeness"
    _CLARITY = "clarity"
    _CONSISTENCY = "consistency"
    _TESTABILITY = "testability"
    _FEASIBILITY = "feasibility"

    def __str__(self) -> str:
        return self.value


class RequirementType(str, Enum):
    """Requirement type enum."""

    FUNCTIONAL = "functional"
    _NON_FUNCTIONAL = "non_functional"

    def __str__(self) -> str:
        return self.value


class RequirementPriority(str, Enum):
    """Requirement priority enum."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        return self.value


class RequirementStatus(str, Enum):
    """Requirement status enum."""

    _DRAFT = "draft"
    _REVIEW = "review"
    _APPROVED = "approved"
    _IMPLEMENTED = "implemented"
    _TESTED = "tested"
    _CLOSED = "closed"

    def __str__(self) -> str:
        return self.value


class Priority(str, Enum):
    """Priority level enum."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        return self.value


class QualityLevel(str, Enum):
    """Quality level enum."""

    _EXCELLENT = "excellent"
    _GOOD = "good"
    _AVERAGE = "average"
    _POOR = "poor"

    def __str__(self) -> str:
        return self.value


class ProcessingStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
