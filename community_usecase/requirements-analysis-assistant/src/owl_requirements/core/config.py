"""Configuration management for the OWL Requirements Analysis system."""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum, auto
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv()

class LLMProvider(str, Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"

class AgentRole(str, Enum):
    """智能体角色"""
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    CHECKER = "checker"
    GENERATOR = "generator"

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000

class WebConfig(BaseModel):
    """Web服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["*"]
    static_dir: str = "static"
    templates_dir: str = "templates"

class AgentConfig(BaseModel):
    """智能体配置"""
    name: str
    role: AgentRole
    description: str
    prompt_template: str

class SystemConfig(BaseModel):
    """系统配置"""
    name: str = "OWL需求分析助手"
    version: str = "0.1.0"
    description: str = "基于多智能体的需求分析系统"
    log_level: str = "INFO"
    log_file: str = "logs/owl.log"
    
    # LLM配置
    llm_provider: LLMProvider = LLMProvider.DEEPSEEK
    llm_model: str = "deepseek-chat"
    llm_api_key: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    
    # Web配置
    web: WebConfig = WebConfig()
    
    # 智能体配置
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)

class AgentStatus(Enum):
    """Agent status states."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"

class RunMode(Enum):
    """运行模式枚举。"""
    WEB = auto()  # Web界面模式
    CLI = auto()  # 命令行交互模式
    ONCE = auto()  # 单次执行模式

class OWLJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for OWL objects."""
    def default(self, obj):
        if isinstance(obj, AgentConfig):
            return obj.to_dict()
        if isinstance(obj, AgentRole):
            return obj.value
        if isinstance(obj, AgentStatus):
            return obj.value
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

@dataclass
class SystemConfig:
    """系统配置类。"""
    
    # 运行模式配置
    mode: RunMode = RunMode.WEB  # 默认使用Web界面模式
    input_text: Optional[str] = None  # 单次执行模式的输入文本
    
    # Web服务配置
    host: str = "127.0.0.1"  # Web服务主机
    port: int = 8080  # Web服务端口
    
    # LLM配置
    llm_provider: LLMProvider = LLMProvider.DEEPSEEK  # 默认使用DeepSeek
    config_file: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "system.yaml"
    )  # 配置文件路径
    
    # 日志配置
    log_level: str = "INFO"  # 日志级别
    log_file: Optional[str] = None  # 日志文件路径
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "SystemConfig":
        """
        从字典创建配置对象。

        Args:
            config_dict: 配置字典

        Returns:
            系统配置对象
        """
        # 处理运行模式
        mode_str = config_dict.get("mode", "web").lower()
        if mode_str == "web":
            mode = RunMode.WEB
        elif mode_str == "cli":
            mode = RunMode.CLI
        elif mode_str == "once":
            mode = RunMode.ONCE
        else:
            raise ValueError(f"无效的运行模式: {mode_str}")
        
        # 处理LLM提供商
        provider_str = config_dict.get("llm_provider", "deepseek").lower()
        try:
            llm_provider = LLMProvider(provider_str)
        except ValueError:
            raise ValueError(f"无效的LLM提供商: {provider_str}")
        
        return cls(
            mode=mode,
            input_text=config_dict.get("input_text"),
            host=config_dict.get("host", "127.0.0.1"),
            port=int(config_dict.get("port", 8080)),
            llm_provider=llm_provider,
            config_file=config_dict.get("config_file", cls.config_file),
            log_level=config_dict.get("log_level", "INFO"),
            log_file=config_dict.get("log_file")
        )

def load_config(config_path: str) -> SystemConfig:
    """Load system configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded system configuration
        
    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If config file is invalid
    """
    # 确保配置文件存在
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    # 读取配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # 提取系统配置
    system_config = config_data.get("system", {})
    
    # 提取LLM配置
    llm_config = config_data.get("llm", {})
    
    # 提取Web配置
    web_config = WebConfig(**config_data.get("web", {}))
    
    # 提取智能体配置
    agents_config = {}
    for agent_id, agent_data in config_data.get("agents", {}).items():
        agents_config[agent_id] = AgentConfig(**agent_data)
    
    # 创建系统配置对象
    return SystemConfig(
        name=system_config.get("name", "OWL需求分析助手"),
        version=system_config.get("version", "0.1.0"),
        description=system_config.get("description", "基于多智能体的需求分析系统"),
        log_level=system_config.get("log_level", "INFO"),
        log_file=system_config.get("log_file", "logs/owl.log"),
        
        llm_provider=llm_config.get("provider", "openai"),
        llm_model=llm_config.get("model", "gpt-4-turbo-preview"),
        llm_api_key=llm_config.get("api_key") or os.getenv("OPENAI_API_KEY"),
        llm_temperature=llm_config.get("temperature", 0.7),
        llm_max_tokens=llm_config.get("max_tokens", 4000),
        
        web=web_config,
        agents=agents_config
    )