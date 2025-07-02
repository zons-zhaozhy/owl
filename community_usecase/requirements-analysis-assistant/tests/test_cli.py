"""
测试CLI模块
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.owl_requirements.cli.app import create_cli_app, CLISession
from src.owl_requirements.core.config import SystemConfig
from src.owl_requirements.core.exceptions import RequirementsAnalysisError

import json
from typer.testing import CliRunner

from src.owl_requirements.core.config import Config
from src.owl_requirements.core.exceptions import CLIError

class TestCLI:
    """CLI 测试类"""
    
    def test_version_command(self):
        """测试版本命令"""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "OWL Requirements Analysis" in result.stdout
        assert "版本" in result.stdout
        
    def test_analyze_command(self, tmp_path: Path, test_input_text: str):
        """测试分析命令"""
        # 创建输入文件
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        # 创建输出文件
        output_file = tmp_path / "output.json"
        
        runner = CliRunner()
        result = runner.invoke(app, [
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
            
    def test_analyze_stdin(self, test_input_text: str):
        """测试从标准输入分析"""
        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "-"], input=test_input_text)
        
        assert result.exit_code == 0
        assert "requirements" in result.stdout
        assert "analysis" in result.stdout
        
    def test_analyze_with_format(self, tmp_path: Path, test_input_text: str):
        """测试不同格式的分析输出"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        runner = CliRunner()
        
        # JSON 格式
        json_output = tmp_path / "output.json"
        result = runner.invoke(app, [
            "analyze",
            str(input_file),
            "--output",
            str(json_output),
            "--format",
            "json"
        ])
        assert result.exit_code == 0
        assert json_output.exists()
        
        # Markdown 格式
        md_output = tmp_path / "output.md"
        result = runner.invoke(app, [
            "analyze",
            str(input_file),
            "--output",
            str(md_output),
            "--format",
            "markdown"
        ])
        assert result.exit_code == 0
        assert md_output.exists()
        
    def test_batch_analyze(self, tmp_path: Path):
        """测试批量分析"""
        # 创建输入目录
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # 创建多个输入文件
        for i in range(3):
            input_file = input_dir / f"req_{i}.txt"
            input_file.write_text(f"需求文本 {i}")
            
        # 创建输出目录
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "analyze-batch",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--pattern",
            "*.txt"
        ])
        
        assert result.exit_code == 0
        assert len(list(output_dir.glob("*.json"))) == 3
        
    def test_config_command(self, tmp_path: Path, test_config: dict):
        """测试配置命令"""
        runner = CliRunner()
        
        # 显示当前配置
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "system" in result.stdout
        assert "llm" in result.stdout
        
        # 设置配置
        result = runner.invoke(app, [
            "config",
            "set",
            "llm.provider",
            "anthropic"
        ])
        assert result.exit_code == 0
        
        # 验证配置更新
        result = runner.invoke(app, ["config", "show"])
        assert "anthropic" in result.stdout
        
    def test_interactive_mode(self):
        """测试交互模式"""
        runner = CliRunner()
        
        # 模拟用户输入
        input_sequence = "需求文本\n\n"
        result = runner.invoke(app, ["interactive"], input=input_sequence)
        
        assert result.exit_code == 0
        assert "欢迎使用" in result.stdout
        assert "分析结果" in result.stdout
        
    def test_error_handling(self, tmp_path: Path):
        """测试错误处理"""
        runner = CliRunner()
        
        # 文件不存在
        result = runner.invoke(app, [
            "analyze",
            "nonexistent.txt"
        ])
        assert result.exit_code == 1
        assert "错误" in result.stdout
        
        # 无效的格式
        result = runner.invoke(app, [
            "analyze",
            "-",
            "--format",
            "invalid"
        ])
        assert result.exit_code == 1
        assert "无效的格式" in result.stdout
        
    def test_progress_reporting(self, tmp_path: Path, test_input_text: str):
        """测试进度报告"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "analyze",
            str(input_file),
            "--show-progress"
        ])
        
        assert result.exit_code == 0
        assert "进度" in result.stdout
        assert "完成" in result.stdout
        
    def test_verbose_output(self, tmp_path: Path, test_input_text: str):
        """测试详细输出"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "analyze",
            str(input_file),
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert "详细信息" in result.stdout
        assert "DEBUG" in result.stdout
        
    def test_quiet_mode(self, tmp_path: Path, test_input_text: str):
        """测试安静模式"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        output_file = tmp_path / "output.json"
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "analyze",
            str(input_file),
            "--output",
            str(output_file),
            "--quiet"
        ])
        
        assert result.exit_code == 0
        assert result.stdout == ""
        assert output_file.exists()
        
    def test_help_command(self):
        """测试帮助命令"""
        runner = CliRunner()
        
        # 主帮助
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "用法" in result.stdout
        assert "命令" in result.stdout
        
        # 子命令帮助
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "选项" in result.stdout
        
    def test_completion_command(self):
        """测试自动完成命令"""
        runner = CliRunner()
        
        # Bash 完成
        result = runner.invoke(app, [
            "completion",
            "bash"
        ])
        assert result.exit_code == 0
        assert "complete" in result.stdout
        
        # Zsh 完成
        result = runner.invoke(app, [
            "completion",
            "zsh"
        ])
        assert result.exit_code == 0
        assert "compdef" in result.stdout
        
    def test_export_command(self, tmp_path: Path, test_input_text: str):
        """测试导出命令"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        runner = CliRunner()
        
        # 导出为 PDF
        pdf_output = tmp_path / "output.pdf"
        result = runner.invoke(app, [
            "export",
            str(input_file),
            "--format",
            "pdf",
            "--output",
            str(pdf_output)
        ])
        assert result.exit_code == 0
        assert pdf_output.exists()
        
        # 导出为 Word
        docx_output = tmp_path / "output.docx"
        result = runner.invoke(app, [
            "export",
            str(input_file),
            "--format",
            "docx",
            "--output",
            str(docx_output)
        ])
        assert result.exit_code == 0
        assert docx_output.exists()
        
    def test_validate_command(self, tmp_path: Path, test_input_text: str):
        """测试验证命令"""
        input_file = tmp_path / "input.txt"
        input_file.write_text(test_input_text)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "validate",
            str(input_file)
        ])
        
        assert result.exit_code == 0
        assert "验证通过" in result.stdout
        
        # 测试无效输入
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("无效的需求格式")
        
        result = runner.invoke(app, [
            "validate",
            str(invalid_file)
        ])
        
        assert result.exit_code == 1
        assert "验证失败" in result.stdout 