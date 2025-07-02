"""配置管理模块"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from pydantic import BaseModel, Field
from ..core.config import AgentConfig, AgentRole, SystemConfig

class WebConfig(BaseModel):
    """Web服务器配置"""
    host: str = Field(default="127.0.0.1", description="服务器主机")
    port: int = Field(default=7860, description="服务器端口")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], description="允许的主机列表")
    debug: bool = Field(default=False, description="调试模式")
    static_dir: str = Field(default="static", description="静态文件目录")
    template_dir: str = Field(default="templates", description="模板目录")

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field(default="deepseek", description="LLM提供商")
    model_name: str = Field(default="deepseek-chat", description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    temperature: float = Field(default=0.1, description="温度参数")
    max_tokens: int = Field(default=4000, description="最大token数")
    top_p: float = Field(default=0.1, description="Top P采样参数")
    frequency_penalty: float = Field(default=0.1, description="频率惩罚参数")
    presence_penalty: float = Field(default=0.1, description="存在惩罚参数")

class Config(BaseModel):
    """全局配置"""
    app_name: str = Field(default="OWL需求分析助手", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM配置")
    web: WebConfig = Field(default_factory=WebConfig, description="Web服务器配置")
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="智能体配置")
    output_dir: str = Field(default="output", description="输出目录")
    template_dir: str = Field(default="templates", description="模板目录")

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config = self._load_config()
        
    def _load_config(self) -> SystemConfig:
        """加载配置
        
        Returns:
            SystemConfig: 系统配置
        """
        return SystemConfig.from_yaml(self.config_path)
        
    @property
    def config(self) -> SystemConfig:
        """获取当前配置
        
        Returns:
            SystemConfig: 系统配置
        """
        return self._config
        
    def reload(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()

# 创建全局配置管理器实例
config_manager = ConfigManager()
config = config_manager.config
