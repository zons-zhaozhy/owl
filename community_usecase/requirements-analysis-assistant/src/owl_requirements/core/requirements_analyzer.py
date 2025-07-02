"""
需求分析器模块

提供需求分析的核心功能，包括需求验证、依赖分析、冲突检测等。
"""

from typing import Dict, Any, List, Optional
from ..utils.exceptions import (
    ValidationError,
    AnalysisError,
)


class RequirementsAnalyzer:
    """需求分析器类"""

    def __init__(self):
        """初始化需求分析器"""
        self._default_rules = {
            "优先级权重": {"高": 3, "中": 2, "低": 1},
            "风险评估阈值": 0.5,
        }

    def analyze(
        self,
        requirements: Dict[str, Any],
        rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分析需求数据。

        Args:
            requirements: 需求数据字典
            rules: 自定义分析规则

        Returns:
            分析结果字典

        Raises:
            ValidationError: 需求数据验证失败时抛出
            AnalysisError: 需求分析过程中出错时抛出
        """
        # 验证输入
        self._validate_requirements(requirements)
        analysis_rules = self._validate_and_merge_rules(rules)

        try:
            # 执行分析
            analysis_result = {
                "项目名称": requirements["项目名称"],
                "版本": requirements.get("版本", "1.0.0"),
                "分析结果": {
                    "功能需求": self._analyze_functional_requirements(
                        requirements["功能需求"]
                    ),
                    "非功能需求": self._analyze_non_functional_requirements(
                        requirements["非功能需求"]
                    ),
                    "使用规则": analysis_rules,
                },
            }

            # 依赖分析
            if any("依赖" in req for req in requirements["功能需求"]):
                analysis_result["分析结果"]["依赖分析"] = self._analyze_dependencies(
                    requirements["功能需求"]
                )
                analysis_result["分析结果"]["依赖图"] = self._generate_dependency_graph(
                    requirements["功能需求"]
                )
                analysis_result["分析结果"]["实现顺序建议"] = (
                    self._suggest_implementation_order(requirements["功能需求"])
                )

            # 冲突检测
            conflicts = self._detect_conflicts(requirements)
            if conflicts:
                analysis_result["分析结果"]["冲突检测"] = conflicts

            # 约束分析
            if "约束条件" in requirements:
                constraints_analysis = self._analyze_constraints(
                    requirements["约束条件"],
                    requirements["功能需求"],
                    requirements["非功能需求"],
                )
                analysis_result["分析结果"]["约束分析"] = constraints_analysis[
                    "约束分析"
                ]
                analysis_result["分析结果"]["约束影响评估"] = constraints_analysis[
                    "影响评估"
                ]

            # 总体评估
            analysis_result["分析结果"]["总体评估"] = self._generate_overall_assessment(
                analysis_result["分析结果"], analysis_rules
            )

            return analysis_result

        except Exception as e:
            raise AnalysisError(f"需求分析失败: {str(e)}")

    def _validate_requirements(self, requirements: Dict[str, Any]) -> None:
        """验证需求数据的有效性"""
        if not requirements:
            raise ValidationError("需求数据为空")

        required_fields = ["项目名称", "功能需求", "非功能需求"]
        missing_fields = [
            field for field in required_fields if field not in requirements
        ]
        if missing_fields:
            raise ValidationError(f"缺少必需字段: {', '.join(missing_fields)}")

        # 验证功能需求
        self._validate_functional_requirements(requirements["功能需求"])

        # 验证非功能需求
        self._validate_non_functional_requirements(requirements["非功能需求"])

        # 验证需求ID唯一性
        self._validate_requirement_ids(requirements)

    def _validate_functional_requirements(
        self, requirements: List[Dict[str, Any]]
    ) -> None:
        """验证功能需求的有效性"""
        required_fields = ["编号", "标题", "描述", "优先级", "状态"]
        valid_priorities = ["高", "中", "低"]
        valid_statuses = ["待实现", "实现中", "已完成", "已取消"]

        for req in requirements:
            missing_fields = [field for field in required_fields if field not in req]
            if missing_fields:
                raise ValidationError(
                    f"功能需求缺少必需字段: {', '.join(missing_fields)}"
                )

            if req["优先级"] not in valid_priorities:
                raise ValidationError(f"无效的优先级值: {req['优先级']}")

            if req["状态"] not in valid_statuses:
                raise ValidationError(f"无效的状态值: {req['状态']}")

    def _validate_non_functional_requirements(
        self, requirements: List[Dict[str, Any]]
    ) -> None:
        """验证非功能需求的有效性"""
        required_fields = ["编号", "类型", "描述", "优先级"]
        valid_priorities = ["高", "中", "低"]

        for req in requirements:
            missing_fields = [field for field in required_fields if field not in req]
            if missing_fields:
                raise ValidationError(
                    f"非功能需求缺少必需字段: {', '.join(missing_fields)}"
                )

            if req["优先级"] not in valid_priorities:
                raise ValidationError(f"无效的优先级值: {req['优先级']}")

    def _validate_requirement_ids(self, requirements: Dict[str, Any]) -> None:
        """验证需求ID的唯一性"""
        all_ids = []

        # 收集所有需求ID
        for req in requirements["功能需求"]:
            all_ids.append(req["编号"])
        for req in requirements["非功能需求"]:
            all_ids.append(req["编号"])

        # 检查重复
        duplicate_ids = set([req_id for req_id in all_ids if all_ids.count(req_id) > 1])
        if duplicate_ids:
            raise ValidationError(f"重复的需求编号: {', '.join(duplicate_ids)}")

    def _validate_and_merge_rules(
        self, rules: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """验证并合并分析规则"""
        if not rules:
            return self._default_rules.copy()

        try:
            merged_rules = self._default_rules.copy()
            merged_rules.update(rules)

            # 验证优先级权重
            weights = merged_rules.get("优先级权重", {})
            if not isinstance(weights, dict) or not all(
                isinstance(v, (int, float)) for v in weights.values()
            ):
                raise ValidationError("无效的优先级权重设置")

            # 验证风险评估阈值
            threshold = merged_rules.get("风险评估阈值")
            if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
                raise ValidationError("无效的风险评估阈值")

            return merged_rules

        except Exception as e:
            raise ValidationError(f"无效的分析规则: {str(e)}")

    def _analyze_functional_requirements(
        self, requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析功能需求"""
        analyzed_requirements = []

        for req in requirements:
            analysis = {
                "需求": req.copy(),
                "复杂度评估": self._assess_complexity(req),
                "风险评估": self._assess_risk(req),
            }
            analyzed_requirements.append(analysis)

        return analyzed_requirements

    def _analyze_non_functional_requirements(
        self, requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析非功能需求"""
        analyzed_requirements = []

        for req in requirements:
            analysis = {
                "需求": req.copy(),
                "影响范围": self._assess_impact(req),
                "实现难度": self._assess_difficulty(req),
            }
            analyzed_requirements.append(analysis)

        return analyzed_requirements

    def _analyze_dependencies(
        self, requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析需求间的依赖关系"""
        dependency_map = {}

        for req in requirements:
            if "依赖" in req:
                dependency_map[req["编号"]] = {
                    "依赖项": req["依赖"],
                    "依赖层级": self._calculate_dependency_level(
                        req["编号"], requirements
                    ),
                }

        return dependency_map

    def _generate_dependency_graph(
        self, requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成需求依赖关系图"""
        graph = {"节点": [], "连接": []}

        for req in requirements:
            graph["节点"].append(
                {
                    "id": req["编号"],
                    "标题": req["标题"],
                    "优先级": req["优先级"],
                }
            )

            if "依赖" in req:
                for dep in req["依赖"]:
                    graph["连接"].append({"从": dep, "到": req["编号"]})

        return graph

    def _suggest_implementation_order(
        self, requirements: List[Dict[str, Any]]
    ) -> List[str]:
        """建议需求实现顺序"""
        # 使用拓扑排序算法
        dependency_map = {req["编号"]: set(req.get("依赖", [])) for req in requirements}
        implementation_order = []
        no_dependencies = set(
            req["编号"] for req in requirements if not req.get("依赖")
        )

        while no_dependencies:
            req_id = no_dependencies.pop()
            implementation_order.append(req_id)

            # 更新依赖关系
            for other_id, deps in dependency_map.items():
                if req_id in deps:
                    deps.remove(req_id)
                    if not deps:
                        no_dependencies.add(other_id)

        return implementation_order

    def _detect_conflicts(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测需求间的冲突"""
        conflicts = []

        # 检查功能需求间的冲突
        for i, req1 in enumerate(requirements["功能需求"]):
            for req2 in requirements["功能需求"][i + 1 :]:
                if self._check_functional_conflict(req1, req2):
                    conflicts.append(
                        {
                            "类型": "功能冲突",
                            "需求1": req1["编号"],
                            "需求2": req2["编号"],
                            "描述": f"功能 '{req1['标题']}' 和 '{req2['标题']}' 存在潜在冲突",
                        }
                    )

        # 检查非功能需求间的冲突
        for i, req1 in enumerate(requirements["非功能需求"]):
            for req2 in requirements["非功能需求"][i + 1 :]:
                if self._check_non_functional_conflict(req1, req2):
                    conflicts.append(
                        {
                            "类型": "非功能冲突",
                            "需求1": req1["编号"],
                            "需求2": req2["编号"],
                            "描述": f"非功能需求 '{req1['描述']}' 和 '{req2['描述']}' 存在冲突",
                        }
                    )

        return conflicts

    def _analyze_constraints(
        self,
        constraints: List[Dict[str, Any]],
        functional_reqs: List[Dict[str, Any]],
        non_functional_reqs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """分析约束条件及其影响"""
        analysis = {"约束分析": [], "影响评估": {}}

        for constraint in constraints:
            constraint_analysis = {
                "约束": constraint.copy(),
                "影响需求": [],
                "影响程度": self._assess_constraint_impact(constraint),
            }

            # 分析影响的需求
            for req_id in constraint["影响范围"]:
                # 查找受影响的需求
                affected_req = None
                for req in functional_reqs:
                    if req["编号"] == req_id:
                        affected_req = req
                        break
                if not affected_req:
                    for req in non_functional_reqs:
                        if req["编号"] == req_id:
                            affected_req = req
                            break

                if affected_req:
                    constraint_analysis["影响需求"].append(
                        {
                            "需求编号": req_id,
                            "需求描述": affected_req["描述"],
                            "影响分析": self._analyze_requirement_constraint_impact(
                                affected_req, constraint
                            ),
                        }
                    )

            analysis["约束分析"].append(constraint_analysis)

            # 更新总体影响评估
            analysis["影响评估"][constraint["类型"]] = (
                self._calculate_constraint_type_impact(constraint_analysis["影响需求"])
            )

        return analysis

    def _generate_overall_assessment(
        self, analysis_results: Dict[str, Any], rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成总体评估结果"""
        # 计算可行性分数
        feasibility = self._calculate_feasibility(analysis_results)

        # 确定风险等级
        risk_level = self._determine_risk_level(analysis_results, rules["风险评估阈值"])

        # 生成建议
        suggestions = self._generate_suggestions(analysis_results)

        return {
            "可行性": feasibility,
            "风险等级": risk_level,
            "建议": suggestions,
        }

    def _assess_complexity(self, requirement: Dict[str, Any]) -> str:
        """评估需求复杂度"""
        # 基于描述长度、依赖数量等因素评估复杂度
        complexity_score = 0

        # 考虑描述长度
        description_length = len(requirement["描述"])
        if description_length > 200:
            complexity_score += 3
        elif description_length > 100:
            complexity_score += 2
        else:
            complexity_score += 1

        # 考虑依赖数量
        if "依赖" in requirement:
            complexity_score += len(requirement["依赖"])

        # 映射分数到复杂度级别
        if complexity_score >= 5:
            return "高"
        elif complexity_score >= 3:
            return "中"
        else:
            return "低"

    def _assess_risk(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """评估需求风险"""
        risks = []
        risk_level = "低"

        # 检查高优先级需求
        if requirement["优先级"] == "高":
            risks.append("高优先级需求可能影响项目进度")
            risk_level = "中"

        # 检查依赖关系
        if "依赖" in requirement and len(requirement["依赖"]) > 2:
            risks.append("复杂的依赖关系可能导致实现困难")
            risk_level = "高"

        # 检查描述完整性
        if len(requirement["描述"]) < 50:
            risks.append("需求描述可能不够详细")
            risk_level = "中"

        return {"风险等级": risk_level, "风险项": risks}

    def _assess_impact(self, requirement: Dict[str, Any]) -> str:
        """评估非功能需求的影响范围"""
        # 基于需求类型和优先级评估影响范围
        if requirement["优先级"] == "高":
            return "全局"
        elif requirement["类型"] in ["性能", "安全性"]:
            return "关键模块"
        else:
            return "局部"

    def _assess_difficulty(self, requirement: Dict[str, Any]) -> str:
        """评估非功能需求的实现难度"""
        # 基于需求类型和描述评估实现难度
        if requirement["类型"] in ["安全性", "性能"] and requirement["优先级"] == "高":
            return "高"
        elif "必须" in requirement["描述"] or "不得" in requirement["描述"]:
            return "中"
        else:
            return "低"

    def _calculate_dependency_level(
        self, req_id: str, requirements: List[Dict[str, Any]]
    ) -> int:
        """计算需求的依赖层级"""
        visited = set()

        def get_level(current_id: str) -> int:
            if current_id in visited:
                return 0
            visited.add(current_id)

            current_req = next(
                (req for req in requirements if req["编号"] == current_id),
                None,
            )
            if not current_req or "依赖" not in current_req:
                return 0

            return 1 + max((get_level(dep) for dep in current_req["依赖"]), default=0)

        return get_level(req_id)

    def _check_functional_conflict(
        self, req1: Dict[str, Any], req2: Dict[str, Any]
    ) -> bool:
        """检查功能需求之间是否存在冲突"""
        # 示例：检查相似功能的不同实现方式
        return req1["标题"] == req2["标题"] or (
            req1.get("依赖")
            and req2["编号"] in req1["依赖"]
            and req2.get("依赖")
            and req1["编号"] in req2["依赖"]
        )

    def _check_non_functional_conflict(
        self, req1: Dict[str, Any], req2: Dict[str, Any]
    ) -> bool:
        """检查非功能需求之间是否存在冲突"""
        # 示例：检查性能和安全性需求的冲突
        return (
            req1["类型"] == req2["类型"]
            and req1["优先级"] == req2["优先级"]
            and req1["描述"] != req2["描述"]
        )

    def _assess_constraint_impact(self, constraint: Dict[str, Any]) -> str:
        """评估约束条件的影响程度"""
        if len(constraint["影响范围"]) > 3:
            return "高"
        elif constraint["类型"] in ["技术约束", "业务约束"]:
            return "中"
        else:
            return "低"

    def _analyze_requirement_constraint_impact(
        self, requirement: Dict[str, Any], constraint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析约束对特定需求的影响"""
        return {
            "影响类型": constraint["类型"],
            "影响程度": "高" if requirement["优先级"] == "高" else "中",
            "需要调整": self._needs_adjustment(requirement, constraint),
        }

    def _calculate_constraint_type_impact(
        self, affected_requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算某类约束的总体影响"""
        high_impact = sum(
            1 for req in affected_requirements if req["影响分析"]["影响程度"] == "高"
        )
        medium_impact = sum(
            1 for req in affected_requirements if req["影响分析"]["影响程度"] == "中"
        )

        return {
            "高影响需求数": high_impact,
            "中影响需求数": medium_impact,
            "总体影响程度": "高" if high_impact > medium_impact else "中",
        }

    def _needs_adjustment(
        self, requirement: Dict[str, Any], constraint: Dict[str, Any]
    ) -> bool:
        """判断需求是否需要根据约束进行调整"""
        return requirement["优先级"] == "高" or constraint["类型"] in [
            "技术约束",
            "业务约束",
        ]

    def _calculate_feasibility(self, analysis_results: Dict[str, Any]) -> float:
        """计算项目可行性分数"""
        total_score = 0
        max_score = 0

        # 考虑功能需求的复杂度和风险
        for req in analysis_results["功能需求"]:
            complexity_score = {"低": 3, "中": 2, "高": 1}[req["复杂度评估"]]
            risk_score = {"低": 3, "中": 2, "高": 1}[req["风险评估"]["风险等级"]]
            total_score += complexity_score + risk_score
            max_score += 6

        # 考虑非功能需求的实现难度
        for req in analysis_results["非功能需求"]:
            difficulty_score = {"低": 3, "中": 2, "高": 1}[req["实现难度"]]
            total_score += difficulty_score
            max_score += 3

        # 计算冲突的影响
        if "冲突检测" in analysis_results:
            conflict_penalty = len(analysis_results["冲突检测"]) * 0.1
            total_score = total_score * (1 - conflict_penalty)

        return round(total_score / max_score, 2) if max_score > 0 else 0

    def _determine_risk_level(
        self, analysis_results: Dict[str, Any], threshold: float
    ) -> str:
        """确定项目整体风险等级"""
        high_risks = 0
        medium_risks = 0

        # 统计功能需求风险
        for req in analysis_results["功能需求"]:
            if req["风险评估"]["风险等级"] == "高":
                high_risks += 1
            elif req["风险评估"]["风险等级"] == "中":
                medium_risks += 1

        # 考虑非功能需求的实现难度
        for req in analysis_results["非功能需求"]:
            if req["实现难度"] == "高":
                high_risks += 1
            elif req["实现难度"] == "中":
                medium_risks += 1

        # 计算风险比例
        total_reqs = len(analysis_results["功能需求"]) + len(
            analysis_results["非功能需求"]
        )
        risk_ratio = (
            (high_risks * 2 + medium_risks) / (total_reqs * 2) if total_reqs > 0 else 0
        )

        if risk_ratio >= threshold:
            return "高"
        elif risk_ratio >= threshold / 2:
            return "中"
        else:
            return "低"

    def _generate_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 检查高风险需求
        high_risk_reqs = [
            req
            for req in analysis_results["功能需求"]
            if req["风险评估"]["风险等级"] == "高"
        ]
        if high_risk_reqs:
            suggestions.append(f"建议优先关注{len(high_risk_reqs)}个高风险需求")

        # 检查复杂依赖
        if "依赖分析" in analysis_results:
            complex_deps = [
                req_id
                for req_id, info in analysis_results["依赖分析"].items()
                if info["依赖层级"] > 2
            ]
            if complex_deps:
                suggestions.append("建议简化复杂的依赖关系")

        # 检查需求冲突
        if "冲突检测" in analysis_results and analysis_results["冲突检测"]:
            suggestions.append("需要解决检测到的需求冲突")

        # 检查非功能需求
        difficult_nfrs = [
            req for req in analysis_results["非功能需求"] if req["实现难度"] == "高"
        ]
        if difficult_nfrs:
            suggestions.append("建议详细评估高难度非功能需求的实现方案")

        return suggestions
