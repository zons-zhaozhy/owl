"""
质量检查智能体测试模块
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.utils.exceptions import QualityCheckError

@pytest.fixture
def mock_llm_service():
    """创建模拟的 LLM 服务"""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "quality_check": {
            "overall_score": 85,
            "issues": [
                {
                    "id": "QC-001",
                    "requirement_id": "FR-001",
                    "type": "清晰度",
                    "severity": "中",
                    "description": "需求描述不够具体",
                    "suggestion": "添加更具体的功能描述"
                }
            ],
            "metrics": {
                "clarity": 0.85,
                "completeness": 0.90,
                "testability": 0.80
            },
            "recommendations": [
                "建议添加更多具体的功能描述",
                "建议添加验收标准"
            ]
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """创建模拟的配置"""
    return {
        "name": "quality_checker",
        "max_retries": 3,
        "timeout": 10
    }

@pytest.mark.asyncio
async def test_quality_check_success(mock_llm_service, mock_config):
    """测试质量检查成功场景"""
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    requirements = {
        "functional_requirements": [
            {
                "id": "FR-001",
                "title": "用户登录",
                "description": "用户可以使用用户名和密码登录系统"
            }
        ],
        "non_functional_requirements": []
    }
    
    result = await checker.process(requirements)
    
    assert isinstance(result, dict)
    assert "quality_check" in result
    assert "overall_score" in result["quality_check"]
    assert "issues" in result["quality_check"]
    assert "metrics" in result["quality_check"]
    assert "recommendations" in result["quality_check"]

@pytest.mark.asyncio
async def test_quality_check_empty_requirements(mock_llm_service, mock_config):
    """测试空需求场景"""
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(QualityCheckError):
        await checker.process({})

@pytest.mark.asyncio
async def test_quality_check_invalid_requirements(mock_llm_service, mock_config):
    """测试无效需求场景"""
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(QualityCheckError):
        await checker.process({"invalid": "data"}) 