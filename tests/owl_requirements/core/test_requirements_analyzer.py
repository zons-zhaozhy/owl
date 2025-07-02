"""
需求分析器测试模块
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.utils.exceptions import AnalysisError

@pytest.fixture
def mock_llm_service():
    """创建模拟的 LLM 服务"""
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
                        "name": "资源可行性",
                        "score": 0.8,
                        "details": "需要3-4人的开发团队，开发周期约2个月"
                    }
                ]
            },
            "risks": [
                {
                    "id": "RISK-001",
                    "type": "技术风险",
                    "level": "低",
                    "description": "使用成熟技术栈，风险可控"
                }
            ],
            "dependencies": [
                {
                    "id": "DEP-001",
                    "from": "FR-001",
                    "to": "FR-002",
                    "type": "强依赖",
                    "description": "用户登录功能依赖于用户管理功能"
                }
            ]
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """创建模拟的配置"""
    return {
        "name": "requirements_analyzer",
        "max_retries": 3,
        "timeout": 10
    }

@pytest.mark.asyncio
async def test_analyze_requirements_success(mock_llm_service, mock_config):
    """测试需求分析成功场景"""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
    requirements = {
        "project_name": "图书管理系统",
        "version": "1.0.0",
        "requirements": {
            "functional": [
                {
                    "id": "FR-001",
                    "title": "用户登录",
                    "description": "用户可以使用用户名和密码登录系统"
                },
                {
                    "id": "FR-002",
                    "title": "用户管理",
                    "description": "管理员可以创建、修改、删除用户账号"
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
    
    result = await analyzer.process(requirements)
    
    assert isinstance(result, dict)
    assert "analysis" in result
    assert "feasibility" in result["analysis"]
    assert "risks" in result["analysis"]
    assert "dependencies" in result["analysis"]

@pytest.mark.asyncio
async def test_analyze_requirements_empty_requirements(mock_llm_service, mock_config):
    """测试空需求场景"""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(AnalysisError):
        await analyzer.process({})

@pytest.mark.asyncio
async def test_analyze_requirements_invalid_requirements(mock_llm_service, mock_config):
    """测试无效需求场景"""
    analyzer = RequirementsAnalyzer(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(AnalysisError):
        await analyzer.process({"invalid": "data"}) 