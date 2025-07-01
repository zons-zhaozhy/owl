import pytest
from unittest.mock import AsyncMock, MagicMock
import json
from src.extractors.requirements_extractor import RequirementsExtractor
from src.services.llm_service import LLMService, LLMResponse

@pytest.fixture
def llm_service():
    service = MagicMock(spec=LLMService)
    service.process_prompt = AsyncMock()
    return service

@pytest.fixture
def requirements_extractor(llm_service):
    return RequirementsExtractor(llm_service)

@pytest.mark.asyncio
async def test_extract_requirements(requirements_extractor, llm_service):
    # 准备测试数据
    test_requirements = {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Test requirement",
                "priority": "high",
                "acceptance_criteria": ["Test criteria"]
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_requirements),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.process_prompt.return_value = {
        "content": json.dumps(test_requirements),
        "finish_reason": "stop",
        "usage": {"total_tokens": 100}
    }
    
    # 执行测试
    result = await requirements_extractor.extract_requirements("Test input")
    
    # 验证结果
    assert result == test_requirements
    llm_service.process_prompt.assert_called_once()

@pytest.mark.asyncio
async def test_extract_requirements_invalid_json(requirements_extractor, llm_service):
    # 准备测试数据
    llm_service.process_prompt.return_value = {
        "content": "Invalid JSON"
    }
    
    # 执行测试
    result = await requirements_extractor.extract_requirements("Test input")
    
    # 验证结果
    assert "error" in result
    assert "Invalid JSON response" in result["error"]

@pytest.mark.asyncio
async def test_analyze_requirements(requirements_extractor, llm_service):
    # 准备测试数据
    test_requirements = {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Test requirement",
                "priority": "high",
                "acceptance_criteria": ["Criteria 1", "Criteria 2"]
            }
        ]
    }
    test_analysis = {
        "feasibility": "high",
        "risks": ["Risk 1", "Risk 2"],
        "dependencies": ["Dep 1", "Dep 2"]
    }
    test_diagrams = {
        "use_case": "```mermaid\nusecaseDiagram\n```",
        "data_flow": "```mermaid\nflowchart LR\n```",
        "state": "```mermaid\nstateDiagram-v2\n```",
        "sequence": "```mermaid\nsequenceDiagram\n```",
        "class": "```mermaid\nclassDiagram\n```"
    }
    
    # 设置模拟返回值
    llm_service.process_prompt.return_value = {
        "content": json.dumps(test_analysis)
    }
    
    # 执行测试
    result = await requirements_extractor.analyze_requirements(test_requirements)
    
    # 验证结果
    assert result["feasibility"] == test_analysis["feasibility"]
    assert result["risks"] == test_analysis["risks"]
    assert result["dependencies"] == test_analysis["dependencies"]
    assert "diagrams" in result
    assert "use_case" in result["diagrams"]
    assert "data_flow" in result["diagrams"]
    assert "state" in result["diagrams"]
    assert "sequence" in result["diagrams"]
    assert "class" in result["diagrams"]

@pytest.mark.asyncio
async def test_analyze_requirements_invalid_json(requirements_extractor, llm_service):
    # 准备测试数据
    test_requirements = {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Test requirement"
            }
        ]
    }
    llm_service.process_prompt.return_value = {
        "content": "Invalid JSON"
    }
    
    # 执行测试
    result = await requirements_extractor.analyze_requirements(test_requirements)
    
    # 验证结果
    assert "error" in result
    assert "Invalid JSON response from LLM" == result["error"]
    assert "diagrams" in result

@pytest.mark.asyncio
async def test_generate_markdown_report(requirements_extractor):
    # 准备测试数据
    test_requirements = {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "Test requirement",
                "priority": "high",
                "acceptance_criteria": ["Criteria 1", "Criteria 2"]
            }
        ]
    }
    test_analysis = {
        "feasibility": "high",
        "risks": ["Risk 1", "Risk 2"],
        "diagrams": {
            "use_case": "```mermaid\nusecaseDiagram\n```",
            "data_flow": "```mermaid\nflowchart LR\n```",
            "state": "```mermaid\nstateDiagram-v2\n```",
            "sequence": "```mermaid\nsequenceDiagram\n```",
            "class": "```mermaid\nclassDiagram\n```"
        }
    }
    
    # 执行测试
    result = await requirements_extractor.generate_markdown_report(
        test_requirements,
        test_analysis
    )
    
    # 验证结果
    assert "# 需求分析报告" in result
    assert "## 需求概述" in result
    assert "Test requirement" in result
    assert "Criteria 1" in result
    assert "Criteria 2" in result
    assert "## 分析结果" in result
    assert "可行性：high" in result
    assert "Risk 1" in result
    assert "Risk 2" in result
    assert "## UML 图" in result
    assert "### 用例图" in result
    assert "### 数据流图" in result
    assert "### 状态图" in result
    assert "### 时序图" in result
    assert "### 类图" in result 