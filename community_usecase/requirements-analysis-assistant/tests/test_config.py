"""
配置系统测试模块。
"""

import os
import pytest
from unittest.mock import patch, mock_open
import tempfile
from pathlib import Path
from typing import Dict, Any
import json

from owl_requirements.core.config import (
    SystemConfig,
    LLMConfig,
    LLMProvider,
    RunMode,
    Config,
    WebConfig
)
from owl_requirements.core.exceptions import ConfigurationError, ConfigError


@pytest.fixture
def mock_system_yaml():
    """模拟system.yaml内容。"""
    return """
mode: web
port: 8080
host: 127.0.0.1
llm_provider: deepseek
debug: false
"""


@pytest.fixture
def mock_llm_yaml():
    """模拟llm.yaml内容。"""
    return """
openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4-turbo-preview
  temperature: 0.7
  max_tokens: 2000

deepseek:
  api_key: ${DEEPSEEK_API_KEY}
  model: deepseek-chat
  temperature: 0.7
  max_tokens: 2000

ollama:
  host: http://localhost:11434
  model: llama2
  temperature: 0.7
  max_tokens: 2000
"""


def test_system_config_load(mock_system_yaml):
    """测试加载系统配置。"""
    with patch("builtins.open", mock_open(read_data=mock_system_yaml)):
        config = SystemConfig()
        config.load()
        
        assert config.mode == RunMode.WEB
        assert config.port == 8080
        assert config.host == "127.0.0.1"
        assert config.llm_provider == LLMProvider.DEEPSEEK
        assert not config.debug


def test_system_config_load_with_env_vars(mock_system_yaml):
    """测试使用环境变量加载系统配置。"""
    with patch.dict(os.environ, {
        "OWL_MODE": "cli",
        "OWL_PORT": "9090",
        "OWL_HOST": "0.0.0.0",
        "OWL_LLM_PROVIDER": "openai",
        "OWL_DEBUG": "true"
    }):
        with patch("builtins.open", mock_open(read_data=mock_system_yaml)):
            config = SystemConfig()
            config.load()
            
            assert config.mode == RunMode.CLI
            assert config.port == 9090
            assert config.host == "0.0.0.0"
            assert config.llm_provider == LLMProvider.OPENAI
            assert config.debug


def test_llm_config_load(mock_llm_yaml):
    """测试加载LLM配置。"""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_openai_key",
        "DEEPSEEK_API_KEY": "test_deepseek_key"
    }):
        with patch("builtins.open", mock_open(read_data=mock_llm_yaml)):
            config = LLMConfig()
            config.load()
            
            # 验证OpenAI配置
            assert config.openai["api_key"] == "test_openai_key"
            assert config.openai["model"] == "gpt-4-turbo-preview"
            assert config.openai["temperature"] == 0.7
            assert config.openai["max_tokens"] == 2000
            
            # 验证DeepSeek配置
            assert config.deepseek["api_key"] == "test_deepseek_key"
            assert config.deepseek["model"] == "deepseek-chat"
            assert config.deepseek["temperature"] == 0.7
            assert config.deepseek["max_tokens"] == 2000
            
            # 验证Ollama配置
            assert config.ollama["host"] == "http://localhost:11434"
            assert config.ollama["model"] == "llama2"
            assert config.ollama["temperature"] == 0.7
            assert config.ollama["max_tokens"] == 2000


def test_llm_config_load_without_api_keys(mock_llm_yaml):
    """测试在没有API密钥的情况下加载LLM配置。"""
    with patch("builtins.open", mock_open(read_data=mock_llm_yaml)):
        config = LLMConfig()
        config.load()
        
        # API密钥应该为None
        assert config.openai["api_key"] is None
        assert config.deepseek["api_key"] is None


def test_system_config_invalid_mode():
    """测试无效的运行模式。"""
    invalid_yaml = """
mode: invalid
port: 8080
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的运行模式"):
            config = SystemConfig()
            config.load()


def test_system_config_invalid_port():
    """测试无效的端口号。"""
    invalid_yaml = """
mode: web
port: -1
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的端口号"):
            config = SystemConfig()
            config.load()


def test_system_config_invalid_host():
    """测试无效的主机地址。"""
    invalid_yaml = """
mode: web
port: 8080
host: invalid_host
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的主机地址"):
            config = SystemConfig()
            config.load()


def test_system_config_invalid_llm_provider():
    """测试无效的LLM提供商。"""
    invalid_yaml = """
mode: web
port: 8080
llm_provider: invalid
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的LLM提供商"):
            config = SystemConfig()
            config.load()


def test_llm_config_invalid_temperature():
    """测试无效的温度值。"""
    invalid_yaml = """
openai:
  api_key: test_key
  model: gpt-4
  temperature: 2.0
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的温度值"):
            config = LLMConfig()
            config.load()


def test_llm_config_invalid_max_tokens():
    """测试无效的最大token数。"""
    invalid_yaml = """
