"""Test requirements analyzer."""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.utils.exceptions import AnalysisError

@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "analysis": {
            "feasibility": {
                "score": 0.85,
                "factors": [
                    {
                        "name": "技术可行性",
                        "score": 0.9,
                        "details": "使用成熟的Web技术栈实现"
                    },
                    {
                        "name": "资源需求",
                        "score": 0.8,
                        "details": "需要专业的开发团队"
                    }
                ]
            },
            "complexity": {
                "score": 0.7,
                "factors": [
                    {
                        "name": "功能复杂度",
                        "score": 0.75,
                        "details": "核心功能相对简单"
                    },
                    {
                        "name": "技术复杂度",
                        "score": 0.65,
                        "details": "需要处理并发和安全问题"
                    }
                ]
            },
            "risks": [
                {
                    "id": "R-001",
                    "category": "技术风险",
                    "description": "数据安全性风险",
                    "impact": "high",
                    "mitigation": "实施严格的安全措施"
                }
            ],
            "dependencies": [
                {
                    "id": "D-001",
                    "type": "技术依赖",
                    "name": "数据库系统",
                    "description": "需要可靠的数据库系统"
                }
            ]
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """Create mock config."""
    return {
        "name": "requirements_analyzer",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }

@pytest.mark.asyncio
async def test_analyze_requirements_success(mock_llm_service, mock_config):
    """Test successful requirements analysis."""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
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
    
    result = await analyzer.process(requirements)
    
    assert isinstance(result, dict)
    assert "analysis" in result
    assert "feasibility" in result["analysis"]
    assert "complexity" in result["analysis"]
    assert "risks" in result["analysis"]
    assert "dependencies" in result["analysis"]

@pytest.mark.asyncio
async def test_analyze_requirements_empty_requirements(mock_llm_service, mock_config):
    """Test analysis with empty requirements."""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(AnalysisError):
        await analyzer.process({})

@pytest.mark.asyncio
async def test_analyze_requirements_invalid_requirements(mock_llm_service, mock_config):
    """Test analysis with invalid requirements."""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(AnalysisError):
        await analyzer.process({"invalid": "data"}) 