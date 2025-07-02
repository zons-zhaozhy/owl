"""
统一LLM服务管理器
整合所有LLM提供商和配置管理
"""

import os
import json
import yaml
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
import httpx
from openai import AsyncOpenAI

from ..core.exceptions import LLMServiceError, ConfigurationError
from ..utils.enums import LLMProvider

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseLLMProvider:
    """LLM提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 10000)
        self.timeout = config.get("timeout", 60)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        raise NotImplementedError
    
    def _get_api_key(self, key_name: str) -> str:
        """获取API密钥"""
        api_key = self.config.get("api_key")
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            # 从环境变量获取
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var)
            if not api_key:
                raise ConfigurationError(f"未找到API密钥: {env_var}")
        elif not api_key:
            # 直接从环境变量获取
            api_key = os.getenv(key_name)
            if not api_key:
                raise ConfigurationError(f"未找到API密钥: {key_name}")
        
        return api_key

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self._get_api_key("DEEPSEEK_API_KEY")
        self.api_base = config.get("api_base", "https://api.deepseek.com/v1")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout
        )
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                top_p=kwargs.get("top_p", 0.95),
                stream=False
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                provider="deepseek",
                model=self.model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise LLMServiceError(f"DeepSeek API调用失败: {str(e)}")

class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self._get_api_key("OPENAI_API_KEY")
        
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                top_p=kwargs.get("top_p", 1.0),
                stream=False
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise LLMServiceError(f"OpenAI API调用失败: {str(e)}")

class OllamaProvider(BaseLLMProvider):
    """Ollama本地提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:11434")
        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=self.timeout
        )
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        try:
            # 确保模型可用
            await self._ensure_model_available(self.model)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    "top_p": kwargs.get("top_p", 0.9)
                }
            }
            
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data.get("response", "")
            
            return LLMResponse(
                content=content,
                provider="ollama",
                model=self.model,
                metadata={"eval_count": data.get("eval_count", 0)}
            )
            
        except Exception as e:
            logger.error(f"Ollama API调用失败: {str(e)}")
            raise LLMServiceError(f"Ollama API调用失败: {str(e)}")
    
    async def _ensure_model_available(self, model: str):
        """确保模型可用"""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            available_models = [m["name"] for m in models]
            
            if model not in available_models:
                logger.info(f"模型 {model} 不可用，尝试拉取...")
                await self._pull_model(model)
                
        except Exception as e:
            logger.warning(f"检查模型可用性失败: {str(e)}")
    
    async def _pull_model(self, model: str):
        """拉取模型"""
        try:
            payload = {"name": model}
            response = await self.client.post("/api/pull", json=payload)
            response.raise_for_status()
            logger.info(f"模型 {model} 拉取完成")
        except Exception as e:
            logger.error(f"拉取模型 {model} 失败: {str(e)}")

