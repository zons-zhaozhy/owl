"""
质量检查智能体测试模块
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.utils.exceptions import QualityCheckError

@pytest.fixture
def mock_llm_service():
    """创建模拟的 LLM 服务"""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "quality_check": {
            "overall_score": 85,
            "issues": [
                {
                    "id": "QC-001",
                    "requirement_id": "FR-001",
                    "type": "清晰度",
                    "severity": "中",
                    "description": "需求描述不够具体",
                    "suggestion": "添加更具体的功能描述"
                }
            ],
            "metrics": {
                "clarity": 0.85,
                "completeness": 0.90,
                "consistency": 0.88,
                "testability": 0.82
            }
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """创建模拟的配置"""
    return {
        "name": "quality_checker",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }

@pytest.fixture
def quality_check_agent(mock_llm_service):
    """创建质量检查智能体实例"""
    return QualityChecker(llm_service=mock_llm_service, config={"max_retries": 3})

@pytest.fixture
def quality_check_agent_no_llm():
    """创建不带 LLM 检查器的质量检查智能体实例"""
    return QualityChecker()

@pytest.fixture
def sample_analysis_result():
    """创建示例分析结果数据"""
    return {
        "项目名称": "在线教育平台",
        "版本": "1.0.0",
        "分析结果": {
            "功能需求": [
                {
                    "需求": {
                        "编号": "FR-001",
                        "标题": "用户注册",
                        "描述": "新用户可以通过邮箱注册账号",
                        "优先级": "高",
                        "状态": "待实现"
                    },
                    "复杂度评估": "中",
                    "风险评估": {
                        "风险等级": "低",
                        "风险项": []
                    }
                }
            ],
            "非功能需求": [
                {
                    "需求": {
                        "编号": "NFR-001",
                        "类型": "性能",
                        "描述": "页面加载时间不超过2秒",
                        "优先级": "高"
                    },
                    "影响范围": "全局",
                    "实现难度": "中"
                }
            ],
            "总体评估": {
                "可行性": 0.75,
                "风险等级": "低",
                "建议": ["建议详细评估高难度非功能需求的实现方案"]
            }
        }
    }

@pytest.mark.asyncio
async def test_quality_check_success(mock_llm_service, mock_config):
    """测试质量检查成功场景"""
    # 创建质量检查器实例
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    # 准备测试数据
    requirements = {
        "functional_requirements": [
            {
                "id": "FR-001",
                "description": "系统应支持用户登录功能",
                "priority": "high"
            }
        ],
        "non_functional_requirements": []
    }
    
    # 执行质量检查
    result = await checker.process(requirements)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "quality_check" in result
    assert result["quality_check"]["overall_score"] == 85
    assert len(result["quality_check"]["issues"]) > 0
    assert "metrics" in result["quality_check"]

@pytest.mark.asyncio
async def test_quality_check_empty_requirements(mock_llm_service, mock_config):
    """测试空需求场景"""
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(QualityCheckError):
        await checker.process({})

@pytest.mark.asyncio
async def test_quality_check_invalid_requirements(mock_llm_service, mock_config):
    """测试无效需求场景"""
    checker = QualityChecker(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(QualityCheckError):
        await checker.process({"invalid": "data"})

@pytest.mark.asyncio
async def test_check_quality(quality_check_agent, sample_analysis_result):
    """测试质量检查功能"""
    result = await quality_check_agent.process(sample_analysis_result)
    
    assert isinstance(result, dict)
    assert "quality_check" in result
    assert "overall_score" in result["quality_check"]
    assert "issues" in result["quality_check"]
    assert "metrics" in result["quality_check"]
    assert "recommendations" in result["quality_check"]
    assert 0 <= result["quality_check"]["overall_score"] <= 100

@pytest.mark.asyncio
async def test_check_quality_failure(quality_check_agent, sample_analysis_result, mock_llm_service):
    """测试质量检查失败的情况"""
    mock_llm_service.generate.side_effect = Exception("LLM服务暂时不可用")
    
    with pytest.raises(ValueError):
        await quality_check_agent.process(sample_analysis_result)

@pytest.mark.asyncio
async def test_check_quality_without_llm(quality_check_agent_no_llm, sample_analysis_result):
    """测试不带 LLM 的质量检查"""
    result = await quality_check_agent_no_llm.process(sample_analysis_result)
    
    assert isinstance(result, dict)
    assert "quality_check" in result
    assert "overall_score" in result["quality_check"]
    assert "issues" in result["quality_check"]
    assert "metrics" in result["quality_check"]
    assert "recommendations" in result["quality_check"]
    assert 0 <= result["quality_check"]["overall_score"] <= 100

@pytest.mark.asyncio
async def test_check_quality_empty_input(quality_check_agent):
    """测试空输入"""
    with pytest.raises(QualityCheckError) as exc_info:
        await quality_check_agent.process({})
    assert "分析结果为空" in str(exc_info.value)

@pytest.mark.asyncio
async def test_check_quality_missing_fields(quality_check_agent):
    """测试缺少必需字段"""
    invalid_result = {
        "分析结果": {
            "功能需求": []
        }
    }
    with pytest.raises(QualityCheckError) as exc_info:
        await quality_check_agent.process(invalid_result)
    assert "缺少必需字段" in str(exc_info.value)

@pytest.mark.asyncio
async def test_check_quality_invalid_rules(quality_check_agent, sample_analysis_result):
    """测试无效的规则"""
    invalid_rules = {
        "最低描述长度": -1,
        "最大依赖层级": 0,
        "高优先级需求比例": 1.5,
        "最低可行性分数": 2.0,
        "最大冲突数": -1
    }
    with pytest.raises(QualityCheckError):
        await quality_check_agent.process(sample_analysis_result, invalid_rules)

@pytest.mark.asyncio
async def test_check_clarity(quality_check_agent, sample_analysis_result):
    """测试清晰度检查"""
    # 添加一个包含模糊词汇的需求
    sample_analysis_result["分析结果"]["功能需求"].append({
        "需求": {
            "编号": "FR005",
            "标题": "数据备份",
            "描述": "系统可能需要定期备份数据",
            "优先级": "中",
            "状态": "待实现"
        }
    })
    
    result = await quality_check_agent.process(sample_analysis_result)
    
    # 验证是否检测到清晰度问题
    clarity_issues = [
        issue for issue in result["quality_check"]["issues"]
        if issue["type"] == "清晰度"
    ]
    assert len(clarity_issues) > 0
    assert any("FR005" in str(issue) for issue in clarity_issues)

@pytest.mark.asyncio
async def test_check_testability(quality_check_agent, sample_analysis_result):
    """测试可测试性检查"""
    # 添加一个难以测试的需求
    sample_analysis_result["分析结果"]["非功能需求"].append({
        "需求": {
            "编号": "NFR002",
            "类型": "性能",
            "描述": "系统应该运行得比较快",
            "优先级": "中"
        },
        "实现难度": "高"
    })
    
    result = await quality_check_agent.process(sample_analysis_result)
    
    # 验证是否检测到可测试性问题
    testability_issues = [
        issue for issue in result["quality_check"]["issues"]
        if issue["type"] == "可测试性"
    ]
    assert len(testability_issues) > 0
    assert any("NFR002" in str(issue) for issue in testability_issues)

@pytest.mark.asyncio
async def test_check_feasibility(quality_check_agent, sample_analysis_result):
    """测试可行性检查"""
    # 修改总体可行性分数
    sample_analysis_result["分析结果"]["总体评估"]["可行性"] = 0.5
    
    # 添加一个高风险需求
    sample_analysis_result["分析结果"]["功能需求"].append({
        "需求": {
            "编号": "FR006",
            "标题": "人工智能分析",
            "描述": "使用AI进行数据分析",
            "优先级": "高",
            "状态": "待实现"
        },
        "风险评估": {
            "风险等级": "高"
        }
    })
    
    result = await quality_check_agent.process(sample_analysis_result)
    
    # 验证是否检测到可行性问题
    feasibility_issues = [
        issue for issue in result["quality_check"]["issues"]
        if issue["type"] == "可行性"
    ]
    assert len(feasibility_issues) > 0
    assert any("可行性较低" in issue["description"] for issue in feasibility_issues)
    assert any("高风险需求" in issue["description"] for issue in feasibility_issues)

@pytest.mark.asyncio
async def test_generate_report(quality_check_agent, sample_analysis_result):
    """测试报告生成"""
    quality_result = await quality_check_agent.process(sample_analysis_result)
    report = quality_check_agent.generate_report(quality_result)
    
    assert isinstance(report, dict)
    assert "overall_score" in report
    assert "issues" in report
    assert "metrics" in report
    assert "recommendations" in report
    assert "quality_trend" in report
    
    # 验证质量趋势分析
    trend = report["quality_trend"]
    trend = report["质量趋势"]
    assert "强项" in trend
    assert "弱项" in trend
    assert "改进空间" in trend
    assert "建议关注点" in trend

@pytest.mark.asyncio
async def test_custom_rules(quality_check_agent, sample_analysis_result):
    """测试自定义规则"""
    custom_rules = {
        "最低描述长度": 50,  # 增加描述长度要求
        "最大依赖层级": 2,   # 降低最大依赖层级
        "高优先级需求比例": 0.3,  # 降低高优先级需求比例
        "最低可行性分数": 0.7,    # 提高可行性要求
        "最大冲突数": 1           # 降低允许的冲突数
    }
    
    result = await quality_check_agent.check_quality(sample_analysis_result, custom_rules)
    
    # 验证是否使用了自定义规则
    assert result["使用规则"] == custom_rules
    
    # 验证是否基于新规则生成了问题
    assert len(result["问题列表"]) > 0

@pytest.mark.asyncio
async def test_quality_score_calculation(quality_check_agent, sample_analysis_result):
    """测试质量评分计算"""
    result = await quality_check_agent.check_quality(sample_analysis_result)
    
    # 验证质量评分计算
    assert isinstance(result["质量评分"], float)
    assert 0 <= result["质量评分"] <= 100
    
    # 验证维度得分计算
    dimension_scores = result["维度得分"]
    for dimension in quality_check_agent._quality_dimensions:
        if dimension in dimension_scores:
            assert 0 <= dimension_scores[dimension] <= 1

@pytest.mark.asyncio
async def test_suggestion_generation(quality_check_agent, sample_analysis_result):
    """测试建议生成"""
    result = await quality_check_agent.check_quality(sample_analysis_result)
    
    # 验证建议生成
    assert isinstance(result["改进建议"], list)
    assert len(result["改进建议"]) > 0
    
    # 验证建议的相关性
    for suggestion in result["改进建议"]:
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0 