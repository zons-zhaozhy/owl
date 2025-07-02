"""
异常类模块。
"""

class RequirementsError(Exception):
    """需求分析助手基础异常类。"""
    pass


class ConfigurationError(RequirementsError):
    """配置错误异常。"""
    pass


class LLMError(RequirementsError):
    """LLM调用错误异常。"""
    pass


class ValidationError(RequirementsError):
    """数据验证错误异常。"""
    pass


class AgentError(RequirementsError):
    """智能体错误异常。"""
    pass


class StorageError(RequirementsError):
    """存储错误异常。"""
    pass

class RequirementsAnalysisError(Exception):
    """需求分析基础异常类。"""
    pass

class DocumentationGenerationError(RequirementsAnalysisError):
    """文档生成过程中的错误。"""
    pass

class InvalidInputError(RequirementsAnalysisError):
    """输入数据无效的错误。"""
    pass

class TemplateError(RequirementsAnalysisError):
    """模板相关的错误。"""
    pass

class LLMServiceError(RequirementsAnalysisError):
    """LLM服务相关的错误。"""
    pass

class ServiceError(RequirementsAnalysisError):
    """服务层错误。"""
    pass 