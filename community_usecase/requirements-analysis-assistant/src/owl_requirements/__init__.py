"""
OWL Requirements Analysis Assistant
==================================

A multi-agent system for intelligent requirements analysis and documentation.

This package provides:
- Requirements extraction from natural language
- Requirements analysis and validation
- Quality checking and assessment
- Automated documentation generation
- Multi-agent coordination system

Core Components:
- agents: Intelligent agents for different analysis tasks
- core: Core system components and coordination
- services: Service layer for LLM integration and utilities
- utils: Utility functions and helpers
- web: Web interface components
- cli: Command-line interface
"""

from typing import Dict, Any, Optional
import logging

# Version information
__version__ = "1.0.0"
__author__ = "OWL Framework Team"
__license__ = "MIT"

# Configure logging for the package
logger = logging.getLogger(__name__)

# Export main components for easy access
__all__ = [
    "__version__",
    "__author__",
    "__license__",
]


# Package initialization
def _initialize_package():
    """Initialize the package with default settings."""
    # Set up basic logging if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


# Initialize the package
_initialize_package()
