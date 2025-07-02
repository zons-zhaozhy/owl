"""Configuration management for the OWL Requirements Analysis system."""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum, auto

# 加载环境变量
load_dotenv()

class AgentRole(str, Enum):
    """Agent roles in the system."""
    REQUIREMENTS_EXTRACTOR = "requirements_extractor"
    REQUIREMENTS_ANALYZER = "requirements_analyzer"
    DOCUMENT_GENERATOR = "document_generator"
    QUALITY_CHECKER = "quality_checker"
    COORDINATOR = "coordinator"

class AgentStatus(Enum):
    """Agent status states."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"

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
class AgentConfig:
    """Agent-specific configuration."""
    role: AgentRole
    name: str
    model: str = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 4000
    stop_sequences: Optional[List[str]] = None
    extra_config: Optional[Dict[str, Any]] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if hasattr(self, key):
            return getattr(self, key)
        if self.extra_config and key in self.extra_config:
            return self.extra_config[key]
        return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "role": self.role.value,
            "name": self.name,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop_sequences": self.stop_sequences,
            **(self.extra_config or {})
        }
        
    def to_json(self) -> str:
        """Convert config to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), cls=OWLJSONEncoder, indent=2)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            AgentConfig instance
        """
        role = data.pop("role")
        if isinstance(role, str):
            role = AgentRole(role)
        return cls(role=role, **data)
        
    @classmethod
    def from_json(cls, json_str: str) -> "AgentConfig":
        """Create config from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            AgentConfig instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    
    # LLM settings
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # Default model settings
    default_model: str = "deepseek-chat"
    default_temperature: float = 0.1
    default_max_tokens: int = 4000
    
    # Agent settings
    agent_configs: Dict[AgentRole, AgentConfig] = field(default_factory=dict)
    
    # Global retry settings
    max_retries: int = 3
    
    # Logging settings
    log_level: str = "DEBUG"
    log_file: str = "logs/owl.log"
    
    # Web interface settings
    web_host: str = "127.0.0.1"
    web_port: int = 8080
    
    # Output settings
    output_dir: str = "output"
    template_dir: str = "templates"
    workspace_dir: str = "workspace"
    
    # Templates settings
    templates_dir: str = "templates/prompts"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_api_key": self.llm_api_key,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "agent_configs": {
                role.value: config.to_dict()
                for role, config in self.agent_configs.items()
            },
            "log_level": self.log_level,
            "log_file": self.log_file,
            "web_host": self.web_host,
            "web_port": self.web_port,
            "output_dir": self.output_dir,
            "template_dir": self.template_dir,
            "workspace_dir": self.workspace_dir,
            "templates_dir": self.templates_dir,
            "max_retries": self.max_retries
        }
        
    def to_json(self) -> str:
        """Convert config to JSON string.
        
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), cls=OWLJSONEncoder, indent=2)
    
    def save(self, config_path: str) -> None:
        """Save the current configuration to a YAML file.
        
        Args:
            config_path: Path where to save the configuration
        """
        # 使用 to_dict() 获取可序列化的数据
        config_data = self.to_dict()
        
        # 将 agent_configs 移动到 agents 字段下
        agents_data = config_data.pop('agent_configs')
        config_data['agents'] = agents_data
        
        # 将 templates_dir 移动到 templates 字段下
        templates_dir = config_data.pop('templates_dir')
        config_data['templates'] = {
            'directory': templates_dir
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False)
            
    def get_agent_config(self, role: AgentRole) -> AgentConfig:
        """Get the configuration for a specific agent role.
        
        Args:
            role: The role of the agent
            
        Returns:
            Configuration for the specified agent role
        """
        return self.agent_configs[role]

    @classmethod
    def from_yaml(cls, config_path: str) -> "SystemConfig":
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            SystemConfig instance
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # 处理智能体配置
        agent_configs = {}
        if "agents" in config_data:
            for role_str, agent_config in config_data["agents"].items():
                role = AgentRole(role_str)
                agent_configs[role] = AgentConfig(
                    role=role,
                    name=agent_config.get("name", f"{role.value}_agent"),
                    model=agent_config.get("model", "deepseek-chat"),
                    temperature=agent_config.get("temperature", 0.1),
                    max_tokens=agent_config.get("max_tokens", 4000),
                    stop_sequences=agent_config.get("stop_sequences"),
                    extra_config={
                        k: v for k, v in agent_config.items()
                        if k not in ["role", "name", "model", "temperature", "max_tokens", "stop_sequences"]
                    } or None
                )

        # 创建系统配置实例
        return cls(
            llm_provider=config_data.get("llm_provider", "deepseek"),
            llm_model=config_data.get("llm_model", "deepseek-chat"),
            llm_api_key=config_data.get("llm_api_key", os.getenv("DEEPSEEK_API_KEY", "")),
            llm_temperature=config_data.get("llm_temperature", cls.llm_temperature),
            llm_max_tokens=config_data.get("llm_max_tokens", cls.llm_max_tokens),
            default_model=config_data.get("default_model", "deepseek-chat"),
            default_temperature=config_data.get("default_temperature", 0.1),
            default_max_tokens=config_data.get("default_max_tokens", 4000),
            agent_configs=agent_configs,
            log_level=config_data.get("log_level", "DEBUG"),
            log_file=config_data.get("log_file", "logs/owl.log"),
            web_host=config_data.get("web_host", "127.0.0.1"),
            web_port=config_data.get("web_port", 8080),
            output_dir=config_data.get("output_dir", "output"),
            template_dir=config_data.get("template_dir", "templates"),
            workspace_dir=config_data.get("workspace_dir", "workspace"),
            templates_dir=config_data.get("templates_dir", "templates/prompts"),
            max_retries=config_data.get("max_retries", 3)
        )

def load_config(config_path: str) -> SystemConfig:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        SystemConfig instance
    """
    return SystemConfig.from_yaml(config_path)