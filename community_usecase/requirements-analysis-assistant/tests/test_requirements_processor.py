"""Tests for the requirements processor."""
import pytest
from unittest.mock import AsyncMock, MagicMock
import json
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from owl_requirements.services.requirements import (
    RequirementsProcessor,
    RequirementType,
    RequirementPriority,
    RequirementStatus,
    Requirement,
    RequirementsContext,
    RequirementsValidation,
    ProcessingResult
)
from owl_requirements.services.llm import LLMService, LLMResponse

# Test data
TEST_REQUIREMENTS_TEXT = """
需要一个基于Python的Web应用，用于管理个人任务清单。
功能包括：
1. 添加、编辑、删除任务
2. 设置任务优先级和截止日期
3. 标记任务完成状态
4. 按不同条件筛选和排序任务
5. 支持任务标签和分类
"""

TEST_CONTEXT = RequirementsContext(
    project_name="Task Manager",
    domain="Web Application",
    stakeholders=["Product Manager", "Developer", "User"],
    constraints={
        "technology": "Python",
        "deployment": "Web-based",
        "timeline": "3 months"
    }
)

TEST_REQUIREMENTS = [
    {
        "id": "REQ-001",
        "type": "functional",
        "title": "Task CRUD Operations",
        "description": "Users can add, edit, and delete tasks",
        "priority": "high",
        "dependencies": [],
        "tags": ["core", "task-management"]
    },
    {
        "id": "REQ-002",
        "type": "functional",
        "title": "Task Priority Management",
        "description": "Users can set and modify task priorities",
        "priority": "medium",
        "dependencies": ["REQ-001"],
        "tags": ["task-management"]
    }
]

@pytest.fixture
def llm_service():
    service = MagicMock(spec=LLMService)
    service.get_json_completion = AsyncMock(return_value=(
        {"requirements": TEST_REQUIREMENTS},
        LLMResponse(
            content=json.dumps({"requirements": TEST_REQUIREMENTS}),
            tokens_used=100,
            finish_reason="stop",
            model="test-model"
        )
    ))
    return service

@pytest.fixture
def processor(llm_service):
    return RequirementsProcessor(llm_service=llm_service)

@pytest.mark.asyncio
async def test_process_requirements_success(processor):
    """Test successful requirements processing."""
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert len(result.requirements) == 2
    assert result.requirements[0].id == "REQ-001"
    assert result.requirements[0].type == RequirementType.FUNCTIONAL
    assert result.requirements[0].priority == RequirementPriority.HIGH
    assert result.validation.is_valid is True

@pytest.mark.asyncio
async def test_process_requirements_validation_issues(processor, llm_service):
    """Test requirements processing with validation issues."""
    # Modify test data to include duplicate IDs
    duplicate_reqs = TEST_REQUIREMENTS.copy()
    duplicate_reqs.append(TEST_REQUIREMENTS[0].copy())
    
    llm_service.get_json_completion = AsyncMock(return_value=(
        {"requirements": duplicate_reqs},
        LLMResponse(
            content=json.dumps({"requirements": duplicate_reqs}),
            tokens_used=100,
            finish_reason="stop",
            model="test-model"
        )
    ))
    
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert result.validation.is_valid is False
    assert "Duplicate requirement IDs found" in result.validation.issues

@pytest.mark.asyncio
async def test_process_requirements_missing_dependencies(processor, llm_service):
    """Test requirements processing with missing dependencies."""
    # Modify test data to include missing dependency
    reqs_with_missing_dep = TEST_REQUIREMENTS.copy()
    reqs_with_missing_dep[1]["dependencies"] = ["REQ-999"]
    
    llm_service.get_json_completion = AsyncMock(return_value=(
        {"requirements": reqs_with_missing_dep},
        LLMResponse(
            content=json.dumps({"requirements": reqs_with_missing_dep}),
            tokens_used=100,
            finish_reason="stop",
            model="test-model"
        )
    ))
    
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert any("missing dependency" in warning for warning in result.validation.warnings)

@pytest.mark.asyncio
async def test_process_requirements_circular_dependencies(processor, llm_service):
    """Test requirements processing with circular dependencies."""
    # Create requirements with circular dependencies
    circular_reqs = [
        {
            "id": "REQ-001",
            "type": "functional",
            "title": "Requirement 1",
            "description": "Description 1",
            "priority": "high",
            "dependencies": ["REQ-002"]
        },
        {
            "id": "REQ-002",
            "type": "functional",
            "title": "Requirement 2",
            "description": "Description 2",
            "priority": "high",
            "dependencies": ["REQ-001"]
        }
    ]
    
    llm_service.get_json_completion = AsyncMock(return_value=(
        {"requirements": circular_reqs},
        LLMResponse(
            content=json.dumps({"requirements": circular_reqs}),
            tokens_used=100,
            finish_reason="stop",
            model="test-model"
        )
    ))
    
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert result.validation.is_valid is False
    assert "Circular dependencies detected" in result.validation.issues

@pytest.mark.asyncio
async def test_process_requirements_llm_validation_failure(processor, llm_service):
    """Test requirements processing with LLM validation failure."""
    # First call succeeds, second call (validation) fails
    llm_service.get_json_completion = AsyncMock(side_effect=[
        (
            {"requirements": TEST_REQUIREMENTS},
            LLMResponse(
                content=json.dumps({"requirements": TEST_REQUIREMENTS}),
                tokens_used=100,
                finish_reason="stop",
                model="test-model"
            )
        ),
        Exception("LLM validation failed")
    ])
    
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert "LLM validation failed" in result.validation.warnings

@pytest.mark.asyncio
async def test_process_requirements_invalid_requirement_data(processor, llm_service):
    """Test requirements processing with invalid requirement data."""
    # Create invalid requirement data
    invalid_req = {
        "id": "REQ-001",
        "type": "invalid_type",  # Invalid type
        "title": "Test Requirement",
        "description": "Test Description",
        "priority": "super_high"  # Invalid priority
    }
    
    llm_service.get_json_completion = AsyncMock(return_value=(
        {"requirements": [invalid_req]},
        LLMResponse(
            content=json.dumps({"requirements": [invalid_req]}),
            tokens_used=100,
            finish_reason="stop",
            model="test-model"
        )
    ))
    
    result = await processor.process_requirements(
        TEST_REQUIREMENTS_TEXT,
        TEST_CONTEXT
    )
    
    assert isinstance(result, ProcessingResult)
    assert len(result.requirements) == 0  # Invalid requirement should be skipped
    assert result.validation.is_valid is False
    assert "No requirements found" in result.validation.issues 