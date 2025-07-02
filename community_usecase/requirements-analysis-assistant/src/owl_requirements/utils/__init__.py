"""
Utility Functions and Classes
============================

This module provides utility functions and classes for the requirements analysis system:

- Enums: System-wide enumerations
- Exceptions: Custom exception classes
- JSON utilities: JSON processing functions
- File utilities: File handling functions
- Markdown converter: Convert data to markdown format
- Template manager: Template management utilities
"""

from .enums import (
    AgentRole,
    AgentStatus,
    LLMProvider,
    DocumentFormat,
    QualityMetric,
    RequirementType,
    RequirementPriority,
    RequirementStatus,
)
from .exceptions import (
    RequirementsAnalysisError,
    ConfigurationError,
    ValidationError,
    ExtractionError,
    AnalysisError,
    DocumentationError,
    QualityCheckError,
    TemplateError,
    LLMError,
)
from .json_utils import (
    load_json_safe,
    save_json_safe,
    validate_json_schema,
    extract_json_from_text,
    format_json_output,
)
from .file import (
    ensure_directory_exists,
    read_file_safe,
    write_file_safe,
    get_file_extension,
    list_files_by_extension,
)
from .markdown_converter import (
    RequirementsMarkdownConverter,
    convert_to_markdown,
)
from .template_manager import (
    TemplateManager,
    load_template,
    render_template,
)

__all__ = [
    # Enums
    "AgentRole",
    "AgentStatus",
    "LLMProvider",
    "DocumentFormat",
    "QualityMetric",
    "RequirementType",
    "RequirementPriority",
    "RequirementStatus",
    # Exceptions
    "RequirementsAnalysisError",
    "ConfigurationError",
    "ValidationError",
    "ExtractionError",
    "AnalysisError",
    "DocumentationError",
    "QualityCheckError",
    "TemplateError",
    "LLMError",
    # JSON utilities
    "load_json_safe",
    "save_json_safe",
    "validate_json_schema",
    "extract_json_from_text",
    "format_json_output",
    # File utilities
    "ensure_directory_exists",
    "read_file_safe",
    "write_file_safe",
    "get_file_extension",
    "list_files_by_extension",
    # Markdown converter
    "RequirementsMarkdownConverter",
    "convert_to_markdown",
    # Template manager
    "TemplateManager",
    "load_template",
    "render_template",
]
