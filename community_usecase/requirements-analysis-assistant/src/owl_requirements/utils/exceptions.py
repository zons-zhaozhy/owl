"""
异常处理模块

定义需求分析系统中使用的自定义异常类。
"""

from typing import Dict, Any, Optional

class RequirementsError(Exception):
    """需求分析系统基础异常类"""
    
    def __init__(self, message: str = "", details: Optional[Dict[str, Any]] = None):
        """
        初始化需求错误异常。
        
        Args:
            message: 错误消息
            details: 错误详细信息字典
        """
        super().__init__(message)
        self.details = details or {}

class TemplateError(RequirementsError):
    """模板相关错误"""
    pass

class ValidationError(RequirementsError):
    """数据验证错误"""
    pass

class DocumentationError(RequirementsError):
    """文档生成错误"""
    pass

class ConfigError(RequirementsError):
    """配置错误"""
    pass

class AgentError(RequirementsError):
    """智能体错误"""
    pass

class ServiceError(RequirementsError):
    """服务错误"""
    pass

class LLMError(ServiceError):
    """LLM服务错误"""
    pass

class ExtractorError(RequirementsError):
    """提取器错误"""
    pass

class AnalysisError(RequirementsError):
    """需求分析错误"""
    pass

class QualityCheckError(RequirementsError):
    """质量检查错误"""
    pass 