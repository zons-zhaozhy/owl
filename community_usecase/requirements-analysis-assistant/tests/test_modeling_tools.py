import pytest
from unittest.mock import AsyncMock, MagicMock
from owl_requirements.utils.modeling_tools import ModelingTools
from owl_requirements.services.llm import LLMService, LLMResponse
import json

@pytest.fixture
def llm_service():
    service = MagicMock(spec=LLMService)
    service.get_json_completion = AsyncMock()
    return service

@pytest.fixture
def modeling_tools(llm_service):
    return ModelingTools(llm_service)

@pytest.mark.asyncio
async def test_generate_use_case_diagram(modeling_tools, llm_service):
    # 准备测试数据
    test_response = {
        "actors": [
            {
                "name": "User",
                "description": "System user",
                "type": "primary"
            }
        ],
        "use_cases": [
            {
                "name": "Login",
                "description": "User login to system",
                "actors": ["User"]
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_response),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.get_json_completion.return_value = (test_response, llm_response)
    
    # 执行测试
    result = await modeling_tools.generate_use_case_diagram("Test requirements")
    
    # 验证结果
    assert result == test_response
    llm_service.get_json_completion.assert_called_once()

@pytest.mark.asyncio
async def test_generate_data_flow_diagram(modeling_tools, llm_service):
    # 准备测试数据
    test_response = {
        "processes": [
            {
                "name": "Process Data",
                "description": "Process user data"
            }
        ],
        "data_stores": [
            {
                "name": "User DB",
                "description": "User database"
            }
        ],
        "data_flows": [
            {
                "from": "Process Data",
                "to": "User DB",
                "data": "User information"
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_response),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.get_json_completion.return_value = (test_response, llm_response)
    
    # 执行测试
    result = await modeling_tools.generate_data_flow_diagram("Test requirements")
    
    # 验证结果
    assert result == test_response
    llm_service.get_json_completion.assert_called_once()

@pytest.mark.asyncio
async def test_generate_state_diagram(modeling_tools, llm_service):
    # 准备测试数据
    test_response = {
        "states": [
            {
                "name": "Initial",
                "type": "initial"
            },
            {
                "name": "Processing",
                "type": "normal"
            },
            {
                "name": "Final",
                "type": "final"
            }
        ],
        "transitions": [
            {
                "from": "Initial",
                "to": "Processing",
                "event": "Start"
            },
            {
                "from": "Processing",
                "to": "Final",
                "event": "Complete"
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_response),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.get_json_completion.return_value = (test_response, llm_response)
    
    # 执行测试
    result = await modeling_tools.generate_state_diagram("Test requirements")
    
    # 验证结果
    assert result == test_response
    llm_service.get_json_completion.assert_called_once()

@pytest.mark.asyncio
async def test_generate_sequence_diagram(modeling_tools, llm_service):
    # 准备测试数据
    test_response = {
        "participants": [
            {
                "name": "User",
                "type": "actor"
            },
            {
                "name": "System",
                "type": "participant"
            }
        ],
        "messages": [
            {
                "from": "User",
                "to": "System",
                "message": "Request data"
            },
            {
                "from": "System",
                "to": "User",
                "message": "Return data"
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_response),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.get_json_completion.return_value = (test_response, llm_response)
    
    # 执行测试
    result = await modeling_tools.generate_sequence_diagram("Test requirements")
    
    # 验证结果
    assert result == test_response
    llm_service.get_json_completion.assert_called_once()

@pytest.mark.asyncio
async def test_generate_class_diagram(modeling_tools, llm_service):
    # 准备测试数据
    test_response = {
        "classes": [
            {
                "name": "User",
                "attributes": [
                    {
                        "name": "id",
                        "type": "int"
                    },
                    {
                        "name": "name",
                        "type": "str"
                    }
                ],
                "methods": [
                    {
                        "name": "login",
                        "return_type": "bool"
                    }
                ]
            }
        ],
        "relationships": [
            {
                "from": "User",
                "to": "System",
                "type": "association"
            }
        ]
    }
    
    llm_response = LLMResponse(
        content=json.dumps(test_response),
        tokens_used=100,
        finish_reason="stop",
        model="deepseek-chat"
    )
    
    llm_service.get_json_completion.return_value = (test_response, llm_response)
    
    # 执行测试
    result = await modeling_tools.generate_class_diagram("Test requirements")
    
    # 验证结果
    assert result == test_response
    llm_service.get_json_completion.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_json_response(modeling_tools, llm_service):
    # 准备测试数据
    llm_service.process_prompt.return_value = "Invalid JSON"
    
    # 执行测试
    result = await modeling_tools.generate_use_case_diagram("Test requirements")
    
    # 验证结果
    assert "Error: Invalid JSON response from LLM" in result 