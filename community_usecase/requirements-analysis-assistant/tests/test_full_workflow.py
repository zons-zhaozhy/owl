"""
需求分析助手完整工作流程测试模块
"""
import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from src.owl_requirements.core.config import Config
from src.owl_requirements.services.analyzer import RequirementsAnalyzer
from src.owl_requirements.services.llm import LLMService
from src.main import main

class TestFullWorkflow:
    """完整工作流程测试类"""
    
    @pytest.fixture
    def sample_requirements(self):
        """示例需求文本"""
        return """
        需求分析助手系统规格说明
        
        1. 系统概述
        本系统是一个基于AI的需求分析助手，帮助用户收集、分析和管理软件需求。
        
        2. 功能需求
        F1. 用户管理
        - 用户可以注册和登录系统
        - 支持多种认证方式（邮箱、手机号）
        - 用户可以修改个人信息
        
        F2. 需求录入
        - 支持文本输入需求描述
        - 支持文件上传（Word、PDF、Markdown）
        - 支持语音输入转文字
        
        F3. 需求分析
        - 自动提取需求关键信息
        - 需求分类和优先级排序
        - 识别需求间依赖关系
        - 检测需求冲突和不一致
        
        F4. 文档生成
        - 生成标准化需求文档
        - 支持多种导出格式（PDF、Word、Markdown）
        - 自动生成需求追踪矩阵
        
        3. 非功能需求
        N1. 性能要求
        - 系统响应时间不超过3秒
        - 支持并发用户数不少于100
        - 系统可用性达到99.9%
        
        N2. 安全要求
        - 用户数据必须加密存储
        - 支持HTTPS通信
        - 定期安全审计
        
        N3. 可用性要求
        - 界面简洁直观
        - 支持多语言（中英文）
        - 响应式设计，支持移动端
        
        4. 约束条件
        C1. 技术约束
        - 必须使用Python开发
        - 数据库使用PostgreSQL
        - 部署在云平台
        
        C2. 时间约束
        - 项目周期6个月
        - 分3个阶段交付
        
        C3. 预算约束
        - 开发预算50万元
        - 运维预算每年10万元
        """
    
    def test_complete_analysis_workflow(self, test_config: Dict[str, Any], sample_requirements: str):
        """测试完整的需求分析工作流程"""
        # 初始化分析器
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 第一步：需求提取
        extracted = analyzer.extract_requirements(sample_requirements)
        assert len(extracted) >= 10  # 至少提取10个需求
        
        # 验证提取的需求包含关键信息
        req_texts = [req["description"] for req in extracted]
        assert any("用户注册" in text for text in req_texts)
        assert any("需求分析" in text for text in req_texts)
        assert any("文档生成" in text for text in req_texts)
        
        # 第二步：需求分类
        classified = analyzer.classify_requirements([req["description"] for req in extracted])
        
        # 验证分类结果
        categories = {req["category"] for req in classified}
        expected_categories = {"功能需求", "性能需求", "安全需求", "界面需求", "约束需求"}
        assert categories.intersection(expected_categories)
        
        # 第三步：优先级排序
        prioritized = analyzer.prioritize_requirements(classified)
        
        # 验证优先级分布
        priorities = [req["priority"] for req in prioritized]
        assert "高" in priorities
        assert "中" in priorities
        
        # 第四步：依赖关系分析
        dependencies = analyzer.analyze_dependencies([req["description"] for req in extracted])
        
        # 验证依赖图
        assert "nodes" in dependencies
        assert "edges" in dependencies
        assert len(dependencies["nodes"]) > 0
        
        # 第五步：风险分析
        risks = analyzer.analyze_risks([req["description"] for req in extracted])
        
        # 验证风险识别
        assert "risks" in risks
        assert len(risks["risks"]) > 0
        
        # 第六步：质量检查
        quality_results = []
        for req in extracted[:5]:  # 检查前5个需求
            quality = analyzer.assess_quality(req["description"])
            quality_results.append(quality)
        
        # 验证质量评估
        assert all("quality_score" in q for q in quality_results)
        assert all("issues" in q for q in quality_results)
        
        # 第七步：冲突检测
        conflicts = analyzer.detect_conflicts([req["description"] for req in extracted])
        
        # 验证冲突检测结果
        assert "conflicts" in conflicts
        
        # 第八步：完整性检查
        completeness = analyzer.check_completeness(classified)
        
        # 验证完整性检查
        assert "missing_aspects" in completeness
        assert "suggestions" in completeness
        
        print("✅ 完整工作流程测试通过")
        
    def test_cli_mode_workflow(self, test_config: Dict[str, Any], sample_requirements: str):
        """测试CLI模式工作流程"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_requirements)
            input_file = f.name
        
        try:
            # 模拟CLI命令执行
            with patch('sys.argv', ['main.py', '--mode', 'cli', '--input', input_file]):
                with patch('src.main.main') as mock_main:
                    mock_main.return_value = {
                        "status": "success",
                        "requirements": [],
                        "analysis": {}
                    }
                    
                    # 执行CLI命令
                    result = main()
                    
                    # 验证执行结果
                    assert result is not None
                    mock_main.assert_called_once()
                    
        finally:
            Path(input_file).unlink()
            
    def test_web_mode_workflow(self, test_config: Dict[str, Any], sample_requirements: str):
        """测试Web模式工作流程"""
        import requests
        from threading import Thread
        import time
        
        # 启动Web服务器（模拟）
        with patch('src.main.main') as mock_main:
            mock_main.return_value = None
            
            # 模拟Web服务器启动
            with patch('uvicorn.run') as mock_uvicorn:
                # 启动服务器
                thread = Thread(target=main, args=(['--mode', 'web'],))
                thread.daemon = True
                thread.start()
                
                # 等待服务器启动
                time.sleep(0.1)
                
                # 验证服务器启动
                mock_uvicorn.assert_called_once()
                
    def test_once_mode_workflow(self, test_config: Dict[str, Any]):
        """测试Once模式工作流程"""
        simple_requirement = "创建一个用户登录系统"
        
        # 模拟Once模式执行
        with patch('sys.argv', ['main.py', '--mode', 'once', simple_requirement]):
            with patch('src.main.main') as mock_main:
                mock_main.return_value = {
                    "requirements": [
                        {
                            "description": "用户可以使用用户名和密码登录",
                            "category": "功能需求",
                            "priority": "高"
                        }
                    ],
                    "analysis": {
                        "complexity": "中",
                        "estimated_effort": "2-3天"
                    }
                }
                
                # 执行Once命令
                result = main()
                
                # 验证执行结果
                assert result is not None
                assert "requirements" in result
                assert "analysis" in result
                
    def test_error_handling_workflow(self, test_config: Dict[str, Any]):
        """测试错误处理工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 测试空输入
        with pytest.raises(Exception):
            analyzer.analyze("")
            
        # 测试无效输入
        with pytest.raises(Exception):
            analyzer.extract_requirements(None)
            
        # 测试配置错误
        invalid_config = test_config.copy()
        invalid_config["llm_provider"] = "invalid_provider"
        
        with pytest.raises(Exception):
            RequirementsAnalyzer(Config(**invalid_config))
            
    def test_performance_workflow(self, test_config: Dict[str, Any], sample_requirements: str):
        """测试性能工作流程"""
        import time
        
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 测试大量需求处理性能
        large_requirements = sample_requirements * 10  # 扩大10倍
        
        start_time = time.time()
        result = analyzer.extract_requirements(large_requirements)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证性能要求（应在合理时间内完成）
        assert processing_time < 30  # 30秒内完成
        assert len(result) > 0
        
        print(f"✅ 处理{len(result)}个需求耗时: {processing_time:.2f}秒")
        
    def test_concurrent_workflow(self, test_config: Dict[str, Any]):
        """测试并发处理工作流程"""
        import threading
        import concurrent.futures
        
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        requirements = [
            "用户登录系统",
            "数据管理模块",
            "报表生成功能",
            "系统监控工具",
            "API接口服务"
        ]
        
        # 并发处理多个需求
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(analyzer.analyze, req)
                for req in requirements
            ]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"并发处理失败: {e}")
                    
        # 验证并发处理结果
        assert len(results) == len(requirements)
        assert all("requirements" in r for r in results)
        
        print("✅ 并发处理测试通过")
        
    def test_data_persistence_workflow(self, test_config: Dict[str, Any], tmp_path):
        """测试数据持久化工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 分析需求
        result = analyzer.analyze("创建用户管理系统")
        
        # 保存结果
        output_file = tmp_path / "analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # 验证文件保存
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # 读取验证
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_result = json.load(f)
            
        assert loaded_result == result
        
        print("✅ 数据持久化测试通过")
        
    def test_integration_with_external_services(self, test_config: Dict[str, Any]):
        """测试与外部服务集成工作流程"""
        # 模拟外部服务调用
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "analysis": "需求分析完成",
                "confidence": 0.95
            }
            mock_post.return_value = mock_response
            
            analyzer = RequirementsAnalyzer(Config(**test_config))
            
            # 执行分析（会调用外部服务）
            result = analyzer.analyze("用户认证系统")
            
            # 验证外部服务调用
            assert result is not None
            
    def test_multi_format_input_workflow(self, test_config: Dict[str, Any], tmp_path):
        """测试多格式输入工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 测试不同格式的输入
        formats = {
            "text": "用户可以登录系统",
            "json": '{"requirement": "用户管理功能", "priority": "高"}',
            "markdown": "# 需求\n- 用户登录\n- 密码重置"
        }
        
        results = {}
        for format_name, content in formats.items():
            try:
                if format_name == "json":
                    # 处理JSON格式
                    data = json.loads(content)
                    result = analyzer.analyze(data["requirement"])
                else:
                    # 处理文本和Markdown格式
                    result = analyzer.analyze(content)
                    
                results[format_name] = result
                
            except Exception as e:
                pytest.fail(f"处理{format_name}格式失败: {e}")
                
        # 验证所有格式都能正确处理
        assert len(results) == len(formats)
        assert all("requirements" in r for r in results.values())
        
        print("✅ 多格式输入测试通过")
        
    def test_quality_assurance_workflow(self, test_config: Dict[str, Any]):
        """测试质量保证工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 测试需求质量检查流程
        test_requirements = [
            "系统应该快速响应",  # 模糊需求
            "用户可以在3秒内完成登录",  # 明确需求
            "系统必须安全",  # 模糊需求
            "密码必须包含至少8个字符，包括数字和字母"  # 明确需求
        ]
        
        quality_results = []
        for req in test_requirements:
            quality = analyzer.assess_quality(req)
            quality_results.append(quality)
            
        # 验证质量评估
        assert len(quality_results) == len(test_requirements)
        
        # 验证模糊需求被识别
        low_quality_count = sum(1 for q in quality_results if q["quality_score"] < 7)
        assert low_quality_count >= 2  # 至少识别出2个低质量需求
        
        print("✅ 质量保证工作流程测试通过")
        
    def test_reporting_workflow(self, test_config: Dict[str, Any], tmp_path):
        """测试报告生成工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 分析需求
        requirements = [
            "用户登录功能",
            "数据备份机制",
            "系统监控工具"
        ]
        
        analysis_results = []
        for req in requirements:
            result = analyzer.analyze(req)
            analysis_results.append(result)
            
        # 生成综合报告
        report_data = {
            "project": "需求分析助手测试",
            "timestamp": "2025-01-XX",
            "requirements_count": len(requirements),
            "analysis_results": analysis_results,
            "summary": {
                "total_requirements": len(requirements),
                "high_priority": sum(1 for r in analysis_results if "高" in str(r)),
                "risks_identified": sum(len(r.get("risks", [])) for r in analysis_results)
            }
        }
        
        # 保存报告
        report_file = tmp_path / "analysis_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        # 验证报告生成
        assert report_file.exists()
        assert report_file.stat().st_size > 0
        
        # 验证报告内容
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        assert report["requirements_count"] == len(requirements)
        assert "summary" in report
        assert "analysis_results" in report
        
        print("✅ 报告生成工作流程测试通过")
        
    def test_continuous_improvement_workflow(self, test_config: Dict[str, Any]):
        """测试持续改进工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 模拟用户反馈和系统学习
        initial_analysis = analyzer.analyze("用户管理系统")
        
        # 模拟用户反馈
        feedback = {
            "accuracy": 8,
            "completeness": 7,
            "usefulness": 9,
            "suggestions": ["需要更详细的安全需求分析"]
        }
        
        # 应用反馈改进分析
        improved_analysis = analyzer.analyze(
            "用户管理系统",
            feedback=feedback
        )
        
        # 验证改进效果
        assert improved_analysis is not None
        assert len(improved_analysis.get("requirements", [])) >= len(initial_analysis.get("requirements", []))
        
        print("✅ 持续改进工作流程测试通过")
        
    @pytest.mark.asyncio
    async def test_async_workflow(self, test_config: Dict[str, Any]):
        """测试异步处理工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 模拟异步需求处理
        requirements = [
            "用户认证模块",
            "数据分析引擎",
            "报告生成服务",
            "API网关",
            "监控系统"
        ]
        
        # 异步处理所有需求
        tasks = [
            asyncio.create_task(
                asyncio.to_thread(analyzer.analyze, req)
            )
            for req in requirements
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证异步处理结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(requirements)
        
        print("✅ 异步处理工作流程测试通过")
        
    def test_rollback_workflow(self, test_config: Dict[str, Any]):
        """测试回滚工作流程"""
        analyzer = RequirementsAnalyzer(Config(**test_config))
        
        # 创建初始需求
        requirement = {
            "id": "REQ-001",
            "description": "用户登录功能",
            "version": "1.0"
        }
        
        # 创建版本2
        v2 = analyzer.create_version(
            requirement,
            changes=["添加双因素认证"]
        )
        
        # 创建版本3
        v3 = analyzer.create_version(
            v2,
            changes=["添加生物识别"]
        )
        
        # 回滚到版本2
        rolled_back = analyzer.rollback_version("REQ-001", "2.0")
        
        # 验证回滚结果
        assert rolled_back["version"] == "2.0"
        assert "双因素认证" in str(rolled_back["changes"])
        assert "生物识别" not in str(rolled_back.get("changes", ""))
        
        print("✅ 回滚工作流程测试通过") 