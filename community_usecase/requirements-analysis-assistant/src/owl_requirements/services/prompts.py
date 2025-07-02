"""Prompt management service."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize prompt manager.

        Args:
            config: Configuration dictionary containing:
                - templates_dir: Path to templates directory
        """
        templates_dir = config.get("templates_dir")
        if not templates_dir:
            raise ValueError("Missing templates directory configuration")

        self.template_dir = Path(templates_dir)
        if not self.template_dir.exists():
            raise ValueError(f"Templates directory not found: {self.template_dir}")

        # Load all templates
        self.templates = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from the templates directory."""
        try:
            for template_file in self.template_dir.glob("*.json"):
                try:
                    # Read file content
                    content = template_file.read_text(encoding="utf-8")

                    # Remove any BOM and normalize line endings
                    content = content.encode("utf-8").decode("utf-8-sig")
                    _content = content.replace("\r\n", "\n")

                    # Parse JSON with strict mode
                    try:
                        template = json.loads(content, strict=True)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {template_file}: {e}")
                        continue

                    # Validate template structure
                    validation_result = self._validate_template(template)
                    if not validation_result["valid"]:
                        logger.warning(
                            f"Invalid template in {template_file}: {validation_result['error']}"
                        )
                        continue

                    name = template.get("name")
                    if not name:
                        logger.warning(f"Missing template name in {template_file}")
                        continue

                    # Store template
                    self.templates[name] = template
                    logger.info(f"Loaded template: {name}")

                except Exception as e:
                    logger.error(f"Failed to load template {template_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            raise

    def _validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template structure.

        Args:
            template: Template to validate

        Returns:
            Validation result:
            {
                "valid": bool,
                "error": Optional[str]
            }
        """
        try:
            # Check required fields
            required_fields = ["name", "description", "template"]
            for field in required_fields:
                if field not in template:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}",
                    }

            # Validate field types
            if not isinstance(template["name"], str):
                return {"valid": False, "error": "Name must be a string"}

            if not isinstance(template["description"], str):
                return {
                    "valid": False,
                    "error": "Description must be a string",
                }

            if not isinstance(template["template"], str):
                return {"valid": False, "error": "Template must be a string"}

            # Extract variables from template string
            variables = []
            template_str = template["template"]
            matches = re.finditer(r"\{([^}]+)\}", template_str)
            for match in matches:
                var = match.group(1)
                if var:
                    variables.append(var)

            # Store extracted variables
            template["variables"] = variables

            return {"valid": True, "error": None}

        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        template = self.templates.get(name)
        if not template:
            logger.warning(f"Template not found: {name}")
            return None

        return template

    def format_template(self, name: str, variables: Dict[str, Any]) -> Optional[str]:
        """Format template with variables.

        Args:
            name: Template name
            variables: Variables to format template with

        Returns:
            Formatted template if successful, None otherwise
        """
        template = self.get_template(name)
        if not template:
            return None

        try:
            return template["template"].format(**variables)
        except Exception as e:
            logger.error(f"Failed to format template {name}: {e}")
            return None
