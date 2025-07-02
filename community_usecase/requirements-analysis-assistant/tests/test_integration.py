"""
系统集成测试模块
"""
import os
import json
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from src.owl_requirements.core.config import Config
from src.owl_requirements.services.analyzer import RequirementsAnalyzer
from src.owl_requirements.services.llm import LLMService
from src.owl_requirements.web.app import app
from src.owl_requirements.cli.app import cli_app

class TestSystemIntegration:
    """系统集成测试类"""
    
    def test_end_to_end_analysis(self, test_config: Dict[str, Any]):
        """测试端到端需求分析"""
        # 初始化配置
        config = Config(**test_config)
        
        # 初始化分析器
        analyzer = RequirementsAnalyzer(config)
        
        # 执行分析
        result = analyzer.analyze("创建一个用户认证系统")
        
        # 验证结果
        assert "requirements" in result
        assert "analysis" in result
        assert isinstance(result["requirements"], list)
        assert isinstance(result["analysis"], dict)
        
        # 验证需求质量
        requirements = result["requirements"]
        assert len(requirements) > 0
        for req in requirements:
            assert "id" in req
            assert "description" in req
            assert "priority" in req
            
        # 验证分析质量
        analysis = result["analysis"]
        assert "complexity" in analysis
        assert "dependencies" in analysis
        assert "risks" in analysis
        
    def test_web_mode_integration(self, test_config: Dict[str, Any]):
        """测试 Web 模式集成"""
        from fastapi.testclient import TestClient
        
        # 配置 Web 模式
        config = Config(**test_config)
        config.system_mode = "web"
        
        # 创建测试客户端
        client = TestClient(app)
        
        # 测试分析端点
        response = client.post(
            "/api/v1/analyze",
            json={"text": "创建一个用户认证系统"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "requirements" in result
        assert "analysis" in result
        
        # 测试批量分析
        response = client.post(
            "/api/v1/analyze/batch",
            json={
                "requests": [
                    {"text": "需求1"},
                    {"text": "需求2"}
                ]
            }
        )
        
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        
        # 测试异步分析
        response = client.post(
            "/api/v1/analyze/async",
            json={"text": "创建一个用户认证系统"}
        )
        
        assert response.status_code == 202
        task_id = response.json()["task_id"]
        
        # 检查任务状态
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        
    def test_cli_mode_integration(self, test_config: Dict[str, Any], tmp_path: Path):
        """测试 CLI 模式集成"""
        from typer.testing import CliRunner
        
        # 配置 CLI 模式
        config = Config(**test_config)
        config.system_mode = "cli"
        
        # 创建测试运行器
        runner = CliRunner()
        
        # 创建输入文件
        input_file = tmp_path / "input.txt"
        input_file.write_text("创建一个用户认证系统")
        
        # 创建输出文件
        output_file = tmp_path / "output.json"
        
        # 测试分析命令
        result = runner.invoke(cli_app, [
            "analyze",
            str(input_file),
            "--output",
            str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # 验证输出
        with open(output_file) as f:
            data = json.load(f)
            assert "requirements" in data
            assert "analysis" in data
            
    def test_once_mode_integration(self, test_config: Dict[str, Any]):
        """测试单次模式集成"""
        # 配置单次模式
        config = Config(**test_config)
        config.system_mode = "once"
        
        # 初始化分析器
        analyzer = RequirementsAnalyzer(config)
        
        # 执行分析
        result = analyzer.analyze_once("创建一个用户认证系统")
        
        # 验证结果
        assert isinstance(result, dict)
        assert "requirements" in result
        assert "analysis" in result
        
    def test_error_handling_integration(self, test_config: Dict[str, Any]):
        """测试错误处理集成"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 测试空输入
        with pytest.raises(ValueError):
            analyzer.analyze("")
            
        # 测试超长输入
        with pytest.raises(ValueError):
            analyzer.analyze("需求" * 10000)
            
        # 测试 LLM 错误
        with patch.object(
            LLMService,
            "analyze_requirements",
            side_effect=Exception("LLM 错误")
        ):
            with pytest.raises(Exception):
                analyzer.analyze("测试需求")
                
    def test_configuration_integration(self, test_config: Dict[str, Any], tmp_path: Path):
        """测试配置集成"""
        # 创建配置文件
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(test_config, f)
            
        # 从文件加载配置
        config = Config.from_file(config_file)
        
        # 初始化分析器
        analyzer = RequirementsAnalyzer(config)
        
        # 验证配置生效
        result = analyzer.analyze("测试需求")
        assert "requirements" in result
        
        # 更新配置
        config.llm_temperature = 0.8
        analyzer.update_config(config)
        
        # 验证更新后的配置
        result = analyzer.analyze("测试需求")
        assert "requirements" in result
        
    def test_llm_integration(self, test_config: Dict[str, Any]):
        """测试 LLM 集成"""
        config = Config(**test_config)
        service = LLMService(config)
        
        # 测试不同提供商
        providers = ["openai", "anthropic", "azure"]
        for provider in providers:
            config.llm_provider = provider
            service.update_config(config)
            
            result = service.analyze_requirements("测试需求")
            assert "requirements" in result
            
        # 测试不同模型
        models = ["gpt-4", "gpt-3.5-turbo", "claude-2"]
        for model in models:
            config.llm_model = model
            service.update_config(config)
            
            result = service.analyze_requirements("测试需求")
            assert "requirements" in result
            
    def test_concurrent_analysis(self, test_config: Dict[str, Any]):
        """测试并发分析"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        async def analyze():
            return await analyzer.analyze_async("测试需求")
            
        async def test_concurrent():
            tasks = [analyze() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            return results
            
        results = asyncio.run(test_concurrent())
        assert len(results) == 5
        assert all("requirements" in r for r in results)
        
    def test_output_formats(self, test_config: Dict[str, Any], tmp_path: Path):
        """测试输出格式"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # JSON 格式
        result = analyzer.analyze(
            "测试需求",
            output_format="json"
        )
        assert isinstance(result, dict)
        
        # Markdown 格式
        result = analyzer.analyze(
            "测试需求",
            output_format="markdown"
        )
        assert isinstance(result, str)
        assert "# " in result
        
        # PDF 格式
        pdf_file = tmp_path / "output.pdf"
        analyzer.analyze(
            "测试需求",
            output_format="pdf",
            output_file=pdf_file
        )
        assert pdf_file.exists()
        
        # Word 格式
        docx_file = tmp_path / "output.docx"
        analyzer.analyze(
            "测试需求",
            output_format="docx",
            output_file=docx_file
        )
        assert docx_file.exists()
        
    def test_performance_integration(self, test_config: Dict[str, Any]):
        """测试性能集成"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 记录性能指标
        with analyzer.monitor_performance() as stats:
            analyzer.analyze("测试需求")
            
        # 验证性能指标
        assert "total_time" in stats
        assert "llm_time" in stats
        assert "processing_time" in stats
        assert "memory_usage" in stats
        
        # 验证性能阈值
        assert stats["total_time"] < 10.0  # 10 秒内完成
        assert stats["memory_usage"] < 512  # 512MB 内存限制
        
    def test_system_state(self, test_config: Dict[str, Any]):
        """测试系统状态"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 检查初始状态
        assert analyzer.is_ready()
        assert not analyzer.is_busy()
        
        # 模拟繁忙状态
        analyzer.set_busy(True)
        assert analyzer.is_busy()
        
        # 检查健康状态
        status = analyzer.get_health_status()
        assert status["status"] == "healthy"
        assert "uptime" in status
        assert "memory_usage" in status
        assert "active_tasks" in status
        
    def test_cleanup_integration(self, test_config: Dict[str, Any], tmp_path: Path):
        """测试清理集成"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 创建临时文件
        temp_file = tmp_path / "temp.txt"
        temp_file.write_text("临时数据")
        
        # 执行分析
        analyzer.analyze("测试需求")
        
        # 执行清理
        analyzer.cleanup()
        
        # 验证清理结果
        assert not temp_file.exists()
        assert analyzer.get_memory_usage() < 100  # MB
        
    def test_logging_integration(self, test_config: Dict[str, Any], tmp_path: Path):
        """测试日志集成"""
        # 配置日志
        log_file = tmp_path / "test.log"
        config = Config(**test_config)
        config.system_log_file = str(log_file)
        
        # 初始化分析器
        analyzer = RequirementsAnalyzer(config)
        
        # 执行操作
        analyzer.analyze("测试需求")
        
        # 验证日志
        assert log_file.exists()
        log_content = log_file.read_text()
        
        assert "INFO" in log_content
        assert "分析开始" in log_content
        assert "分析完成" in log_content
        
        # 验证错误日志
        with pytest.raises(Exception):
            analyzer.analyze("")
            
        log_content = log_file.read_text()
        assert "ERROR" in log_content
        
    def test_security_integration(self, test_config: Dict[str, Any]):
        """测试安全集成"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 测试输入验证
        with pytest.raises(ValueError):
            analyzer.analyze("<script>alert('xss')</script>")
            
        # 测试 API 密钥处理
        assert "sk-" not in str(analyzer)
        assert "sk-" not in repr(analyzer)
        
        # 测试访问控制
        with pytest.raises(PermissionError):
            analyzer.analyze_system_file("/etc/passwd")
            
        # 测试数据清理
        result = analyzer.analyze("测试需求")
        assert not any("<script>" in str(v) for v in result.values())
        
    def test_monitoring_integration(self, test_config: Dict[str, Any]):
        """测试监控集成"""
        config = Config(**test_config)
        analyzer = RequirementsAnalyzer(config)
        
        # 收集指标
        analyzer.analyze("测试需求")
        metrics = analyzer.get_metrics()
        
        # 验证指标
        assert "requests_total" in metrics
        assert "response_time_seconds" in metrics
        assert "errors_total" in metrics
        assert "memory_usage_bytes" in metrics
        
        # 验证告警
        with patch.object(
            analyzer,
            "get_memory_usage",
            return_value=1024  # 1GB
        ):
            alerts = analyzer.check_alerts()
            assert "memory_high" in alerts 