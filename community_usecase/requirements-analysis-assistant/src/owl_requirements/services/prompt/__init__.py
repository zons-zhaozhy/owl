"""Prompt management system for the OWL Requirements Analysis system."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
from pathlib import Path

from ...core.config import SystemConfig


@dataclass
class PromptTemplate:
    """A template for generating prompts."""

    name: str
    template: str
    description: str
    variables: List[str]
    examples: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptManager:
    """Manages prompt templates and their rendering."""

    def __init__(self, config: SystemConfig):
        """Initialize the prompt manager.

        Args:
            config: System configuration
        """
        self.templates_dir = Path(config.templates_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from the templates directory."""
        if not self.templates_dir.exists():
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}"
            )

        for file in self.templates_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                template = PromptTemplate(
                    name=data["name"],
                    template=data["template"],
                    _description=data["description"],
                    variables=data["variables"],
                    _examples=data.get("examples"),
                    _metadata=data.get("metadata"),
                )
                self.templates[template.name] = template

    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name.

        Args:
            name: Name of the template to retrieve

        Returns:
            The requested template

        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            raise KeyError(f"Template not found: {name}")
        return self.templates[name]

    def render(self, template_name: str, variables: Dict[str, str]) -> str:
        """Render a prompt template with the given variables.

        Args:
            template_name: Name of the template to render
            variables: Dictionary of variables to substitute

        Returns:
            The rendered prompt

        Raises:
            KeyError: If template not found
            ValueError: If required variables are missing
        """
        template = self.get_template(template_name)

        # Verify all required variables are provided
        missing = set(template.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Render the template
        result = template.template
        for var, value in variables.items():
            result = result.replace(f"{{{var}}}", value)

        return result

    def list_templates(self) -> List[str]:
        """Get a list of all available template names.

        Returns:
            List of template names
        """
        return list(self.templates.keys())

    def reload_templates(self) -> None:
        """Reload all templates from disk."""
        self.templates.clear()
        self._load_templates()