class AnthropicProvider(BaseLLMProvider):
    """Anthropic提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self._get_api_key("ANTHROPIC_API_KEY")
        
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                timeout=self.timeout
            )
        except ImportError:
            raise ConfigurationError("需要安装 anthropic 包: pip install anthropic")
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
            
            return LLMResponse(
                content=content,
                provider="anthropic",
                model=self.model,
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {str(e)}")
            raise LLMServiceError(f"Anthropic API调用失败: {str(e)}")

class LLMManager:
    """统一LLM管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.providers = {}
        self.current_provider = None
        self._initialize_providers()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if not config_path:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                "src/config/llm_unified.yaml",
                "config/llm_unified.yaml", 
                "src/config/llm.yaml",
                "config.yaml"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                raise ConfigurationError("未找到LLM配置文件")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info(f"加载配置文件: {config_path}")
                return config
        except Exception as e:
            raise ConfigurationError(f"配置文件加载失败: {str(e)}")
    
    def _initialize_providers(self):
        """初始化提供商"""
        llm_config = self.config.get("llm", {})
        enabled_providers = llm_config.get("enabled_providers", [])
        provider_configs = llm_config.get("providers", {})
        
        for provider_name in enabled_providers:
            if provider_name not in provider_configs:
                logger.warning(f"提供商 {provider_name} 配置不存在，跳过")
                continue
                
            provider_config = provider_configs[provider_name]
            if not provider_config.get("enabled", True):
                logger.info(f"提供商 {provider_name} 已禁用，跳过")
                continue
            
            try:
                if provider_name == "deepseek":
                    self.providers[provider_name] = DeepSeekProvider(provider_config)
                elif provider_name == "openai":
                    self.providers[provider_name] = OpenAIProvider(provider_config)
                elif provider_name == "ollama":
                    self.providers[provider_name] = OllamaProvider(provider_config)
                elif provider_name == "anthropic":
                    self.providers[provider_name] = AnthropicProvider(provider_config)
                else:
                    logger.warning(f"未知的提供商: {provider_name}")
                    
                logger.info(f"初始化提供商: {provider_name}")
                
            except Exception as e:
                logger.error(f"初始化提供商 {provider_name} 失败: {str(e)}")
        
        # 设置默认提供商
        default_provider = os.getenv("OWL_LLM_PROVIDER") or llm_config.get("default_provider", "deepseek")
        if default_provider in self.providers:
            self.current_provider = default_provider
            logger.info(f"设置默认提供商: {default_provider}")
        else:
            # 使用第一个可用的提供商
            if self.providers:
                self.current_provider = list(self.providers.keys())[0]
                logger.warning(f"默认提供商不可用，使用: {self.current_provider}")
            else:
                raise ConfigurationError("没有可用的LLM提供商")
    
    def set_provider(self, provider_name: str):
        """设置当前提供商"""
        if provider_name not in self.providers:
            raise ValueError(f"提供商 {provider_name} 不可用")
        
        self.current_provider = provider_name
        logger.info(f"切换到提供商: {provider_name}")
    
    def get_available_providers(self) -> List[str]:
        """获取可用提供商列表"""
        return list(self.providers.keys())
    
    async def generate(
        self,
        template_name: Optional[str] = None,
        prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        # 如果提供了模板名称，则格式化提示词
        if template_name:
            formatted_prompt = self.format_prompt(template_name, **kwargs)
        elif prompt:
            formatted_prompt = prompt
        else:
            raise ValueError("必须提供 template_name 或 prompt")

        provider_name = provider or self.current_provider
        
        if provider_name not in self.providers:
            raise ValueError(f"提供商 {provider_name} 不可用")
        
        provider_instance = self.providers[provider_name]
        
        # 重试机制
        for attempt in range(provider_instance.retry_attempts):
            try:
                return await provider_instance.generate(formatted_prompt, **kwargs)
                
            except Exception as e:
                if attempt == provider_instance.retry_attempts - 1:
                    # 最后一次尝试失败，尝试降级到备用提供商
                    return await self._fallback_generate(formatted_prompt, provider_name, **kwargs)
                
                logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                await asyncio.sleep(provider_instance.retry_delay)
    
    async def _fallback_generate(self, prompt: str, failed_provider: str, **kwargs) -> LLMResponse:
        """降级生成"""
        fallback_provider = self.config.get("error_handling", {}).get("fallback_provider")
        
        if (fallback_provider and 
            fallback_provider != failed_provider and 
            fallback_provider in self.providers):
            
            logger.info(f"使用备用提供商: {fallback_provider}")
            provider_instance = self.providers[fallback_provider]
            return await provider_instance.generate(prompt, **kwargs)
        
        raise LLMServiceError(f"所有提供商都不可用")
    
    def get_prompt_template(self, template_name: str) -> Dict[str, Any]:
        """获取提示词模板"""
        # 首先尝试从配置文件加载
        templates = self.config.get("prompts", {}).get("templates", {})
        
        if template_name in templates:
            return templates[template_name]
        
        # 如果配置文件中没有，尝试从独立的JSON文件加载
        template_paths = [
            f"src/templates/{template_name}.json",
            f"templates/{template_name}.json",
            f"config/templates/{template_name}.json"
        ]
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                        logger.debug(f"加载模板文件: {template_path}")
                        return template_data
                except Exception as e:
                    logger.warning(f"模板文件加载失败 {template_path}: {e}")
        
        raise ValueError(f"提示词模板 {template_name} 不存在")
    
    def format_prompt(self, template_name: str, **kwargs) -> str:
        """格式化提示词"""
        template = self.get_prompt_template(template_name)
        
        # 处理JSON格式的模板
        if isinstance(template, dict) and "instruction" in template:
            # 构建完整的提示词
            prompt_parts = []
            
            # 添加指令
            prompt_parts.append(template["instruction"])
            
            # 添加上下文
            if "context" in template:
                try:
                    formatted_context = template["context"].format(**kwargs)
                    prompt_parts.append(formatted_context)
                except KeyError as e:
                    logger.warning(f"上下文格式化失败，缺少参数: {e}")
                    prompt_parts.append(template["context"])
            
            # 添加任务描述
            if "task" in template:
                prompt_parts.append(template["task"])
            
            # 添加输出格式说明
            if "output_format" in template:
                prompt_parts.append("请按照以下格式返回结果：")
                prompt_parts.append(json.dumps(template["output_format"], ensure_ascii=False, indent=2))
            
            # 添加指导原则
            if "guidelines" in template:
                prompt_parts.append("请遵循以下指导原则：")
                for guideline in template["guidelines"]:
                    prompt_parts.append(f"- {guideline}")
            
            # 添加响应格式要求
            if "response_format" in template:
                prompt_parts.append(template["response_format"])
            
            return "\n\n".join(prompt_parts)
        
        # 处理配置文件格式的模板
        else:
            # 获取系统提示词和用户提示词
            system_prompt = template.get("system", "")
            user_prompt = template.get("user", "")
            
            # 格式化提示词
            try:
                formatted_user = user_prompt.format(**kwargs)
                return f"{system_prompt}\n\n{formatted_user}"
            except KeyError as e:
                raise ValueError(f"提示词模板缺少参数: {e}")
    
    async def analyze_requirements(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """分析需求 - 便捷方法"""
        response = await self.generate(
            template_name="requirements_extraction", 
            input_text=input_text, 
            **kwargs
        )
        
        try:
            # 尝试解析JSON响应
            return json.loads(response.content)
        except json.JSONDecodeError:
            # 如果不是JSON，返回原始文本
            return {"raw_response": response.content}
    
    async def check_quality(self, requirements: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """质量检查 - 便捷方法"""
        response = await self.generate(
            template_name="quality_check",
            requirements=json.dumps(requirements, ensure_ascii=False),
            analysis=json.dumps(analysis, ensure_ascii=False),
            **kwargs
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"raw_response": response.content}
    
    async def generate_documentation(self, requirements: Dict[str, Any], analysis: Dict[str, Any], quality_report: Dict[str, Any]) -> str:
        """生成文档 - 便捷方法"""
        response = await self.generate(
            template_name="documentation_generation",
            requirements=json.dumps(requirements, ensure_ascii=False),
            analysis=json.dumps(analysis, ensure_ascii=False),
            quality_report=json.dumps(quality_report, ensure_ascii=False),
            format="markdown",
            template="standard",
            **kwargs
        )
        return response.content
    
    async def close(self):
        """关闭所有连接"""
        for provider in self.providers.values():
            if hasattr(provider, 'client') and hasattr(provider.client, 'aclose'):
                await provider.client.aclose()

# 全局LLM管理器实例
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

def set_llm_provider(provider: str):
    """设置LLM提供商"""
    get_llm_manager().set_provider(provider)

async def generate_text(prompt: str, **kwargs) -> str:
    """生成文本的便捷函数"""
    response = await get_llm_manager().generate(prompt, **kwargs)
    return response.content 