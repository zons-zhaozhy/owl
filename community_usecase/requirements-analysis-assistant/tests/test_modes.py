"""Test all three modes of the requirements analysis assistant."""

import asyncio
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
from fastapi.testclient import TestClient
import os

from owl_requirements.core.config import SystemConfig
from owl_requirements.core.coordinator import AgentCoordinator
from owl_requirements.web.app import create_web_app
from owl_requirements.cli.app import create_cli_app
from owl_requirements.services.llm import create_llm_service, LLMConfig, LLMProvider
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.agents.documentation_generator import DocumentationGenerator

@pytest.fixture
def config():
    """Create test configuration."""
    # 使用实际的DeepSeek配置，确保DEEPSEEK_API_KEY已设置
    return SystemConfig(
        templates_dir=Path(__file__).parent.parent / "templates",
        llm_provider=LLMProvider.DEEPSEEK.value, # 确保传递字符串值
        llm_model="deepseek-chat",
        llm_api_key=os.getenv("DEEPSEEK_API_KEY", ""), # 从环境变量获取API Key
        llm_temperature=0.1,
        llm_max_tokens=2000
    )

@pytest.fixture
def llm_service(config):
    """Create DeepSeek LLM service."""
    llm_config = LLMConfig(
        provider=LLMProvider(config.llm_provider), # 将字符串转换为枚举成员
        model=config.llm_model,
        api_key=config.llm_api_key,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens
    )
    return create_llm_service(llm_config)

@pytest.fixture
def coordinator(llm_service, config):
    """Create agent coordinator."""
    return AgentCoordinator(
        extractor=RequirementsExtractor(llm_service, config),
        analyzer=RequirementsAnalyzer(llm_service, config),
        checker=QualityChecker(llm_service, config),
        generator=DocumentationGenerator(llm_service, config)
    )

@pytest.mark.asyncio
async def test_web_mode(coordinator, config):
    """Test web mode."""
    app = create_web_app(coordinator, config)
    client = TestClient(app)
    
    # 测试初始请求
    response = client.post("/api/analyze", json={
        "text": "需要一个用户认证系统"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["needs_clarification"] is True
    assert "clarification" in data
    assert data["clarification"]["question"] == "系统需要支持哪些认证方式？"
    
    # 测试澄清回答
    session_id = data["session_id"]
    response = client.post("/api/analyze", json={
        "session_id": session_id,
        "text": "用户名密码"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_complete"] is True
    assert "analysis" in data

@pytest.mark.asyncio
async def test_cli_mode(coordinator, config):
    """Test CLI mode."""
    app = create_cli_app(coordinator, config)
    
    # 模拟CLI输入
    inputs = [
        "需要一个用户认证系统",
        "用户名密码"
    ]
    outputs = []
    
    def mock_input(_):
        return inputs.pop(0) if inputs else ""
    
    def mock_print(text):
        outputs.append(text)
    
    # 运行CLI应用
    await app.run(input_func=mock_input, print_func=mock_print)
    
    # 验证输出
    assert any("需要澄清" in out for out in outputs)
    assert any("分析完成" in out for out in outputs)

@pytest.mark.asyncio
async def test_once_mode(coordinator, config):
    """Test once mode."""
    result = await coordinator.process_input(
        session_id=coordinator.create_dialogue_session(),
        input_text="需要一个用户认证系统"
    )
    
    # 验证需要澄清
    assert result["needs_clarification"] is True
    assert "clarification" in result
    
    # 提供澄清答案
    result = await coordinator.process_input(
        session_id=result["session_id"],
        input_text="用户名密码"
    )
    
    # 验证完成分析
    assert result["is_complete"] is True
    assert "analysis" in result 