"""Tests for the prompt manager."""
import pytest
from datetime import datetime
import json
import tempfile
import os
from src.owl_requirements.services.prompt_manager import (
    PromptManager,
    PromptTemplate,
    PromptVersion,
    PromptValidation
)

# Test data
TEST_TEMPLATE = """
Given the following context and requirements text, extract and structure the requirements.

Context:
- Project: {project_name}
- Domain: {domain}

Requirements Text:
{requirements_text}

Please analyze the text and extract structured requirements.
"""

TEST_DESCRIPTION = "Template for requirements extraction"

@pytest.fixture
def prompt_manager():
    return PromptManager()

@pytest.fixture
def template_data():
    return {
        "name": "extract_requirements",
        "template": TEST_TEMPLATE,
        "description": TEST_DESCRIPTION,
        "variables": ["project_name", "domain", "requirements_text"],
        "required_variables": ["project_name", "requirements_text"]
    }

def test_add_template(prompt_manager, template_data):
    """Test adding a new template."""
    template = prompt_manager.add_template(**template_data)
    
    assert isinstance(template, PromptTemplate)
    assert template.name == template_data["name"]
    assert template.template == template_data["template"]
    assert template.description == template_data["description"]
    assert template.variables == template_data["variables"]
    assert template.required_variables == template_data["required_variables"]
    assert isinstance(template.version, PromptVersion)

def test_get_template_latest(prompt_manager, template_data):
    """Test getting the latest template version."""
    template1 = prompt_manager.add_template(**template_data)
    
    # Add another version
    template2 = prompt_manager.add_template(**template_data)
    
    # Get latest version
    latest = prompt_manager.get_template(template_data["name"])
    
    assert latest.version.version == template2.version.version

def test_get_template_specific_version(prompt_manager, template_data):
    """Test getting a specific template version."""
    template1 = prompt_manager.add_template(**template_data)
    template2 = prompt_manager.add_template(**template_data)
    
    # Get specific version
    result = prompt_manager.get_template(
        template_data["name"],
        version=template1.version.version
    )
    
    assert result.version.version == template1.version.version

def test_get_template_not_found(prompt_manager):
    """Test getting a non-existent template."""
    with pytest.raises(ValueError, match="Template not found"):
        prompt_manager.get_template("nonexistent")

def test_get_template_version_not_found(prompt_manager, template_data):
    """Test getting a non-existent template version."""
    prompt_manager.add_template(**template_data)
    
    with pytest.raises(ValueError, match="Version not found"):
        prompt_manager.get_template(template_data["name"], version="nonexistent")

def test_render_prompt_success(prompt_manager, template_data):
    """Test successful prompt rendering."""
    prompt_manager.add_template(**template_data)
    
    variables = {
        "project_name": "Test Project",
        "domain": "Test Domain",
        "requirements_text": "Test requirements"
    }
    
    result = prompt_manager.render_prompt(template_data["name"], variables)
    
    assert "Test Project" in result
    assert "Test Domain" in result
    assert "Test requirements" in result

def test_render_prompt_missing_required_variable(prompt_manager, template_data):
    """Test prompt rendering with missing required variable."""
    prompt_manager.add_template(**template_data)
    
    variables = {
        "domain": "Test Domain",
        "requirements_text": "Test requirements"
    }
    
    with pytest.raises(ValueError, match="Missing required variables"):
        prompt_manager.render_prompt(template_data["name"], variables)

def test_render_prompt_unknown_variable(prompt_manager, template_data):
    """Test prompt rendering with unknown variable."""
    prompt_manager.add_template(**template_data)
    
    variables = {
        "project_name": "Test Project",
        "domain": "Test Domain",
        "requirements_text": "Test requirements",
        "unknown": "Unknown"
    }
    
    validation = prompt_manager._validate_variables(
        prompt_manager.get_template(template_data["name"]),
        variables
    )
    
    assert "Unknown variable: unknown" in validation.warnings

def test_export_import_templates(prompt_manager, template_data):
    """Test exporting and importing templates."""
    template = prompt_manager.add_template(**template_data)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # Export templates
        prompt_manager.export_templates(f.name)
        
        # Create new manager
        new_manager = PromptManager()
        
        # Import templates
        new_manager.import_templates(f.name)
        
        # Verify imported template
        imported = new_manager.get_template(template_data["name"])
        assert imported.name == template.name
        assert imported.template == template.template
        assert imported.description == template.description
        
    # Clean up
    os.unlink(f.name)

def test_delete_template_version(prompt_manager, template_data):
    """Test deleting a specific template version."""
    template1 = prompt_manager.add_template(**template_data)
    template2 = prompt_manager.add_template(**template_data)
    
    # Delete first version
    prompt_manager.delete_template(
        template_data["name"],
        version=template1.version.version
    )
    
    # Verify only second version remains
    templates = prompt_manager.templates[template_data["name"]]
    assert len(templates) == 1
    assert templates[0].version.version == template2.version.version

def test_delete_template_all_versions(prompt_manager, template_data):
    """Test deleting all versions of a template."""
    prompt_manager.add_template(**template_data)
    prompt_manager.add_template(**template_data)
    
    # Delete all versions
    prompt_manager.delete_template(template_data["name"])
    
    # Verify template is removed
    assert template_data["name"] not in prompt_manager.templates

def test_list_templates(prompt_manager, template_data):
    """Test listing all templates."""
    template = prompt_manager.add_template(**template_data)
    
    result = prompt_manager.list_templates()
    
    assert template_data["name"] in result
    assert len(result[template_data["name"]]) == 1
    assert result[template_data["name"]][0]["version"] == template.version.version
    assert result[template_data["name"]][0]["description"] == template.description 