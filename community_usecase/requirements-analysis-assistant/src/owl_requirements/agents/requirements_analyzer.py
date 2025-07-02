"""需求分析智能体"""

import json
import logging
from typing import Dict, Any, Optional, List

from .base import BaseAgent

logger = logging.getLogger(__name__)


class RequirementsAnalyzer(BaseAgent):
    """需求分析智能体 - 深入分析需求的可行性、复杂度和影响"""

    def __init__(self, config: Any = None):
        """初始化需求分析智能体

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
        super().__init__("RequirementsAnalyzer", config_dict)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理需求分析任务

        Args:
            input_data: 包含需求信息的数据

        Returns:
            分析结果
        """
        try:
            requirements = input_data.get("requirements", {})
            if not requirements:
                raise ValueError("需求信息不能为空")

            constraints = input_data.get("constraints", [])
            context = input_data.get("context", {})

            logger.info("开始需求分析")

            # 使用统一的提示词模板
            response = await self._call_llm_with_template(
                "requirements_analysis",
                requirements=json.dumps(requirements, ensure_ascii=False),
                constraints=json.dumps(constraints, ensure_ascii=False),
                _project_scope=context.get("project_scope", ""),
                _timeline=context.get("timeline", ""),
                _resources=context.get("resources", ""),
            )

            # 解析响应
            _analysis_result = self._parse_llm_response(response)

            # 后处理和验证
            validated_analysis = self._validate_analysis(analysis_result)

            logger.info("需求分析完成")

            return {
                "status": "success",
                "analysis": validated_analysis,
                "metadata": {
                    "requirements_count": self._count_requirements(requirements),
                    "analysis_method": "llm_template",
                },
            }

        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}")
            return {"status": "error", "error": str(e), "analysis": None}

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
            "feasibility_analysis": {
                "technical_feasibility": "medium",
                "resource_feasibility": "medium",
                "time_feasibility": "medium",
                "analysis_details": text,
            },
            "complexity_assessment": {
                "overall_complexity": "medium",
                "technical_complexity": "medium",
                "integration_complexity": "medium",
                "complexity_factors": ["需要进一步分析"],
            },
            "risk_analysis": [
                {
                    "risk_id": "RISK_001",
                    "description": "从文本解析的通用风险",
                    "probability": "medium",
                    "impact": "medium",
                    "mitigation": "需要详细评估",
                }
            ],
            "effort_estimation": {
                "development_effort": "待评估",
                "testing_effort": "待评估",
                "deployment_effort": "待评估",
                "total_effort": "待评估",
            },
            "recommendations": [
                {
                    "type": "process",
                    "description": "建议进行更详细的需求分析",
                    "rationale": "基于文本解析的建议",
                }
            ],
        }

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化分析结果"""
        validated = {
            "feasibility_analysis": {},
            "complexity_assessment": {},
            "risk_analysis": [],
            "effort_estimation": {},
            "recommendations": [],
        }

        # 验证可行性分析
        feasibility = analysis.get("feasibility_analysis", {})
        validated["feasibility_analysis"] = {
            "technical_feasibility": feasibility.get("technical_feasibility", "medium"),
            "resource_feasibility": feasibility.get("resource_feasibility", "medium"),
            "time_feasibility": feasibility.get("time_feasibility", "medium"),
            "analysis_details": feasibility.get("analysis_details", ""),
        }

        # 验证复杂度评估
        complexity = analysis.get("complexity_assessment", {})
        validated["complexity_assessment"] = {
            "overall_complexity": complexity.get("overall_complexity", "medium"),
            "technical_complexity": complexity.get("technical_complexity", "medium"),
            "integration_complexity": complexity.get(
                "integration_complexity", "medium"
            ),
            "complexity_factors": complexity.get("complexity_factors", []),
        }

        # 验证风险分析
        for risk in analysis.get("risk_analysis", []):
            if isinstance(risk, dict):
                validated_risk = {
                    "risk_id": risk.get(
                        "risk_id",
                        f"RISK_{len(validated['risk_analysis']) + 1:03d}",
                    ),
                    "description": risk.get("description", ""),
                    "probability": risk.get("probability", "medium"),
                    "impact": risk.get("impact", "medium"),
                    "mitigation": risk.get("mitigation", ""),
                }
                validated["risk_analysis"].append(validated_risk)

        # 验证工作量估算
        effort = analysis.get("effort_estimation", {})
        validated["effort_estimation"] = {
            "development_effort": effort.get("development_effort", "待评估"),
            "testing_effort": effort.get("testing_effort", "待评估"),
            "deployment_effort": effort.get("deployment_effort", "待评估"),
            "total_effort": effort.get("total_effort", "待评估"),
        }

        # 验证建议
        for rec in analysis.get("recommendations", []):
            if isinstance(rec, dict):
                validated_rec = {
                    "type": rec.get("type", "general"),
                    "description": rec.get("description", ""),
                    "rationale": rec.get("rationale", ""),
                }
                validated["recommendations"].append(validated_rec)

        return validated

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

    async def analyze_feasibility(
        self, requirements: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """便捷方法：可行性分析"""
        result = await self.process({"requirements": requirements, **kwargs})

        if result["status"] == "success":
            return result["analysis"]["feasibility_analysis"]
        else:
            return {"error": result.get("error", "分析失败")}

    async def assess_complexity(
        self, requirements: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """便捷方法：复杂度评估"""
        result = await self.process({"requirements": requirements, **kwargs})

        if result["status"] == "success":
            return result["analysis"]["complexity_assessment"]
        else:
            return {"error": result.get("error", "评估失败")}

    async def analyze_risks(
        self, requirements: Dict[str, Any], **kwargs
    ) -> List[Dict[str, Any]]:
        """便捷方法：风险分析"""
        result = await self.process({"requirements": requirements, **kwargs})

        if result["status"] == "success":
            return result["analysis"]["risk_analysis"]
        else:
            return [{"error": result.get("error", "分析失败")}]

    def get_analysis_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取分析摘要"""
        if result.get("status") != "success" or not result.get("analysis"):
            return {"error": "无效的分析结果"}

        analysis = result["analysis"]

        return {
            "feasibility_score": self._calculate_feasibility_score(
                analysis["feasibility_analysis"]
            ),
            "complexity_level": analysis["complexity_assessment"]["overall_complexity"],
            "risk_count": len(analysis["risk_analysis"]),
            "high_risks": [
                risk
                for risk in analysis["risk_analysis"]
                if risk.get("probability") == "high" or risk.get("impact") == "high"
            ],
            "recommendations_count": len(analysis["recommendations"]),
        }

    def _calculate_feasibility_score(self, feasibility: Dict[str, Any]) -> float:
        """计算可行性分数"""
        _scores = {"high": 1.0, "medium": 0.6, "low": 0.3}

        technical_score = scores.get(
            feasibility.get("technical_feasibility", "medium"), 0.6
        )
        resource_score = scores.get(
            feasibility.get("resource_feasibility", "medium"), 0.6
        )
        time_score = scores.get(feasibility.get("time_feasibility", "medium"), 0.6)

        return (technical_score + resource_score + time_score) / 3

    async def analyze(
        self, requirements: Dict[str, Any], context: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析需求的接口方法，供AgentCoordinator调用

        Args:
            requirements: 需求信息
            context: 可选的上下文信息

        Returns:
            分析结果
        """
        input_data = {"requirements": requirements}
        if context:
            input_data["context"] = context

        result = await self.process(input_data)
        return result.get("analysis", {})
