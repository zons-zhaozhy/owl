"""Core data models for the requirements analysis system."""

from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import json

class RequirementType(str, Enum):
    """需求类型枚举"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"

class Priority(str, Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Requirement:
    """单个需求数据模型"""
    id: str
    title: str
    description: str
    priority: Priority
    type: RequirementType
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "type": self.type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """从字典创建需求对象"""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=Priority(data["priority"]),
            type=RequirementType(data["type"])
        )

@dataclass
class ClarificationRequest:
    """澄清请求数据模型"""
    question: str
    options: Optional[List[str]] = None
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"question": self.question}
        if self.options:
            result["options"] = self.options
        if self.context:
            result["context"] = self.context
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClarificationRequest":
        """从字典创建澄清请求对象"""
        return cls(
            question=data["question"],
            options=data.get("options"),
            context=data.get("context")
        )

@dataclass
class ExtractionResult:
    """需求提取结果数据模型"""
    requirements: List[Requirement]
    clarification_needed: Optional[ClarificationRequest] = None
    requirements_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "requirements": [req.to_dict() for req in self.requirements],
            "requirements_complete": self.requirements_complete
        }
        
        if self.clarification_needed:
            result["clarification_needed"] = self.clarification_needed.to_dict()
        else:
            result["clarification_needed"] = None
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionResult":
        """从字典创建提取结果对象"""
        requirements = [Requirement.from_dict(req) for req in data.get("requirements", [])]
        
        clarification_data = data.get("clarification_needed")
        clarification = None
        if clarification_data and isinstance(clarification_data, dict):
            clarification = ClarificationRequest.from_dict(clarification_data)
        elif clarification_data and isinstance(clarification_data, str):
            # 兼容字符串格式的澄清请求
            clarification = ClarificationRequest(question=clarification_data)
            
        return cls(
            requirements=requirements,
            clarification_needed=clarification,
            requirements_complete=data.get("requirements_complete", False)
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

@dataclass
class QualityScore:
    """质量评分数据模型"""
    score: int
    details: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "score": self.score,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityScore":
        """从字典创建质量评分对象"""
        return cls(
            score=data.get("score", 0),
            details=data.get("details", [])
        )

@dataclass
class QualityReport:
    """质量报告数据模型"""
    requirements_quality: QualityScore
    analysis_quality: QualityScore
    issues: List[str]
    suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "quality_score": {
                "requirements_quality": self.requirements_quality.to_dict(),
                "analysis_quality": self.analysis_quality.to_dict()
            },
            "issues": self.issues,
            "suggestions": self.suggestions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityReport":
        """从字典创建质量报告对象"""
        quality_score = data.get("quality_score", {})
        return cls(
            requirements_quality=QualityScore.from_dict(quality_score.get("requirements_quality", {})),
            analysis_quality=QualityScore.from_dict(quality_score.get("analysis_quality", {})),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", [])
        )

def validate_extraction_data(data: Dict[str, Any]) -> ExtractionResult:
    """验证并转换提取数据
    
    Args:
        data: 原始数据字典
        
    Returns:
        验证后的ExtractionResult对象
        
    Raises:
        ValueError: 数据格式不正确时
    """
    try:
        # 基本字段验证
        if not isinstance(data, dict):
            raise ValueError(f"数据必须是字典格式，当前类型: {type(data)}")
        
        # 验证requirements字段
        requirements_data = data.get("requirements", [])
        if not isinstance(requirements_data, list):
            raise ValueError(f"requirements字段必须是列表，当前类型: {type(requirements_data)}")
        
        # 验证每个需求项
        requirements = []
        for i, req_data in enumerate(requirements_data):
            if not isinstance(req_data, dict):
                raise ValueError(f"需求项 {i} 必须是字典格式，当前类型: {type(req_data)}")
            
            # 检查必需字段
            required_fields = ["id", "title", "description", "priority", "type"]
            missing_fields = [field for field in required_fields if field not in req_data]
            if missing_fields:
                raise ValueError(f"需求项 {i} 缺少必需字段: {missing_fields}")
            
            # 验证枚举值
            try:
                priority = Priority(req_data["priority"])
                req_type = RequirementType(req_data["type"])
            except ValueError as e:
                raise ValueError(f"需求项 {i} 包含无效的枚举值: {e}")
            
            requirements.append(Requirement(
                id=req_data["id"],
                title=req_data["title"],
                description=req_data["description"],
                priority=priority,
                type=req_type
            ))
        
        # 处理澄清请求
        clarification = None
        clarification_data = data.get("clarification_needed")
        
        if clarification_data is not None:
            if isinstance(clarification_data, str):
                clarification = ClarificationRequest(question=clarification_data)
            elif isinstance(clarification_data, dict):
                if "question" not in clarification_data:
                    raise ValueError("澄清请求必须包含question字段")
                clarification = ClarificationRequest.from_dict(clarification_data)
            elif not isinstance(clarification_data, bool):
                raise ValueError(f"clarification_needed字段类型无效: {type(clarification_data)}")
        
        # 获取完整性标志
        requirements_complete = data.get("requirements_complete", False)
        if not isinstance(requirements_complete, bool):
            raise ValueError(f"requirements_complete字段必须是布尔值，当前类型: {type(requirements_complete)}")
        
        return ExtractionResult(
            requirements=requirements,
            clarification_needed=clarification,
            requirements_complete=requirements_complete
        )
        
    except Exception as e:
        raise ValueError(f"数据验证失败: {str(e)}") 