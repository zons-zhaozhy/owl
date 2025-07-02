"""
文档生成器测试模块
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.utils.exceptions import DocumentationError

@pytest.fixture
def mock_llm_service():
    """创建模拟的 LLM 服务"""
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
                        "系统验证用户名和密码的正确性",
                        "登录成功后跳转到主页面"
                    ]
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "category": "性能",
                    "description": "系统响应时间应在2秒内",
                    "acceptance_criteria": [
                        "95%的请求响应时间不超过2秒",
                        "99%的请求响应时间不超过5秒"
                    ]
                }
            ]
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """创建模拟的配置"""
    return {
        "name": "documentation_generator",
        "max_retries": 3,
        "timeout": 10,
        "output_format": "markdown"
    }

@pytest.mark.asyncio
async def test_generate_documentation_success(mock_llm_service, mock_config):
    """测试文档生成成功场景"""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    requirements = {
        "project_name": "图书管理系统",
        "version": "1.0.0",
        "requirements": {
            "functional": [
                {
                    "id": "FR-001",
                    "title": "用户登录",
                    "description": "用户可以使用用户名和密码登录系统"
                }
            ],
            "non_functional": [
                {
                    "id": "NFR-001",
                    "category": "性能",
                    "description": "系统响应时间应在2秒内"
                }
            ]
        }
    }
    
    result = await generator.process(requirements)
    
    assert isinstance(result, dict)
    assert "documentation" in result
    assert "overview" in result["documentation"]
    assert "functional_requirements" in result["documentation"]
    assert "non_functional_requirements" in result["documentation"]

@pytest.mark.asyncio
async def test_generate_documentation_empty_requirements(mock_llm_service, mock_config):
    """测试空需求场景"""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({})

@pytest.mark.asyncio
async def test_generate_documentation_invalid_requirements(mock_llm_service, mock_config):
    """测试无效需求场景"""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({"invalid": "data"}) 