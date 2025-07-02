"""
异常类模块。
"""


class OWLError(Exception):
    """OWL框架基础异常类"""

    pass


class ConfigurationError(OWLError):
    """配置错误"""

    pass


class ConfigError(ConfigurationError):
    """配置错误（兼容性别名）"""

    pass


class ExtractionError(OWLError):
    """需求提取错误"""

    pass


class AnalysisError(OWLError):
    """需求分析错误"""

    pass


class AnalyzerError(AnalysisError):
    """分析器错误（兼容性别名）"""

    pass


class ValidationError(OWLError):
    """验证错误"""

    pass


class DocumentationError(OWLError):
    """文档生成错误"""

    pass


class LLMError(OWLError):
    """LLM服务错误"""

    pass


class WebError(OWLError):
    """Web服务错误"""

    pass


class CLIError(OWLError):
    """CLI错误"""

    pass


class AgentError(OWLError):
    """智能体错误"""

    pass


class CoordinatorError(OWLError):
    """协调器错误"""

    pass


class RequirementsError(Exception):
    """需求分析助手基础异常类。"""

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
