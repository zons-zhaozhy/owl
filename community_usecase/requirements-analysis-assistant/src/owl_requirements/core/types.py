"""
类型定义模块。
"""

from typing import List, TypedDict


class RequirementsResult(TypedDict):
    """需求提取结果。"""
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    constraints: List[str]


class AnalysisResult(TypedDict):
    """需求分析结果。"""
    technical_feasibility: List[str]
    resource_requirements: List[str]
    risk_analysis: List[str]


class QualityCheckResult(TypedDict):
    """质量检查结果。"""
    issues: List[str]
    recommendations: List[str]


class DocumentationResult(TypedDict):
    """文档生成结果。"""
    project_overview: List[str]
    requirements_list: List[str]
    technical_solution: List[str]
    implementation_plan: List[str]
    risk_management: List[str] 