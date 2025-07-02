"""Enums for the OWL requirements analysis system."""

from enum import Enum

class AgentRole(str, Enum):
    """Agent roles in the system."""
    REQUIREMENTS_EXTRACTOR = "requirements_extractor"
    REQUIREMENTS_ANALYZER = "requirements_analyzer"
    DOCUMENT_GENERATOR = "document_generator"
    QUALITY_CHECKER = "quality_checker"
    COORDINATOR = "coordinator" 