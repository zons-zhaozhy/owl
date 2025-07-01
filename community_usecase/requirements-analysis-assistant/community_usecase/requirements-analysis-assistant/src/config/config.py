"""配置管理模块"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from pydantic import BaseModel, Field

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
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大token数")

class AgentConfig(BaseModel):
    """智能体配置"""
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    enabled: bool = Field(default=True, description="是否启用")
    tools: List[str] = Field(default_factory=list, description="可用工具列表")

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
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml"
        )
        self.config = self._load_config()
        
    def _load_config(self) -> Config:
        """
        加载配置
        
        Returns:
            配置对象
        """
        # 默认配置
        default_config = {
            "app_name": "OWL需求分析助手",
            "debug": False,
            "llm": {
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "web": {
                "host": "127.0.0.1",
                "port": 7860,
                "allowed_hosts": ["localhost", "127.0.0.1"],
                "debug": False,
                "static_dir": "static",
                "template_dir": "templates"
            },
            "agents": {
                "requirements_extractor": {
                    "name": "RequirementsExtractor",
                    "description": "需求提取智能体",
                    "enabled": True,
                    "tools": ["nlp_toolkit", "text_analyzer"]
                },
                "requirements_analyzer": {
                    "name": "RequirementsAnalyzer",
                    "description": "需求分析智能体",
                    "enabled": True,
                    "tools": ["dependency_analyzer", "risk_assessor"]
                },
                "document_generator": {
                    "name": "DocumentGenerator",
                    "description": "文档生成智能体",
                    "enabled": True,
                    "tools": ["template_engine", "markdown_generator"]
                },
                "quality_checker": {
                    "name": "QualityChecker",
                    "description": "质量检查智能体",
                    "enabled": True,
                    "tools": ["quality_rules", "consistency_checker"]
                }
            },
            "output_dir": "output",
            "template_dir": "templates"
        }
        
        # 如果配置文件存在，则加载并合并配置
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._merge_config(default_config, file_config)
                    
        return Config(**default_config)
        
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        合并配置
        
        Args:
            base: 基础配置
            update: 更新配置
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
                
    def get_config(self) -> Config:
        """获取配置"""
        return self.config
        
    def save_config(self) -> None:
        """保存配置到文件"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
            
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.model_dump(), f, allow_unicode=True, default_flow_style=False)
            
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            updates: 更新的配置项
        """
        config_dict = self.config.model_dump()
        self._merge_config(config_dict, updates)
        self.config = Config(**config_dict)
        
# 全局配置实例
config_manager = ConfigManager()
config = config_manager.get_config()
