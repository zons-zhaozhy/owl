"""Test documentation generation."""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.utils.exceptions import DocumentationError

@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "documentation": {
            "overview": "图书管理系统概述",
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "用户登录",
                    "description": "系统应支持用户通过用户名和密码登录",
                    "acceptance_criteria": [
                        "用户可以输入用户名和密码",
                        "系统验证用户凭据",
                        "登录成功后跳转到主页"
                    ]
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "category": "性能",
                    "description": "系统响应时间应在2秒内",
                    "metrics": [
                        "95%的请求响应时间<2秒",
                        "99%的请求响应时间<5秒"
                    ]
                }
            ],
            "architecture": {
                "overview": "系统采用三层架构",
                "components": [
                    "前端界面层",
                    "业务逻辑层",
                    "数据访问层"
                ]
            }
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """Create mock config."""
    return {
        "name": "documentation_generator",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }

@pytest.mark.asyncio
async def test_generate_documentation_success(mock_llm_service, mock_config):
    """Test successful documentation generation."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    requirements = {
        "functional_requirements": [
            {
                "id": "FR-001",
                "description": "系统应支持用户登录功能",
                "priority": "high"
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-001",
                "category": "性能",
                "description": "系统响应时间应在2秒内"
            }
        ]
    }
    
    result = await generator.process(requirements)
    
    assert isinstance(result, dict)
    assert "documentation" in result
    assert "overview" in result["documentation"]
    assert "functional_requirements" in result["documentation"]
    assert "non_functional_requirements" in result["documentation"]
    assert "architecture" in result["documentation"]

@pytest.mark.asyncio
async def test_generate_documentation_empty_requirements(mock_llm_service, mock_config):
    """Test documentation generation with empty requirements."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({})

@pytest.mark.asyncio
async def test_generate_documentation_invalid_requirements(mock_llm_service, mock_config):
    """Test documentation generation with invalid requirements."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({"invalid": "data"}) 