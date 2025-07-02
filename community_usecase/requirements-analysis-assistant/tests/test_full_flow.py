"""Test full workflow."""

import os
import pytest
import logging
import json
from typing import Dict, Any
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from owl_requirements.services.llm import create_llm_service, LLMService
from owl_requirements.services.prompts import PromptManager
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.core.coordinator import AgentCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def base_dir() -> Path:
    """Get base directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def config(base_dir) -> Dict[str, Any]:
    """Create test configuration."""
    return {
        "name": "requirements_analysis_test",
        "llm": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "temperature": 0.1,
            "max_tokens": 4000,
            "api_key": os.getenv("DEEPSEEK_API_KEY")
        },
        "prompts": {
            "templates_dir": str(base_dir / "src" / "owl_requirements" / "services" / "templates")
        },
        "max_retries": 3
    }

@pytest.fixture
def extractor_config(config) -> Dict[str, Any]:
    """Create extractor configuration."""
    return {**config, "name": "requirements_extractor"}

@pytest.fixture
def analyzer_config(config) -> Dict[str, Any]:
    """Create analyzer configuration."""
    return {**config, "name": "requirements_analyzer"}

@pytest.fixture
def documenter_config(config) -> Dict[str, Any]:
    """Create documenter configuration."""
    return {**config, "name": "documentation_generator"}

@pytest.fixture
def quality_check_config(config) -> Dict[str, Any]:
    """Create quality check configuration."""
    return {**config, "name": "quality_check_agent"}

@pytest.fixture
def llm_quality_check_config(config) -> Dict[str, Any]:
    """Create LLM quality check configuration."""
    return {**config, "name": "quality_checker"}

@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock(spec=LLMService)
    mock.generate = AsyncMock()
    return mock

@pytest.fixture
def mock_prompt_manager():
    """Create mock prompt manager."""
    mock = Mock(spec=PromptManager)
    mock.get_template = Mock(side_effect=[
        # 需求提取模板
        {
            "template": "请分析以下需求文本并提取需求：\n\n{input_text}\n\n请按照以下格式返回JSON：\n{example_json}",
            "variables": ["input_text", "example_json"]
        },
        # 需求分析模板
        {
            "template": "请分析以下需求：\n\n{requirements}\n\n请提供详细的分析结果，包括可行性、风险、依赖等。",
            "variables": ["requirements"]
        },
        # 质量检查模板
        {
            "template": "请评估以下需求的质量：\n\n{requirements}\n\n请提供质量评分和改进建议。",
            "variables": ["requirements"]
        },
        # 文档生成模板
        {
            "template": "请根据以下信息生成需求规格说明书：\n\n需求：{requirements}\n分析：{analysis}\n质量评估：{quality_check}",
            "variables": ["requirements", "analysis", "quality_check"]
        }
    ])
    return mock

@pytest.fixture
def requirements_extractor(extractor_config, mock_llm_service, mock_prompt_manager):
    """Create requirements extractor instance."""
    return RequirementsExtractor(extractor_config, mock_llm_service, mock_prompt_manager)

@pytest.fixture
def requirements_analyzer(analyzer_config, mock_llm_service, mock_prompt_manager):
    """Create requirements analyzer instance."""
    return RequirementsAnalyzer(analyzer_config, mock_llm_service, mock_prompt_manager)

@pytest.fixture
def documentation_generator(documenter_config):
    """Create documentation generator instance."""
    return DocumentationGenerator(documenter_config, "test_output/docs")

@pytest.fixture
def mock_llm_checker():
    """Create mock quality checker."""
    mock = Mock(spec=QualityChecker)
    mock.process = AsyncMock(return_value={
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
                "consistency": 0.88,
                "testability": 0.87,
                "traceability": 0.86
            },
            "recommendations": [
                "添加具体的性能指标",
                "明确用户角色和权限"
            ]
        }
    })
    return mock

@pytest.fixture
def quality_check_agent(quality_check_config, mock_llm_checker):
    """Create quality check agent instance."""
    return QualityChecker(llm_service=mock_llm_checker, config=quality_check_config)

@pytest.fixture
def agent_coordinator(
    requirements_extractor,
    requirements_analyzer,
    documentation_generator,
    quality_check_agent
):
    """Create agent coordinator instance."""
    return AgentCoordinator(
        extractor=requirements_extractor,
        analyzer=requirements_analyzer,
        generator=documentation_generator,
        checker=quality_check_agent
    )

@pytest.fixture
def mock_requirements_result():
    """Create mock requirements extraction result."""
    return {
        "functional_requirements": [
            {
                "id": "F1",
                "category": "用户认证",
                "description": "系统应该支持用户登录",
                "priority": "high",
                "stakeholders": ["用户", "系统管理员"]
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NF1",
                "category": "performance",
                "description": "系统响应时间不超过500ms",
                "priority": "high",
                "constraints": ["服务器响应时间", "网络延迟"]
            }
        ]
    }

@pytest.fixture
def mock_analysis_result():
    """Create mock analysis result."""
    return {
        "分析结果": {
            "功能需求": [
                {
                    "需求": {
                        "编号": "F1",
                        "描述": "系统应该支持用户登录",
                        "优先级": "high",
                        "状态": "待实现"
                    },
                    "风险评估": {
                        "风险等级": "低",
                        "风险描述": "标准功能，实现风险较低"
                    }
                }
            ],
            "非功能需求": [
                {
                    "需求": {
                        "编号": "NF1",
                        "描述": "系统响应时间不超过500ms",
                        "类型": "性能",
                        "优先级": "high"
                    },
                    "实现难度": "中",
                    "依赖项": []
                }
            ],
            "总体评估": {
                "可行性": 0.8,
                "复杂度": "中",
                "工期估算": "2周"
            },
            "依赖分析": {
                "F1": {
                    "依赖层级": 1,
                    "依赖项": []
                }
            }
        }
    }

@pytest.fixture
def mock_quality_result():
    """Create mock quality check result."""
    return {
        "质量评分": 88,
        "维度得分": {
            "完整性": 0.9,
            "清晰度": 0.85,
            "可测试性": 0.89,
            "一致性": 0.87,
            "可行性": 0.86,
            "依赖关系": 0.88
        },
        "问题列表": [
            {
                "类型": "清晰度问题",
                "需求编号": "F1",
                "描述": "需求描述不够具体"
            }
        ],
        "改进建议": [
            "建议添加更详细的用户登录流程描述"
        ]
    }

@pytest.fixture
def mock_documentation_result():
    """Create mock documentation result."""
    return {
        "需求规格说明书": {
            "项目概述": "用户认证系统",
            "功能需求": [
                {
                    "编号": "F1",
                    "描述": "系统应该支持用户登录",
                    "详细说明": "...",
                    "验收标准": "..."
                }
            ],
            "非功能需求": [
                {
                    "编号": "NF1",
                    "描述": "系统响应时间不超过500ms",
                    "详细说明": "...",
                    "验收标准": "..."
                }
            ],
            "质量评估": {
                "总体评分": 88,
                "主要问题": "需求描述不够具体",
                "改进建议": "建议添加更详细的用户登录流程描述"
            }
        }
    }

@pytest.mark.asyncio
async def test_full_flow(coordinator):
    """Test full workflow."""
    input_text = "需要一个图书管理系统，包含图书借阅、归还、查询等基本功能"
    
    # Process requirements
    result = await coordinator.process_requirements(input_text)
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "requirements" in result
    assert "analysis" in result
    assert "quality_check" in result
    assert "documents" in result
    
    # Verify requirements
    requirements = result["requirements"]
    assert isinstance(requirements, dict)
    assert "functional_requirements" in requirements
    assert "non_functional_requirements" in requirements
    
    # Verify functional requirements
    func_reqs = requirements["functional_requirements"]
    assert any("借阅" in req["description"] for req in func_reqs)
    assert any("归还" in req["description"] for req in func_reqs)
    assert any("查询" in req["description"] for req in func_reqs)
    
    # Verify analysis
    analysis = result["analysis"]
    assert isinstance(analysis, dict)
    assert "feasibility" in analysis
    assert "risks" in analysis
    assert "dependencies" in analysis
    
    # Verify quality check
    quality_check = result["quality_check"]
    assert isinstance(quality_check, dict)
    assert "overall_score" in quality_check
    assert "issues" in quality_check
    assert "metrics" in quality_check
    assert "recommendations" in quality_check
    
    # Verify documents
    documents = result["documents"]
    assert isinstance(documents, dict)
    assert "requirements_doc" in documents
    assert "analysis_doc" in documents

@pytest.mark.asyncio
async def test_workflow_error_handling(
    config,
    mock_llm_service,
    mock_prompt_manager
):
    """Test error handling in the workflow."""
    # 配置mock抛出异常
    mock_llm_service.generate.side_effect = Exception("模拟的错误")
    
    # 初始化智能体
    extractor = RequirementsExtractor(config, mock_llm_service, mock_prompt_manager)
    
    # 测试错误处理
    with pytest.raises(Exception) as exc_info:
        await extractor.process({"input_text": "测试输入"})
    
    assert "模拟的错误" in str(exc_info.value)
    assert mock_llm_service.generate.call_count == 1

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 