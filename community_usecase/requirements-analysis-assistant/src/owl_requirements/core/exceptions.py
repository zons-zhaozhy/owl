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

class ValidationError(RequirementsAnalysisError):
    """数据验证错误。"""
    pass

class ConfigurationError(RequirementsAnalysisError):
    """配置相关错误。"""
    pass

class AgentError(RequirementsAnalysisError):
    """智能体相关错误。"""
    pass

class ServiceError(RequirementsAnalysisError):
    """服务层错误。"""
    pass

class StorageError(RequirementsAnalysisError):
    """存储相关错误。"""
    pass 