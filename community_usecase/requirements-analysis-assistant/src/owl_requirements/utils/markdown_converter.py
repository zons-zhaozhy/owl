from typing import Dict, Any
from loguru import logger


class RequirementsMarkdownConverter:
    """需求文档的Markdown转换器"""

    def __init__(self):
        """初始化转换器"""
        pass

    def convert(self, documentation: Dict[str, Any]) -> str:
        """
        将文档转换为Markdown格式。

        Args:
            documentation: 文档数据字典

        Returns:
            str: Markdown格式的文档内容
        """
        return convert_json_to_markdown(documentation)

    def convert_requirements(self, requirements: Dict[str, Any]) -> str:
        """
        将需求数据转换为Markdown格式。

        Args:
            requirements: 需求数据字典

        Returns:
            str: Markdown格式的需求文档
        """
        md_content = []

        # 标题
        md_content.append("# 需求文档")
        md_content.append("")

        # 功能需求
        if "functional_requirements" in requirements:
            md_content.append("## 功能需求")
            md_content.append("")
            for req in requirements["functional_requirements"]:
                md_content.append(f"### {req.get('title', 'N/A')}")
                md_content.append(f"**ID**: {req.get('id', 'N/A')}")
                md_content.append(f"**描述**: {req.get('description', 'N/A')}")
                md_content.append(f"**优先级**: {req.get('priority', 'N/A')}")
                md_content.append("")

        # 非功能需求
        if "non_functional_requirements" in requirements:
            md_content.append("## 非功能需求")
            md_content.append("")
            for req in requirements["non_functional_requirements"]:
                md_content.append(f"### {req.get('title', 'N/A')}")
                md_content.append(f"**ID**: {req.get('id', 'N/A')}")
                md_content.append(f"**描述**: {req.get('description', 'N/A')}")
                md_content.append(f"**类别**: {req.get('category', 'N/A')}")
                md_content.append("")

        return "\n".join(md_content)


