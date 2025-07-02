"""Tests for documentation generator agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.core.config import SystemConfig, AgentConfig
from owl_requirements.utils.enums import AgentRole

@pytest.fixture
def mock_system_config():
    """Create mock system configuration."""
    config = MagicMock(spec=SystemConfig)
    config.agents = {
        "documentation_generator": AgentConfig(
            name="documentation_generator",
            description="文档生成智能体",
            role=AgentRole.DOCUMENTATION_GENERATOR,
            prompt_template="测试提示模板 {analysis_results}"
        )
    }
    return config

@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value="项目概述\n项目背景\n\n需求清单\n功能需求\n\n技术方案\n系统架构")
    return service

@pytest.fixture
def documentation_generator(mock_system_config, mock_llm_service):
    """Create documentation generator instance."""
    return DocumentationGenerator(mock_system_config, mock_llm_service)

@pytest.mark.asyncio
async def test_process_valid_input(documentation_generator):
    """Test processing valid input data."""
    # 准备测试数据
    test_input = {
        "requirements": {
            "functional_requirements": ["需求1", "需求2"],
            "non_functional_requirements": ["性能要求"],
            "constraints": ["约束1"]
        },
        "analysis": {
            "technical_feasibility": ["可行1", "可行2"],
            "resource_requirements": ["资源1"],
            "risk_analysis": ["风险1"]
        },
        "quality_check": {
            "issues": ["问题1"],
            "recommendations": ["建议1"]
        }
    }
    
    # 执行处理
    result = await documentation_generator.process(test_input)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "project_overview" in result
    assert "requirements_list" in result
    assert "technical_solution" in result
    assert "implementation_plan" in result
    assert "risk_management" in result

@pytest.mark.asyncio
async def test_format_analysis_results(documentation_generator):
    """Test formatting analysis results."""
    # 准备测试数据
    test_input = {
        "requirements": {
            "functional_requirements": ["需求1"],
            "non_functional_requirements": ["性能要求"],
            "constraints": ["约束1"]
        }
    }
    
    # 执行格式化
    result = documentation_generator._format_analysis_results(test_input)
    
    # 验证结果
    assert isinstance(result, str)
    assert "原始需求:" in result
    assert "需求1" in result
    assert "性能要求" in result
    assert "约束1" in result

@pytest.mark.asyncio
async def test_parse_response(documentation_generator):
    """Test parsing LLM response."""
    # 准备测试响应
    test_response = """
    项目概述
    背景说明
    项目目标
    
    需求清单
    功能需求1
    功能需求2
    
    技术方案
    架构设计
    
    实现计划
    阶段1
    阶段2
    
    风险管理
    风险1
    风险2
    """
    
    # 执行解析
    result = documentation_generator._parse_response(test_response)
    
    # 验证结果
    assert isinstance(result, dict)
    assert len(result["project_overview"]) > 0
    assert len(result["requirements_list"]) > 0
    assert len(result["technical_solution"]) > 0
    assert len(result["implementation_plan"]) > 0
    assert len(result["risk_management"]) > 0

@pytest.mark.asyncio
async def test_process_empty_input(documentation_generator):
    """Test processing empty input data."""
    # 准备空输入
    empty_input = {}
    
    # 执行处理
    result = await documentation_generator.process(empty_input)
    
    # 验证结果
    assert isinstance(result, dict)
    assert all(isinstance(section, list) for section in result.values())

@pytest.mark.asyncio
async def test_process_partial_input(documentation_generator):
    """Test processing partial input data."""
    # 准备部分输入
    partial_input = {
        "requirements": {
            "functional_requirements": ["需求1"]
        }
    }
    
    # 执行处理
    result = await documentation_generator.process(partial_input)
    
    # 验证结果
    assert isinstance(result, dict)
    assert all(isinstance(section, list) for section in result.values()) 