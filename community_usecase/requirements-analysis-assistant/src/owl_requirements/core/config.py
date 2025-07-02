"""
OWL需求分析系统配置模块
"""

import os
import yaml
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field(default="ollama")
    model: str = Field(default="mistral")
    api_key: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)
    timeout: int = Field(default=60)


class WebConfig(BaseModel):
    """Web配置"""
    static_path: str = Field(default="static")
    templates_path: str = Field(default="templates")
    session_timeout: int = Field(default=3600)
    max_connections: int = Field(default=100)
    cors_origins: List[str] = Field(default=["*"])


class AgentConfig(BaseModel):
    """智能体配置"""
    enabled: bool = Field(default=True)
    batch_size: Optional[int] = Field(default=10)
    max_depth: Optional[int] = Field(default=3)
    threshold: Optional[float] = Field(default=0.8)
    format: Optional[str] = Field(default="markdown")


class SystemConfig(BaseModel):
    """系统配置"""
    mode: str = Field(default="web")
    port: int = Field(default=8082)
    host: str = Field(default="0.0.0.0")
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path):
        """从YAML文件加载配置"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {str(e)}")

    def validate(self):
        """验证配置"""
        if self.llm.provider not in ["ollama", "openai", "deepseek", "anthropic", "azure"]:
            raise ValueError(f"不支持的LLM提供商: {self.llm.provider}")


Config = SystemConfig
