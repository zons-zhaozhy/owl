"""配置系统测试"""

import os
import pytest
from pathlib import Path
from typing import Dict, Any
import yaml
from owl_requirements.core.config import (
    Config,
    ConfigManager,
    WebConfig,
    LLMConfig,
    AgentConfig
)

@pytest.fixture
def test_config_path(tmp_path) -> Path:
    """创建测试配置文件"""
    config_path = tmp_path / "test_config.yaml"
    test_config = {
        "app_name": "测试应用",
        "debug": True,
        "llm": {
            "provider": "test_provider",
            "model_name": "test_model",
            "api_key": "test_key" * 2,  # 确保长度大于32
            "temperature": 0.5,
            "max_tokens": 1000
        },
        "web": {
            "host": "0.0.0.0",
            "port": 8000,
            "allowed_hosts": ["test.com", "example.com"],
            "debug": True
        },
        "agents": {
            "test_agent": {
                "name": "TestAgent",
                "description": "测试智能体",
                "enabled": True,
                "tools": ["tool1", "tool2"],
                "model": "test_model",
                "temperature": 0.3,
                "max_tokens": 1500
            }
        }
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_config, f)
    return config_path

def test_web_config():
    """测试Web配置"""
    # 测试默认值
    config = WebConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 7860
    assert config.allowed_hosts == ["localhost", "127.0.0.1"]
    assert not config.debug
    
    # 测试自定义值
    config = WebConfig(
        host="0.0.0.0",
        port=8000,
        allowed_hosts=["test.com"],
        debug=True
    )
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.allowed_hosts == ["test.com"]
    assert config.debug
    
    # 测试端口范围验证
    with pytest.raises(ValueError):
        WebConfig(port=0)
    with pytest.raises(ValueError):
        WebConfig(port=65536)
        
    # 测试allowed_hosts验证
    config = WebConfig(allowed_hosts="test.com,example.com")
    assert config.allowed_hosts == ["test.com", "example.com"]
    
    config = WebConfig(allowed_hosts='["test.com", "example.com"]')
    assert config.allowed_hosts == ["test.com", "example.com"]

def test_llm_config():
    """测试LLM配置"""
    # 测试默认值
    config = LLMConfig()
    assert config.provider == "deepseek"
    assert config.model_name == "deepseek-chat"
    assert config.api_key == ""
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    
    # 测试自定义值
    config = LLMConfig(
        provider="test",
        model_name="test_model",
        api_key="x" * 32,
        temperature=0.5,
        max_tokens=1000
    )
    assert config.provider == "test"
    assert config.model_name == "test_model"
    assert config.api_key == "x" * 32
    assert config.temperature == 0.5
    assert config.max_tokens == 1000
    
    # 测试API密钥长度验证
    with pytest.raises(ValueError):
        LLMConfig(api_key="short")
        
    # 测试温度范围验证
    with pytest.raises(ValueError):
        LLMConfig(temperature=-0.1)
    with pytest.raises(ValueError):
        LLMConfig(temperature=1.1)
        
    # 测试token范围验证
    with pytest.raises(ValueError):
        LLMConfig(max_tokens=0)
    with pytest.raises(ValueError):
        LLMConfig(max_tokens=9000)

def test_agent_config():
    """测试智能体配置"""
    # 测试必需字段
    with pytest.raises(ValueError):
        AgentConfig()
        
    # 测试有效配置
    config = AgentConfig(
        name="TestAgent",
        description="Test Description"
    )
    assert config.name == "TestAgent"
    assert config.description == "Test Description"
    assert config.enabled
    assert config.tools == []
    assert config.model == "deepseek-chat"
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    
    # 测试完整配置
    config = AgentConfig(
        name="TestAgent",
        description="Test Description",
        enabled=False,
        tools=["tool1", "tool2"],
        model="custom_model",
        temperature=0.5,
        max_tokens=1000,
        instructions="Test Instructions"
    )
    assert not config.enabled
    assert config.tools == ["tool1", "tool2"]
    assert config.model == "custom_model"
    assert config.temperature == 0.5
    assert config.max_tokens == 1000
    assert config.instructions == "Test Instructions"

def test_config_manager(test_config_path):
    """测试配置管理器"""
    # 测试加载配置文件
    manager = ConfigManager(str(test_config_path))
    config = manager.get_config()
    
    assert config.app_name == "测试应用"
    assert config.debug
    assert config.llm.provider == "test_provider"
    assert config.llm.model_name == "test_model"
    assert config.web.host == "0.0.0.0"
    assert config.web.port == 8000
    assert "test_agent" in config.agents
    
    # 测试更新配置
    manager.update_config({
        "app_name": "新应用名称",
        "llm": {
            "temperature": 0.8
        }
    })
    
    assert manager.config.app_name == "新应用名称"
    assert manager.config.llm.temperature == 0.8
    assert manager.config.llm.provider == "test_provider"  # 确保其他值保持不变
    
    # 测试保存配置
    save_path = str(test_config_path.parent / "saved_config.yaml")
    manager.config_path = save_path
    manager.save_config()
    
    # 验证保存的配置
    with open(save_path, 'r', encoding='utf-8') as f:
        saved_config = yaml.safe_load(f)
    
    assert saved_config["app_name"] == "新应用名称"
    assert saved_config["llm"]["temperature"] == 0.8
    assert saved_config["llm"]["provider"] == "test_provider"

def test_config_validation():
    """测试配置验证"""
    # 测试环境验证
    with pytest.raises(ValueError):
        Config(environment="invalid")
        
    # 测试日志级别验证
    with pytest.raises(ValueError):
        Config(log_level="INVALID")
        
    # 测试有效配置
    config = Config(
        environment="production",
        log_level="INFO"
    )
    assert config.environment == "production"
    assert config.log_level == "INFO"
    
    # 测试默认值
    config = Config()
    assert config.environment == "development"
    assert config.log_level == "DEBUG"