openai:
  api_key: test_key
  model: gpt-4
  max_tokens: -1
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)):
        with pytest.raises(ConfigurationError, match="无效的最大token数"):
            config = LLMConfig()
            config.load()


def test_system_config_defaults():
    """测试系统配置默认值。"""
    empty_yaml = ""
    with patch("builtins.open", mock_open(read_data=empty_yaml)):
        config = SystemConfig()
        config.load()
        
        assert config.mode == RunMode.WEB
        assert config.port == 8080
        assert config.host == "127.0.0.1"
        assert config.llm_provider == LLMProvider.DEEPSEEK
        assert not config.debug


def test_llm_config_defaults():
    """测试LLM配置默认值。"""
    empty_yaml = ""
    with patch("builtins.open", mock_open(read_data=empty_yaml)):
        config = LLMConfig()
        config.load()
        
        # 验证默认配置
        assert config.openai["model"] == "gpt-4-turbo-preview"
        assert config.openai["temperature"] == 0.7
        assert config.openai["max_tokens"] == 2000
        
        assert config.deepseek["model"] == "deepseek-chat"
        assert config.deepseek["temperature"] == 0.7
        assert config.deepseek["max_tokens"] == 2000
        
        assert config.ollama["host"] == "http://localhost:11434"
        assert config.ollama["model"] == "llama2"
        assert config.ollama["temperature"] == 0.7
        assert config.ollama["max_tokens"] == 2000 


