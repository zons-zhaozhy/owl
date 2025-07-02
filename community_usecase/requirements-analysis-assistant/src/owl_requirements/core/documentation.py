"""
需求文档生成器模块

此模块提供了用于生成结构化需求文档的核心功能。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.exceptions import (
    DocumentationError,
    TemplateError,
    ValidationError,
)
from ..utils.json_utils import load_json_safe, save_json_safe

logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """项目信息数据类"""

    name: str
    description: str
    version: str


@dataclass
class Requirement:
    """需求数据类"""

    id: str
    title: str
    description: str
    category: Optional[str] = None


@dataclass
class Requirements:
    """需求集合数据类"""

    functional: List[Requirement]
    non_functional: List[Requirement]


@dataclass
class Analysis:
    """分析结果数据类"""

    feasibility: float
    complexity: float
    risks: Dict[str, List[str]]


@dataclass
class QualityMetrics:
    """质量指标数据类"""

    overall_score: float
    metrics: Dict[str, float]
    improvements: List[str]


class DocumentationGenerator:
    """需求文档生成器类"""

    def __init__(self, template_path: Union[str, Path]):
        """
        初始化文档生成器

        Args:
            template_path: 文档模板文件路径
        """
        self.template_path = Path(template_path)
        self.template = self._load_template()
        logger.info(f"已初始化文档生成器，使用模板：{template_path}")

    def _load_template(self) -> Dict[str, Any]:
        """
        加载文档模板

        Returns:
            Dict[str, Any]: 模板数据
        """
        try:
            return load_json_safe(self.template_path)
        except Exception as e:
            raise TemplateError(f"加载模板失败：{e}") from e

    def _validate_project_info(self, info: Dict[str, Any]) -> ProjectInfo:
        """
        验证项目信息

        Args:
            info: 项目信息字典

        Returns:
            ProjectInfo: 验证后的项目信息对象
        """
        try:
            return ProjectInfo(
                name=info["name"],
                description=info["description"],
                version=info["version"],
            )
        except KeyError as e:
            raise ValidationError(f"项目信息缺少必要字段：{e}") from e

    def _validate_requirements(
        self, reqs: Dict[str, List[Dict[str, Any]]]
    ) -> Requirements:
        """
        验证需求数据

        Args:
            reqs: 需求数据字典

        Returns:
            Requirements: 验证后的需求对象
        """
        try:
            functional = [Requirement(**req) for req in reqs.get("functional", [])]
            non_functional = [
                Requirement(**req) for req in reqs.get("non_functional", [])
            ]
            return Requirements(functional=functional, non_functional=non_functional)
        except (KeyError, TypeError) as e:
            raise ValidationError(f"需求数据格式错误：{e}") from e

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Analysis:
        """
        验证分析结果

        Args:
            analysis: 分析结果字典

        Returns:
            Analysis: 验证后的分析对象
        """
        try:
            return Analysis(
                feasibility=float(analysis["feasibility"]),
                complexity=float(analysis["complexity"]),
                risks=analysis["risks"],
            )
        except (KeyError, ValueError) as e:
            raise ValidationError(f"分析结果格式错误：{e}") from e

    def _validate_quality(self, quality: Dict[str, Any]) -> QualityMetrics:
        """
        验证质量指标

        Args:
            quality: 质量指标字典

        Returns:
            QualityMetrics: 验证后的质量指标对象
        """
        try:
            return QualityMetrics(
                overall_score=float(quality["overall_score"]),
                metrics=quality["metrics"],
                improvements=quality["improvements"],
            )
        except (KeyError, ValueError) as e:
            raise ValidationError(f"质量指标格式错误：{e}") from e

    def generate_documentation(
        self,
        project_info: Dict[str, Any],
        requirements: Dict[str, List[Dict[str, Any]]],
        analysis: Dict[str, Any],
        quality: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成需求文档

        Args:
            project_info: 项目信息
            requirements: 需求数据
            analysis: 分析结果
            quality: 质量指标
            output_path: 输出文件路径（可选）

        Returns:
            Dict[str, Any]: 生成的文档数据
        """
        try:
            # 验证输入数据
            validated_info = self._validate_project_info(project_info)
            validated_reqs = self._validate_requirements(requirements)
            validated_analysis = self._validate_analysis(analysis)
            validated_quality = self._validate_quality(quality)

            # 生成文档结构
            doc = {
                "project": {
                    "name": validated_info.name,
                    "description": validated_info.description,
                    "version": validated_info.version,
                },
                "requirements": {
                    "functional": [
                        {
                            "id": req.id,
                            "title": req.title,
                            "description": req.description,
                        }
                        for req in validated_reqs.functional
                    ],
                    "non_functional": [
                        {
                            "id": req.id,
                            "title": req.title,
                            "description": req.description,
                            "category": req.category,
                        }
                        for req in validated_reqs.non_functional
                    ],
                },
                "analysis": {
                    "feasibility_score": validated_analysis.feasibility,
                    "complexity_score": validated_analysis.complexity,
                    "risk_assessment": validated_analysis.risks,
                },
                "quality": {
                    "overall_quality_score": validated_quality.overall_score,
                    "quality_metrics": validated_quality.metrics,
                    "improvement_suggestions": validated_quality.improvements,
                },
                "metadata": {
                    "generated_at": "2024-03-21T10:00:00Z",
                    "generator_version": "1.0.0",
                },
            }

            # 保存文档（如果指定了输出路径）
            if output_path:
                save_json_safe(doc, output_path)
                logger.info(f"文档已保存至：{output_path}")

            return doc

        except (ValidationError, TemplateError) as e:
            raise DocumentationError(f"生成文档失败：{e}") from e
        except Exception as e:
            raise DocumentationError(f"生成文档时发生未知错误：{e}") from e
