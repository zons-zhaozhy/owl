"""
测试异常模块
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import pytest

from src.owl_requirements.core.exceptions import (
    RequirementsError,
    RequirementsAnalysisError,
    ConfigurationError,
    LLMError,
    ValidationError,
    AgentError,
    StorageError,
    DocumentationGenerationError,
    InvalidInputError,
    TemplateError,
    LLMServiceError,
    ServiceError
)

class TestExceptions:
    """异常测试类"""
    
    def test_base_exception(self):
        """测试基础异常类"""
        error = RequirementsError("测试错误")
        assert str(error) == "测试错误"
        assert isinstance(error, Exception)
        
    def test_config_error(self):
        """测试配置错误"""
        error = ConfigurationError("配置错误")
        assert str(error) == "配置错误"
        assert isinstance(error, RequirementsError)
        
    def test_llm_error(self):
        """测试 LLM 错误"""
        error = LLMError("LLM 服务错误")
        assert str(error) == "LLM 服务错误"
        assert isinstance(error, RequirementsError)
        
    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("验证错误")
        assert str(error) == "验证错误"
        assert isinstance(error, RequirementsError)
        
    def test_agent_error(self):
        """测试智能体错误"""
        error = AgentError("智能体错误")
        assert str(error) == "智能体错误"
        assert isinstance(error, RequirementsError)
        
    def test_storage_error(self):
        """测试存储错误"""
        error = StorageError("存储错误")
        assert str(error) == "存储错误"
        assert isinstance(error, RequirementsError)
        
    def test_analysis_error(self):
        """测试需求分析错误"""
        error = RequirementsAnalysisError("分析错误")
        assert str(error) == "分析错误"
        assert isinstance(error, Exception)
        
    def test_documentation_error(self):
        """测试文档生成错误"""
        error = DocumentationGenerationError("文档生成错误")
        assert str(error) == "文档生成错误"
        assert isinstance(error, RequirementsAnalysisError)
        
    def test_invalid_input_error(self):
        """测试输入无效错误"""
        error = InvalidInputError("输入无效")
        assert str(error) == "输入无效"
        assert isinstance(error, RequirementsAnalysisError)
        
    def test_template_error(self):
        """测试模板错误"""
        error = TemplateError("模板错误")
        assert str(error) == "模板错误"
        assert isinstance(error, RequirementsAnalysisError)
        
    def test_llm_service_error(self):
        """测试LLM服务错误"""
        error = LLMServiceError("LLM服务错误")
        assert str(error) == "LLM服务错误"
        assert isinstance(error, RequirementsAnalysisError)
        
    def test_service_error(self):
        """测试服务错误"""
        error = ServiceError("服务错误")
        assert str(error) == "服务错误"
        assert isinstance(error, RequirementsAnalysisError)
        
    def test_error_inheritance(self):
        """测试错误继承关系"""
        assert issubclass(ConfigurationError, RequirementsError)
        assert issubclass(LLMError, RequirementsError)
        assert issubclass(ValidationError, RequirementsError)
        assert issubclass(AgentError, RequirementsError)
        assert issubclass(StorageError, RequirementsError)
        
        assert issubclass(DocumentationGenerationError, RequirementsAnalysisError)
        assert issubclass(InvalidInputError, RequirementsAnalysisError)
        assert issubclass(TemplateError, RequirementsAnalysisError)
        assert issubclass(LLMServiceError, RequirementsAnalysisError)
        assert issubclass(ServiceError, RequirementsAnalysisError) 