def convert_json_to_markdown(documentation: Dict[str, Any]) -> str:
    """Converts the generated documentation (JSON) to Markdown format.

    Args:
        documentation: The documentation dictionary in JSON format.

    Returns:
        The documentation formatted as a Markdown string.
    """
    if not documentation or "documentation" not in documentation:
        logger.warning("Invalid documentation for Markdown conversion.")
        return "# 文档内容缺失"

    doc_data = documentation["documentation"]
    md_content = []

    # Project Overview
    overview = doc_data.get("project_overview", {})
    md_content.append("# 项目概述")
    md_content.append(f"**项目名称**: {overview.get('title', 'N/A')}")
    md_content.append(f"**版本**: {overview.get('version', 'N/A')}")
    md_content.append(f"**日期**: {overview.get('date', 'N/A')}")
    md_content.append(f"**状态**: {overview.get('status', 'N/A')}")
    authors = ", ".join(overview.get("authors", ["N/A"]))
    md_content.append(f"**作者**: {authors}")
    reviewers = ", ".join(overview.get("reviewers", ["N/A"]))
    md_content.append(f"**审阅者**: {reviewers}")
    approvers = ", ".join(overview.get("approvers", ["N/A"]))
    md_content.append(f"**批准者**: {approvers}")
    md_content.append("")  # Blank line for spacing

    # Executive Summary
    summary = doc_data.get("executive_summary", {})
    md_content.append("## 执行摘要")
    md_content.append(f"**项目背景**: {summary.get('background', 'N/A')}")
    md_content.append("**目标**:")
    for obj in summary.get("objectives", []):
        md_content.append(f"- {obj}")
    md_content.append("**范围**:")
    scope = summary.get("scope", {})
    in_scope = ", ".join(scope.get("in_scope", ["N/A"]))
    out_scope = ", ".join(scope.get("out_of_scope", ["N/A"]))
    md_content.append(f"  - **在内**: {in_scope}")
    md_content.append(f"  - **排除**: {out_scope}")
    stakeholders = ", ".join(summary.get("stakeholders", ["N/A"]))
    md_content.append(f"**干系人**: {stakeholders}")
    md_content.append("")  # Blank line for spacing

    # Requirements Specification
    req_spec = doc_data.get("requirements_specification", {})
    md_content.append("## 需求规格说明")
    md_content.append("### 功能需求")
    for req in req_spec.get("functional_requirements", []):
        req_id = req.get("id", "N/A")
        title = req.get("title", "N/A")
        md_content.append(f"- **{req_id}**: {title}")
        md_content.append(f"  - **描述**: {req.get('description', 'N/A')}")
        md_content.append(f"  - **优先级**: {req.get('priority', 'N/A')}")
        md_content.append(f"  - **状态**: {req.get('status', 'N/A')}")
        md_content.append("  - **验收标准**:")
        for ac in req.get("acceptance_criteria", []):
            md_content.append(f"    - {ac}")
    md_content.append("### 非功能需求")
    for req in req_spec.get("non_functional_requirements", []):
        req_id = req.get("id", "N/A")
        category = req.get("category", "N/A")
        description = req.get("description", "N/A")
        md_content.append(f"- **{req_id}** ({category}): {description}")
        constraints = ", ".join(req.get("constraints", ["N/A"]))
        md_content.append(f"  - **约束**: {constraints}")
        md_content.append(f"  - **测量标准**: {req.get('measurement', 'N/A')}")
    md_content.append("")  # Blank line for spacing

    # Analysis Results
    analysis_results = doc_data.get("analysis_results", {})
    md_content.append("## 分析结果")
    md_content.append("### 可行性分析")
    for key, val in analysis_results.get("feasibility", {}).items():
        md_content.append(f"- **{key.capitalize()}可行性**:")
        md_content.append(f"  - **评分**: {val.get('score', 'N/A')}")
        md_content.append(f"  - **总结**: {val.get('summary', 'N/A')}")
        challenges = ", ".join(val.get("challenges", ["N/A"]))
        md_content.append(f"  - **挑战**: {challenges}")
        recommendations = ", ".join(val.get("recommendations", ["N/A"]))
        md_content.append(f"  - **建议**: {recommendations}")
    md_content.append("### 依赖关系")
    md_content.append("#### 内部依赖")
    dependencies = analysis_results.get("dependencies", {})
    for dep in dependencies.get("internal", []):
        md_content.append(f"- **从**: {dep.get('from', 'N/A')}")
        md_content.append(f"  - **到**: {dep.get('to', 'N/A')}")
        md_content.append(f"  - **类型**: {dep.get('type', 'N/A')}")
        md_content.append(f"  - **描述**: {dep.get('description', 'N/A')}")
    md_content.append("#### 外部依赖")
    for dep in dependencies.get("external", []):
        md_content.append(f"- **名称**: {dep.get('name', 'N/A')}")
        md_content.append(f"  - **类型**: {dep.get('type', 'N/A')}")
        md_content.append(f"  - **描述**: {dep.get('description', 'N/A')}")
    md_content.append("")  # Blank line for spacing

    # Quality Assessment
    quality_assessment = doc_data.get("quality_assessment", {})
    md_content.append("## 质量评估")
    overall_score = quality_assessment.get("overall_score", "N/A")
    md_content.append(f"**总体评分**: {overall_score}")
    summary_text = quality_assessment.get("summary", "N/A")
    md_content.append(f"**总结**: {summary_text}")
    md_content.append("### 质量指标")
    for metric_type, metrics_data in quality_assessment.get("metrics", {}).items():
        md_content.append(f"- **{metric_type.capitalize()}**:")
        md_content.append(f"  - **评分**: {metrics_data.get('score', 'N/A')}")
        findings = ", ".join(metrics_data.get("findings", ["N/A"]))
        md_content.append(f"  - **发现**: {findings}")
        recommendations = ", ".join(metrics_data.get("recommendations", ["N/A"]))
        md_content.append(f"  - **建议**: {recommendations}")
    md_content.append("")  # Blank line for spacing

    # Implementation Plan
    impl_plan = doc_data.get("implementation_plan", {})
    md_content.append("## 实施计划")
    md_content.append("### 阶段")
    for phase in impl_plan.get("phases", []):
        md_content.append(f"- **名称**: {phase.get('name', 'N/A')}")
        md_content.append(f"  - **持续时间**: {phase.get('duration', 'N/A')}")
        deliverables = ", ".join(phase.get("deliverables", ["N/A"]))
        md_content.append(f"  - **交付物**: {deliverables}")
        milestones = ", ".join(phase.get("milestones", ["N/A"]))
        md_content.append(f"  - **里程碑**: {milestones}")
    md_content.append("### 风险")
    for risk in impl_plan.get("risks", []):
        risk_id = risk.get("id", "N/A")
        description = risk.get("description", "N/A")
        md_content.append(f"- **{risk_id}**: {description}")
        md_content.append(f"  - **可能性**: {risk.get('probability', 'N/A')}")
        md_content.append(f"  - **影响**: {risk.get('impact', 'N/A')}")
        mitigation = ", ".join(risk.get("mitigation", ["N/A"]))
        md_content.append(f"  - **缓解措施**: {mitigation}")
    assumptions = ", ".join(impl_plan.get("assumptions", ["N/A"]))
    md_content.append(f"**假设**: {assumptions}")
    constraints = ", ".join(impl_plan.get("constraints", ["N/A"]))
    md_content.append(f"**约束**: {constraints}")
    md_content.append("")  # Blank line for spacing

    # Metadata
    metadata = documentation.get("metadata", {})
    md_content.append("## 元数据")
    md_content.append(f"**生成时间**: {metadata.get('generated_at', 'N/A')}")
    md_content.append(f"**版本**: {metadata.get('version', 'N/A')}")
    md_content.append(f"**格式**: {metadata.get('format', 'N/A')}")
    md_content.append(f"**生成器**: {metadata.get('generator', 'N/A')}")
    md_content.append("")  # Blank line for spacing

    return "\n".join(md_content)


def convert_to_markdown(data: Dict[str, Any]) -> str:
    """
    通用的Markdown转换函数。

    Args:
        data: 要转换的数据字典

    Returns:
        str: Markdown格式的内容
    """
    converter = RequirementsMarkdownConverter()
    return converter.convert(data)