class TestConfig:
    """配置系统测试类"""
    
    def test_initialization(self):
        """测试配置初始化"""
        # 默认配置
        config = Config()
        assert config.system_mode is not None
        assert config.llm_provider is not None
        assert config.llm_model is not None
        
        # 从字典初始化
        config_dict = {
            "system_mode": "web",
            "llm_provider": "anthropic",
            "llm_model": "claude-2"
        }
        config = Config(**config_dict)
        assert config.system_mode == "web"
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-2"
        
    def test_load_from_file(self, tmp_path: Path):
        """测试从文件加载配置"""
        # 创建配置文件
        config_file = tmp_path / "config.json"
        config_data = {
            "system_mode": "cli",
            "llm_provider": "openai",
            "llm_model": "gpt-4"
        }
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        # 加载配置
        config = Config.from_file(config_file)
        assert config.system_mode == "cli"
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        
    def test_load_from_env(self):
        """测试从环境变量加载配置"""
        # 设置环境变量
        env_vars = {
            "OWL_SYSTEM_MODE": "web",
            "OWL_LLM_PROVIDER": "anthropic",
            "OWL_LLM_MODEL": "claude-2"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.from_env()
            assert config.system_mode == "web"
            assert config.llm_provider == "anthropic"
            assert config.llm_model == "claude-2"
            
    def test_default_values(self):
        """测试默认值"""
        config = Config()
        
        # 系统配置
        assert config.system_mode == "web"
        assert config.system_port == 8000
        assert config.system_host == "127.0.0.1"
        
        # LLM 配置
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert 0 <= config.llm_temperature <= 1
        
    def test_validation(self):
        """测试配置验证"""
        # 无效的系统模式
        with pytest.raises(ConfigError) as exc:
            Config(system_mode="invalid")
        assert "无效的系统模式" in str(exc.value)
        
        # 无效的 LLM 提供商
        with pytest.raises(ConfigError) as exc:
            Config(llm_provider="invalid")
        assert "无效的 LLM 提供商" in str(exc.value)
        
        # 无效的温度值
        with pytest.raises(ConfigError) as exc:
            Config(llm_temperature=2.0)
        assert "无效的温度值" in str(exc.value)
        
    def test_sensitive_info(self, tmp_path: Path):
        """测试敏感信息处理"""
        # 创建包含敏感信息的配置
        config_data = {
            "llm_api_key": "sk-123456",
            "system_mode": "web"
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
            
        # 加载配置
        config = Config.from_file(config_file)
        
        # 验证敏感信息被正确处理
        assert config.llm_api_key.startswith("sk-")
        assert str(config).count("sk-") == 0
        assert repr(config).count("sk-") == 0
        
    def test_config_update(self):
        """测试配置更新"""
        config = Config()
        
        # 更新单个值
        config.update(system_mode="cli")
        assert config.system_mode == "cli"
        
        # 更新多个值
        config.update(
            llm_provider="anthropic",
            llm_model="claude-2"
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-2"
        
        # 更新嵌套配置
        config.update({
            "system": {
                "mode": "web",
                "port": 9000
            }
        })
        assert config.system_mode == "web"
        assert config.system_port == 9000
        
    def test_config_merge(self):
        """测试配置合并"""
        base_config = Config(
            system_mode="web",
            llm_provider="openai"
        )
        
        override_config = Config(
            system_port=9000,
            llm_model="gpt-4"
        )
        
        # 合并配置
        merged_config = Config.merge(base_config, override_config)
        
        assert merged_config.system_mode == "web"
        assert merged_config.system_port == 9000
        assert merged_config.llm_provider == "openai"
        assert merged_config.llm_model == "gpt-4"
        
    def test_config_reset(self):
        """测试配置重置"""
        config = Config(
            system_mode="cli",
            llm_provider="anthropic"
        )
        
        # 重置所有配置
        config.reset()
        
        assert config.system_mode == "web"  # 默认值
        assert config.llm_provider == "openai"  # 默认值
        
        # 重置特定配置
        config.system_mode = "cli"
        config.reset(["system_mode"])
        
        assert config.system_mode == "web"  # 默认值
        assert config.llm_provider == "openai"  # 保持不变
        
    def test_validation_chain(self):
        """测试验证链"""
        # 创建依赖的配置项
        config_data = {
            "llm_provider": "anthropic",
            "llm_model": "gpt-4"  # 与提供商不匹配
        }
        
        with pytest.raises(ConfigError) as exc:
            Config(**config_data)
        assert "模型与提供商不匹配" in str(exc.value)
        
        # 修复依赖
        config_data["llm_model"] = "claude-2"
        config = Config(**config_data)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-2"
        
    def test_config_dependencies(self):
        """测试配置依赖关系"""
        # Web 模式依赖
        config = Config(
            system_mode="web",
            system_port=None  # 缺少必需的端口
        )
        
        with pytest.raises(ConfigError) as exc:
            config.validate()
        assert "Web 模式需要指定端口" in str(exc.value)
        
        # LLM 配置依赖
        config = Config(
            llm_provider="openai",
            llm_api_key=None  # 缺少必需的 API 密钥
        )
        
        with pytest.raises(ConfigError) as exc:
            config.validate()
        assert "需要提供 API 密钥" in str(exc.value)
        
    def test_export_config(self, tmp_path: Path):
        """测试配置导出"""
        config = Config(
            system_mode="web",
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        # 导出为 JSON
        json_file = tmp_path / "config.json"
        config.export(json_file)
        
        with open(json_file) as f:
            exported = json.load(f)
            assert exported["system_mode"] == "web"
            assert exported["llm_provider"] == "openai"
            
        # 导出为 YAML
        yaml_file = tmp_path / "config.yaml"
        config.export(yaml_file)
        
        import yaml
        with open(yaml_file) as f:
            exported = yaml.safe_load(f)
            assert exported["system_mode"] == "web"
            assert exported["llm_provider"] == "openai"
            
        # 导出为环境变量
        env_file = tmp_path / ".env"
        config.export(env_file, format="env")
        
        with open(env_file) as f:
            content = f.read()
            assert "OWL_SYSTEM_MODE=web" in content
            assert "OWL_LLM_PROVIDER=openai" in content
            
    def test_config_schema(self):
        """测试配置模式"""
        schema = Config.get_schema()
        
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # 验证必需字段
        assert "required" in schema
        assert "system_mode" in schema["required"]
        assert "llm_provider" in schema["required"]
        
        # 验证字段类型
        props = schema["properties"]
        assert props["system_mode"]["type"] == "string"
        assert props["llm_temperature"]["type"] == "number"
        
        # 验证枚举值
        assert "enum" in props["system_mode"]
        assert "web" in props["system_mode"]["enum"]
        assert "cli" in props["system_mode"]["enum"]
        
    def test_config_inheritance(self):
        """测试配置继承"""
        class ExtendedConfig(Config):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.custom_field = kwargs.get("custom_field")
                
            def validate(self):
                super().validate()
                if self.custom_field is not None:
                    if not isinstance(self.custom_field, str):
                        raise ConfigError("custom_field 必须是字符串")
                        
        # 测试扩展配置
        config = ExtendedConfig(
            system_mode="web",
            custom_field="test"
        )
        assert config.custom_field == "test"
        
        # 测试验证
        with pytest.raises(ConfigError):
            ExtendedConfig(
                system_mode="web",
                custom_field=123  # 类型错误
            )
            
    def test_config_serialization(self):
        """测试配置序列化"""
        config = Config(
            system_mode="web",
            llm_provider="openai"
        )
        
        # 转换为字典
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["system_mode"] == "web"
        
        # 转换为 JSON
        config_json = config.to_json()
        assert isinstance(config_json, str)
        assert json.loads(config_json)["system_mode"] == "web"
        
        # 从 JSON 恢复
        recovered = Config.from_json(config_json)
        assert recovered.system_mode == "web"
        assert recovered.llm_provider == "openai" 