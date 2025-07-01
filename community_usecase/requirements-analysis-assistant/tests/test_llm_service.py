"""Tests for the LLM service."""

import os
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
from owl_requirements.services.llm import LLMService, LLMConfig, LLMProvider, LLMResponse
from owl_requirements.core.settings import DEEPSEEK_SETTINGS
from owl_requirements.core.config import Config

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

TEST_REQUIREMENTS = {
    "functional": [
        {
            "id": "F1",
            "title": "Task Management",
            "description": "Users can add, edit, and delete tasks",
            "priority": "high"
        }
    ],
    "non_functional": [
        {
            "id": "NF1",
            "title": "Performance",
            "description": "System should respond within 1 second",
            "priority": "medium"
        }
    ]
}

TEST_ANALYSIS = {
    "validation_results": {
        "valid": True,
        "issues": []
    },
    "risks": [],
    "dependencies": {}
}

TEST_DOCS = {
    "requirements_spec": "# Requirements Specification\n...",
    "technical_spec": "# Technical Specification\n...",
    "implementation_guide": "# Implementation Guide\n...",
    "test_plan": "# Test Plan\n..."
}

@pytest.fixture
def config():
    return MagicMock(spec=Config)

@pytest.fixture
def llm_service():
    service = LLMService()
    service.api_key = "test_key"
    service.api_base = "https://api.deepseek.com/v1"
    service.model = "deepseek-chat"
    service.temperature = 0.05
    service.max_tokens = 4096
    return service

@pytest.fixture
def mock_response():
    return {
        "id": "cmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "deepseek-chat",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Test response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@pytest.mark.asyncio
async def test_process_prompt(llm_service, mock_response):
    """Test processing a prompt."""
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value=mock_response)
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        response = await llm_service._make_request("Test prompt")
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.tokens_used == 30
        assert response.finish_reason == "stop"
        assert response.model == "deepseek-chat"

@pytest.mark.asyncio
async def test_extract_requirements(llm_service, mock_response):
    """Test requirements extraction."""
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": json.dumps(TEST_REQUIREMENTS)},
                    "finish_reason": "stop"
                }
            ],
            "usage": None
        })
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        result = await llm_service.extract_requirements(TEST_REQUIREMENTS_TEXT)
        assert "functional" in result
        assert "non_functional" in result
        assert len(result["functional"]) > 0
        assert len(result["non_functional"]) > 0

@pytest.mark.asyncio
async def test_analyze_requirements(llm_service, mock_response):
    """Test requirements analysis."""
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": json.dumps(TEST_ANALYSIS)},
                    "finish_reason": "stop"
                }
            ],
            "usage": None
        })
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        result = await llm_service.analyze_requirements(TEST_REQUIREMENTS)
        assert "validation_results" in result
        assert "risks" in result
        assert "dependencies" in result
        assert result["validation_results"]["valid"] is True

@pytest.mark.asyncio
async def test_generate_documentation(llm_service, mock_response):
    """Test documentation generation."""
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": json.dumps(TEST_DOCS)},
                    "finish_reason": "stop"
                }
            ],
            "usage": None
        })
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        result = await llm_service.generate_documentation(TEST_REQUIREMENTS, TEST_ANALYSIS)
        assert "requirements_spec" in result
        assert "technical_spec" in result
        assert "implementation_guide" in result
        assert "test_plan" in result

@pytest.mark.asyncio
async def test_check_quality(llm_service, mock_response):
    """Test quality checking."""
    mock_quality = {
        "metrics": {
            "completeness": 0.95,
            "clarity": 0.90,
            "consistency": 0.85,
            "testability": 0.80
        },
        "issues": []
    }
    
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": json.dumps(mock_quality)},
                    "finish_reason": "stop"
                }
            ],
            "usage": None
        })
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        result = await llm_service.check_quality(TEST_REQUIREMENTS, TEST_DOCS)
        assert "metrics" in result
        assert "issues" in result
        assert len(result["metrics"]) > 0

@pytest.mark.asyncio
async def test_error_handling(llm_service):
    """Test error handling."""
    async def mock_post(*args, **kwargs):
        raise aiohttp.ClientError("Test error")

    with patch("aiohttp.ClientSession.post", new=mock_post):
        with pytest.raises(Exception):
            await llm_service._make_request("Test prompt")

@pytest.mark.asyncio
async def test_json_parsing_error(llm_service, mock_response):
    """Test handling of JSON parsing errors."""
    async def mock_post(*args, **kwargs):
        mock = AsyncMock()
        mock.status = 200
        mock.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": "Invalid JSON"},
                    "finish_reason": "stop"
                }
            ],
            "usage": None
        })
        mock.raise_for_status = AsyncMock()
        return mock

    with patch("aiohttp.ClientSession.post", new=mock_post):
        result = await llm_service.extract_requirements(TEST_REQUIREMENTS_TEXT)
        assert "error" in result
        assert "raw_response" in result

@pytest.mark.asyncio
async def test_token_counting(llm_service):
    text = "Test text"
    token_count = llm_service.count_tokens(text)
    assert isinstance(token_count, int)
    assert token_count > 0

@pytest.mark.asyncio
async def test_max_tokens_validation(llm_service):
    long_text = "test " * 2000  # Create a very long text
    with pytest.raises(ValueError, match="输入token数.*超过限制"):
        await llm_service._make_request(long_text) 