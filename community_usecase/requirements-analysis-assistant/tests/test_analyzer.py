"""
需求分析器测试模块
"""
import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from src.owl_requirements.services.analyzer import RequirementsAnalyzer
from src.owl_requirements.core.config import Config
from src.owl_requirements.core.exceptions import AnalyzerError

class TestRequirementsAnalyzer:
    """需求分析器测试类"""
    
    def test_initialization(self, test_config: Dict[str, Any]):
        """测试分析器初始化"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        assert analyzer.llm_service is not None
        assert analyzer.config is not None
        
    def test_basic_analysis(self, test_config: Dict[str, Any]):
        """测试基本需求分析"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        result = analyzer.analyze("创建一个用户登录系统")
        
        assert "requirements" in result
        assert "analysis" in result
        assert isinstance(result["requirements"], list)
        assert isinstance(result["analysis"], dict)
        
    def test_requirement_extraction(self, test_config: Dict[str, Any]):
        """测试需求提取"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 简单需求
        result = analyzer.extract_requirements("用户可以登录和注册")
        assert len(result) >= 2  # 至少包含登录和注册两个需求
        
        # 复杂需求
        complex_req = """
        系统功能要求：
        1. 用户注册和登录
        2. 个人信息管理
        3. 密码重置
        4. 多因素认证
        """
        result = analyzer.extract_requirements(complex_req)
        assert len(result) >= 4
        
    def test_requirement_classification(self, test_config: Dict[str, Any]):
        """测试需求分类"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "系统必须支持用户登录",
            "页面加载时间不超过2秒",
            "系统需要每日备份数据",
            "界面必须支持深色模式"
        ]
        
        result = analyzer.classify_requirements(requirements)
        
        # 验证分类
        categories = {r["category"] for r in result}
        assert "功能需求" in categories
        assert "性能需求" in categories
        assert "安全需求" in categories
        assert "界面需求" in categories
        
    def test_requirement_prioritization(self, test_config: Dict[str, Any]):
        """测试需求优先级排序"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            {
                "description": "用户登录",
                "complexity": "中",
                "impact": "高"
            },
            {
                "description": "深色模式",
                "complexity": "低",
                "impact": "低"
            },
            {
                "description": "数据备份",
                "complexity": "高",
                "impact": "高"
            }
        ]
        
        result = analyzer.prioritize_requirements(requirements)
        
        # 验证优先级
        priorities = [r["priority"] for r in result]
        assert "高" in priorities
        assert "中" in priorities
        assert "低" in priorities
        
        # 验证排序
        assert result[0]["priority"] >= result[-1]["priority"]
        
    def test_dependency_analysis(self, test_config: Dict[str, Any]):
        """测试依赖关系分析"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "用户必须先注册才能登录",
            "用户必须登录才能修改个人信息",
            "修改密码需要验证邮箱"
        ]
        
        result = analyzer.analyze_dependencies(requirements)
        
        # 验证依赖图
        assert "nodes" in result
        assert "edges" in result
        assert len(result["edges"]) > 0
        
        # 验证依赖关系
        deps = [(e["from"], e["to"]) for e in result["edges"]]
        assert any("注册" in d[0] and "登录" in d[1] for d in deps)
        
    def test_complexity_analysis(self, test_config: Dict[str, Any]):
        """测试复杂度分析"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirement = {
            "description": "实现实时协作编辑功能",
            "features": [
                "并发控制",
                "冲突解决",
                "实时同步",
                "历史记录"
            ]
        }
        
        result = analyzer.analyze_complexity(requirement)
        
        assert "complexity_score" in result
        assert "factors" in result
        assert result["complexity_score"] >= 7  # 高复杂度
        
    def test_risk_analysis(self, test_config: Dict[str, Any]):
        """测试风险分析"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "系统需要处理敏感用户数据",
            "系统需要集成第三方支付",
            "系统需要支持高并发访问"
        ]
        
        result = analyzer.analyze_risks(requirements)
        
        # 验证风险识别
        assert "risks" in result
        risks = result["risks"]
        assert len(risks) > 0
        
        # 验证风险评估
        for risk in risks:
            assert "description" in risk
            assert "probability" in risk
            assert "impact" in risk
            assert "mitigation" in risk
            
    def test_requirement_validation(self, test_config: Dict[str, Any]):
        """测试需求验证"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 有效需求
        valid_req = {
            "description": "用户可以通过邮箱重置密码",
            "type": "功能需求",
            "priority": "高"
        }
        assert analyzer.validate_requirement(valid_req)
        
        # 无效需求
        invalid_reqs = [
            {"description": ""},  # 空描述
            {"description": "用户可以登录", "type": "无效类型"},  # 无效类型
            {"priority": "高"}  # 缺少描述
        ]
        
        for req in invalid_reqs:
            with pytest.raises(AnalyzerError):
                analyzer.validate_requirement(req)
                
    def test_requirement_refinement(self, test_config: Dict[str, Any]):
        """测试需求细化"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirement = "系统需要支持用户管理"
        
        result = analyzer.refine_requirement(requirement)
        
        # 验证细化结果
        assert "sub_requirements" in result
        assert "acceptance_criteria" in result
        assert "constraints" in result
        
        # 验证子需求
        sub_reqs = result["sub_requirements"]
        assert len(sub_reqs) > 0
        assert all(isinstance(r, dict) for r in sub_reqs)
        
    def test_requirement_conflict_detection(self, test_config: Dict[str, Any]):
        """测试需求冲突检测"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "系统响应时间必须小于1秒",
            "系统必须进行全面的安全检查",
            "系统必须支持离线操作",
            "系统必须实时同步数据"
        ]
        
        result = analyzer.detect_conflicts(requirements)
        
        # 验证冲突检测
        assert "conflicts" in result
        conflicts = result["conflicts"]
        assert len(conflicts) > 0
        
        # 验证冲突详情
        for conflict in conflicts:
            assert "requirements" in conflict
            assert "reason" in conflict
            assert "suggestion" in conflict
            
    def test_requirement_completeness(self, test_config: Dict[str, Any]):
        """测试需求完整性检查"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            {
                "description": "用户可以登录",
                "type": "功能需求",
                "priority": "高"
            }
        ]
        
        result = analyzer.check_completeness(requirements)
        
        # 验证完整性检查
        assert "missing_aspects" in result
        assert "suggestions" in result
        
        # 验证建议
        assert len(result["suggestions"]) > 0
        assert all(isinstance(s, str) for s in result["suggestions"])
        
    def test_requirement_consistency(self, test_config: Dict[str, Any]):
        """测试需求一致性检查"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "系统必须使用 SQL 数据库",
            "系统必须使用 NoSQL 数据库",
            "数据必须实时同步",
            "系统必须支持离线操作"
        ]
        
        result = analyzer.check_consistency(requirements)
        
        # 验证一致性问题
        assert "inconsistencies" in result
        assert len(result["inconsistencies"]) > 0
        
        # 验证问题描述
        for issue in result["inconsistencies"]:
            assert "requirements" in issue
            assert "description" in issue
            assert "resolution" in issue
            
    def test_requirement_feasibility(self, test_config: Dict[str, Any]):
        """测试需求可行性分析"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirement = {
            "description": "系统必须支持100万用户同时在线",
            "constraints": {
                "budget": "有限",
                "timeline": "3个月",
                "resources": "小型团队"
            }
        }
        
        result = analyzer.analyze_feasibility(requirement)
        
        # 验证可行性分析
        assert "feasibility_score" in result
        assert "challenges" in result
        assert "recommendations" in result
        
        # 验证建议
        assert len(result["recommendations"]) > 0
        assert all(isinstance(r, str) for r in result["recommendations"])
        
    def test_requirement_quality(self, test_config: Dict[str, Any]):
        """测试需求质量评估"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirement = "系统应该表现良好"  # 模糊的需求
        
        result = analyzer.assess_quality(requirement)
        
        # 验证质量评估
        assert "quality_score" in result
        assert "issues" in result
        assert "improvements" in result
        
        # 验证问题
        assert len(result["issues"]) > 0
        assert "模糊" in str(result["issues"])
        
        # 验证改进建议
        assert len(result["improvements"]) > 0
        assert all(isinstance(i, str) for i in result["improvements"])
        
    def test_requirement_traceability(self, test_config: Dict[str, Any]):
        """测试需求追踪性"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            {
                "id": "REQ-001",
                "description": "用户登录",
                "source": "客户访谈",
                "version": "1.0"
            },
            {
                "id": "REQ-002",
                "description": "密码重置",
                "source": "安全规范",
                "version": "1.1"
            }
        ]
        
        result = analyzer.track_requirements(requirements)
        
        # 验证追踪信息
        assert "trace_matrix" in result
        assert "change_history" in result
        assert "dependencies" in result
        
        # 验证矩阵
        matrix = result["trace_matrix"]
        assert len(matrix) == len(requirements)
        assert all("source" in m for m in matrix)
        
    def test_requirement_versioning(self, test_config: Dict[str, Any]):
        """测试需求版本控制"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirement = {
            "id": "REQ-001",
            "description": "用户登录功能",
            "version": "1.0"
        }
        
        # 创建新版本
        new_version = analyzer.create_version(
            requirement,
            changes=["添加双因素认证"]
        )
        
        # 验证版本信息
        assert new_version["version"] == "1.1"
        assert "change_log" in new_version
        assert "timestamp" in new_version
        
        # 获取版本历史
        history = analyzer.get_version_history(requirement["id"])
        assert len(history) >= 2
        assert all("version" in v for v in history)
        
    def test_requirement_export(self, test_config: Dict[str, Any], tmp_path):
        """测试需求导出"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            {
                "id": "REQ-001",
                "description": "用户登录",
                "priority": "高"
            },
            {
                "id": "REQ-002",
                "description": "密码重置",
                "priority": "中"
            }
        ]
        
        # 导出为不同格式
        formats = ["json", "markdown", "pdf", "docx"]
        for fmt in formats:
            output_file = tmp_path / f"requirements.{fmt}"
            analyzer.export_requirements(
                requirements,
                output_file=output_file,
                format=fmt
            )
            assert output_file.exists()
            
    def test_requirement_import(self, test_config: Dict[str, Any], tmp_path):
        """测试需求导入"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 准备测试文件
        test_file = tmp_path / "requirements.json"
        test_data = [
            {
                "id": "REQ-001",
                "description": "用户登录"
            }
        ]
        
        with open(test_file, "w") as f:
            import json
            json.dump(test_data, f)
            
        # 测试导入
        result = analyzer.import_requirements(test_file)
        
        assert len(result) == len(test_data)
        assert result[0]["id"] == test_data[0]["id"] 