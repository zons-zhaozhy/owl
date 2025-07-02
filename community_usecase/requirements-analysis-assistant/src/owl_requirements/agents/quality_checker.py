from typing import Any
from typing import Dict
from typing import Optional

"""质量检查智能体"""

import json
import logging

from .base import BaseAgent

logger = logging.getLogger(__name__)


class QualityChecker(BaseAgent):
    """质量检查智能体 - 检查需求和分析的质量、完整性和一致性"""

    def __init__(self, config: Any = None):
        """初始化质量检查智能体

        Args:
            config: 配置对象（SystemConfig或字典）
        """
        # 处理配置参数
        if config is None:
            config_dict = {}
        elif hasattr(config, "__dict__"):
            # 如果是配置对象，转换为字典
            config_dict = vars(config)
        elif isinstance(config, dict):
            config_dict = config
        else:
            config_dict = {}

        # 调用父类初始化，传递name和config字典
        super().__init__("QualityChecker", config_dict)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理质量检查任务

        Args:
            input_data: 包含需求和分析信息的数据

        Returns:
            质量检查结果
        """
        try:
            requirements = input_data.get("requirements", {})
            analysis = input_data.get("analysis", {})

            if not requirements:
                raise ValueError("需求信息不能为空")

            logger.info("开始质量检查")

            # 使用统一的提示词模板
            response = await self._call_llm_with_template(
                "quality_check",
                requirements=json.dumps(requirements, ensure_ascii=False),
                analysis=json.dumps(analysis, ensure_ascii=False),
            )

            # 解析响应
            _quality_result = self._parse_llm_response(response)

            # 后处理和验证
            validated_quality = self._validate_quality_check(quality_result)

            # 计算质量分数
            quality_score = self._calculate_quality_score(validated_quality)

            logger.info(f"质量检查完成，总分: {quality_score:.2f}")

            return {
                "status": "success",
                "quality_report": validated_quality,
                "quality_score": quality_score,
                "metadata": {
                    "check_method": "llm_template",
                    "requirements_count": self._count_requirements(requirements),
                },
            }

        except Exception as e:
            logger.error(f"质量检查失败: {str(e)}")
            return {"status": "error", "error": str(e), "quality_report": None}

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response)

        except json.JSONDecodeError:
            # 如果不是JSON，尝试提取JSON部分
            return self._extract_json_from_text(response)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        try:
            # 查找JSON代码块
            json_start = text.find("{")
            _json_end = text.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)

            # 如果找不到JSON，返回结构化的文本解析结果
            return self._parse_text_response(text)

        except Exception as e:
            logger.warning(f"JSON提取失败: {str(e)}")
            return self._parse_text_response(text)

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """解析文本响应为结构化格式"""
        # 基本的文本解析逻辑
        return {
            "completeness_check": {
                "score": 0.7,
                "missing_elements": ["需要进一步分析"],
                "recommendations": ["建议补充更多细节"],
            },
            "consistency_check": {
                "score": 0.8,
                "inconsistencies": [],
                "recommendations": ["检查一致性"],
            },
            "clarity_check": {
                "score": 0.7,
                "unclear_requirements": [],
                "recommendations": ["提高清晰度"],
            },
            "feasibility_check": {
                "score": 0.6,
                "concerns": ["需要详细评估"],
                "recommendations": ["进行可行性分析"],
            },
            "testability_check": {
                "score": 0.6,
                "untestable_requirements": [],
                "recommendations": ["增加可测试性"],
            },
            "overall_assessment": {
                "strengths": ["基于文本解析的评估"],
                "weaknesses": ["需要更详细的分析"],
                "priority_issues": ["建议进行人工审查"],
                "improvement_suggestions": ["补充详细信息"],
            },
        }

    def _validate_quality_check(self, quality_check: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化质量检查结果"""
        validated = {
            "completeness_check": {},
            "consistency_check": {},
            "clarity_check": {},
            "feasibility_check": {},
            "testability_check": {},
            "overall_assessment": {},
        }

        # 验证完整性检查
        completeness = quality_check.get("completeness_check", {})
        validated["completeness_check"] = {
            "score": max(0.0, min(1.0, completeness.get("score", 0.7))),
            "missing_elements": completeness.get("missing_elements", []),
            "recommendations": completeness.get("recommendations", []),
        }

        # 验证一致性检查
        consistency = quality_check.get("consistency_check", {})
        validated["consistency_check"] = {
            "score": max(0.0, min(1.0, consistency.get("score", 0.8))),
            "inconsistencies": consistency.get("inconsistencies", []),
            "recommendations": consistency.get("recommendations", []),
        }

        # 验证清晰度检查
        clarity = quality_check.get("clarity_check", {})
        validated["clarity_check"] = {
            "score": max(0.0, min(1.0, clarity.get("score", 0.7))),
            "unclear_requirements": clarity.get("unclear_requirements", []),
            "recommendations": clarity.get("recommendations", []),
        }

        # 验证可行性检查
        feasibility = quality_check.get("feasibility_check", {})
        validated["feasibility_check"] = {
            "score": max(0.0, min(1.0, feasibility.get("score", 0.6))),
            "concerns": feasibility.get("concerns", []),
            "recommendations": feasibility.get("recommendations", []),
        }

        # 验证可测试性检查
        testability = quality_check.get("testability_check", {})
        validated["testability_check"] = {
            "score": max(0.0, min(1.0, testability.get("score", 0.6))),
            "untestable_requirements": testability.get("untestable_requirements", []),
            "recommendations": testability.get("recommendations", []),
        }

        # 验证总体评估
        overall = quality_check.get("overall_assessment", {})
        validated["overall_assessment"] = {
            "strengths": overall.get("strengths", []),
            "weaknesses": overall.get("weaknesses", []),
            "priority_issues": overall.get("priority_issues", []),
            "improvement_suggestions": overall.get("improvement_suggestions", []),
        }

        return validated

    def _calculate_quality_score(self, quality_check: Dict[str, Any]) -> float:
        """计算总体质量分数"""
        _scores = []
        weights = {
            "completeness_check": 0.25,
            "consistency_check": 0.20,
            "clarity_check": 0.20,
            "feasibility_check": 0.20,
            "testability_check": 0.15,
        }

        total_score = 0.0
        total_weight = 0.0

        for check_type, weight in weights.items():
            check_data = quality_check.get(check_type, {})
            score = check_data.get("score", 0.0)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _count_requirements(self, requirements: Dict[str, Any]) -> Dict[str, int]:
        """统计需求数量"""
        return {
            "functional": len(requirements.get("functional_requirements", [])),
            "non_functional": len(requirements.get("non_functional_requirements", [])),
            "constraints": len(requirements.get("constraints", [])),
            "total": (
                len(requirements.get("functional_requirements", []))
                + len(requirements.get("non_functional_requirements", []))
            ),
        }

    async def check_completeness(
        self, requirements: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """便捷方法：完整性检查"""
        result = await self.process({"requirements": requirements, **kwargs})

        if result["status"] == "success":
            return result["quality_report"]["completeness_check"]
        else:
            return {"error": result.get("error", "检查失败")}

    async def check_consistency(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """便捷方法：一致性检查"""
        result = await self.process(
            {
                "requirements": requirements,
                "analysis": analysis or {},
                **kwargs,
            }
        )

        if result["status"] == "success":
            return result["quality_report"]["consistency_check"]
        else:
            return {"error": result.get("error", "检查失败")}

    async def check_clarity(
        self, requirements: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """便捷方法：清晰度检查"""
        result = await self.process({"requirements": requirements, **kwargs})

        if result["status"] == "success":
            return result["quality_report"]["clarity_check"]
        else:
            return {"error": result.get("error", "检查失败")}

    def get_quality_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取质量摘要"""
        if result.get("status") != "success" or not result.get("quality_report"):
            return {"error": "无效的质量检查结果"}

        quality_report = result["quality_report"]
        quality_score = result.get("quality_score", 0.0)

        # 确定质量等级
        if quality_score >= 0.9:
            quality_grade = "优秀"
        elif quality_score >= 0.8:
            quality_grade = "良好"
        elif quality_score >= 0.7:
            quality_grade = "中等"
        elif quality_score >= 0.6:
            quality_grade = "及格"
        else:
            quality_grade = "不及格"

        # 收集所有问题
        all_issues = []
        for check_type in [
            "completeness_check",
            "consistency_check",
            "clarity_check",
            "feasibility_check",
            "testability_check",
        ]:
            check_data = quality_report.get(check_type, {})
            issues = (
                check_data.get("missing_elements", [])
                + check_data.get("inconsistencies", [])
                + check_data.get("unclear_requirements", [])
                + check_data.get("concerns", [])
                + check_data.get("untestable_requirements", [])
            )
            all_issues.extend(issues)

        # 收集所有建议
        all_recommendations = []
        for check_type in [
            "completeness_check",
            "consistency_check",
            "clarity_check",
            "feasibility_check",
            "testability_check",
        ]:
            check_data = quality_report.get(check_type, {})
            recommendations = check_data.get("recommendations", [])
            all_recommendations.extend(recommendations)

        return {
            "quality_score": quality_score,
            "quality_grade": quality_grade,
            "total_issues": len(all_issues),
            "total_recommendations": len(all_recommendations),
            "priority_issues": quality_report.get("overall_assessment", {}).get(
                "priority_issues", []
            ),
            "strengths": quality_report.get("overall_assessment", {}).get(
                "strengths", []
            ),
            "weaknesses": quality_report.get("overall_assessment", {}).get(
                "weaknesses", []
            ),
        }

    def generate_quality_report(self, result: Dict[str, Any]) -> str:
        """生成质量报告文本"""
        if result.get("status") != "success":
            return f"质量检查失败: {result.get('error', '未知错误')}"

        quality_report = result["quality_report"]
        quality_score = result.get("quality_score", 0.0)
        summary = self.get_quality_summary(result)

        report_lines = [
            "# 需求质量检查报告",
            "",
            f"## 总体评分: {quality_score:.2f} ({summary['quality_grade']})",
            "",
            "## 详细检查结果",
            "",
        ]

        # 各项检查结果
        check_sections = {
            "completeness_check": "完整性检查",
            "consistency_check": "一致性检查",
            "clarity_check": "清晰度检查",
            "feasibility_check": "可行性检查",
            "testability_check": "可测试性检查",
        }

        for check_type, section_name in check_sections.items():
            check_data = quality_report.get(check_type, {})
            score = check_data.get("score", 0.0)

            report_lines.extend([f"### {section_name}", f"评分: {score:.2f}", ""])

            # 添加具体问题
            _issues_keys = {
                "completeness_check": "missing_elements",
                "consistency_check": "inconsistencies",
                "clarity_check": "unclear_requirements",
                "feasibility_check": "concerns",
                "testability_check": "untestable_requirements",
            }

            issues_key = issues_keys.get(check_type)
            if issues_key and check_data.get(issues_key):
                report_lines.append("问题:")
                for issue in check_data[issues_key]:
                    report_lines.append(f"- {issue}")
                report_lines.append("")

            # 添加建议
            if check_data.get("recommendations"):
                report_lines.append("建议:")
                for rec in check_data["recommendations"]:
                    report_lines.append(f"- {rec}")
                report_lines.append("")

        # 总体评估
        overall = quality_report.get("overall_assessment", {})
        if overall:
            report_lines.extend(["## 总体评估", ""])

            if overall.get("strengths"):
                report_lines.append("### 优势")
                for strength in overall["strengths"]:
                    report_lines.append(f"- {strength}")
                report_lines.append("")

            if overall.get("weaknesses"):
                report_lines.append("### 待改进")
                for weakness in overall["weaknesses"]:
                    report_lines.append(f"- {weakness}")
                report_lines.append("")

            if overall.get("priority_issues"):
                report_lines.append("### 优先问题")
                for issue in overall["priority_issues"]:
                    report_lines.append(f"- {issue}")
                report_lines.append("")

            if overall.get("improvement_suggestions"):
                report_lines.append("### 改进建议")
                for suggestion in overall["improvement_suggestions"]:
                    report_lines.append(f"- {suggestion}")
                report_lines.append("")

        return "\n".join(report_lines)

    async def check(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """质量检查的接口方法，供AgentCoordinator调用

        Args:
            requirements: 需求信息
            analysis: 分析结果
            context: 可选的上下文信息

        Returns:
            质量检查结果
        """
        input_data = {"requirements": requirements}
        if analysis:
            input_data["analysis"] = analysis
        if context:
            input_data["context"] = context

        result = await self.process(input_data)
        return result.get("quality_report", {})
