"""
工具函数测试模块
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any

from src.owl_requirements.utils.file import (
    read_file,
    write_file,
    ensure_directory,
    list_files,
    remove_file
)
from src.owl_requirements.utils.text import (
    clean_text,
    extract_requirements,
    format_markdown,
    count_tokens
)
from src.owl_requirements.utils.validation import (
    validate_config,
    validate_input,
    validate_output_format
)
from src.owl_requirements.core.exceptions import ValidationError

class TestFileUtils:
    """文件工具测试类"""
    
    def test_read_file(self, tmp_path: Path):
        """测试文件读取"""
        file_path = tmp_path / "test.txt"
        content = "测试内容\n第二行"
        file_path.write_text(content)
        
        assert read_file(file_path) == content
        
    def test_write_file(self, tmp_path: Path):
        """测试文件写入"""
        file_path = tmp_path / "test.txt"
        content = "测试内容"
        
        write_file(file_path, content)
        assert file_path.read_text() == content
        
    def test_ensure_directory(self, tmp_path: Path):
        """测试目录确保"""
        dir_path = tmp_path / "test_dir" / "sub_dir"
        ensure_directory(dir_path)
        
        assert dir_path.exists()
        assert dir_path.is_dir()
        
    def test_list_files(self, tmp_path: Path):
        """测试文件列表"""
        # 创建测试文件
        (tmp_path / "test1.txt").touch()
        (tmp_path / "test2.txt").touch()
        (tmp_path / "test.json").touch()
        
        # 测试模式匹配
        txt_files = list_files(tmp_path, "*.txt")
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)
        
    def test_remove_file(self, tmp_path: Path):
        """测试文件删除"""
        file_path = tmp_path / "test.txt"
        file_path.touch()
        
        remove_file(file_path)
        assert not file_path.exists()
        
class TestTextUtils:
    """文本工具测试类"""
    
    def test_clean_text(self):
        """测试文本清理"""
        text = "  测试文本\n\n多余的空行\r\n特殊字符#@!  "
        cleaned = clean_text(text)
        
        assert cleaned == "测试文本\n多余的空行\n特殊字符#@!"
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
        
    def test_extract_requirements(self):
        """测试需求提取"""
        text = """
        系统需求：
        1. 用户认证
        2. 数据分析
        3. 报表导出
        """
        
        requirements = extract_requirements(text)
        assert len(requirements) == 3
        assert "用户认证" in requirements[0]
        assert "数据分析" in requirements[1]
        assert "报表导出" in requirements[2]
        
    def test_format_markdown(self):
        """测试 Markdown 格式化"""
        data = {
            "title": "测试报告",
            "sections": [
                {"heading": "简介", "content": "这是简介"},
                {"heading": "需求", "content": "这是需求"}
            ]
        }
        
        markdown = format_markdown(data)
        assert "# 测试报告" in markdown
        assert "## 简介" in markdown
        assert "## 需求" in markdown
        
    def test_count_tokens(self):
        """测试令牌计数"""
        text = "这是一个测试文本，用于计算令牌数。"
        count = count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0
        
class TestValidationUtils:
    """验证工具测试类"""
    
    def test_validate_config(self, test_config: Dict[str, Any]):
        """测试配置验证"""
        # 有效配置
        validate_config(test_config)
        
        # 无效配置
        invalid_config = test_config.copy()
        del invalid_config["system"]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config(invalid_config)
        assert "缺少必需的配置项" in str(exc_info.value)
        
    def test_validate_input(self):
        """测试输入验证"""
        # 有效输入
        valid_input = "这是有效的输入文本"
        validate_input(valid_input)
        
        # 空输入
        with pytest.raises(ValidationError) as exc_info:
            validate_input("")
        assert "输入文本不能为空" in str(exc_info.value)
        
        # 过长输入
        long_input = "测试" * 5000
        with pytest.raises(ValidationError) as exc_info:
            validate_input(long_input)
        assert "输入文本过长" in str(exc_info.value)
        
    def test_validate_output_format(self):
        """测试输出格式验证"""
        # 有效格式
        validate_output_format("json")
        validate_output_format("markdown")
        validate_output_format("text")
        
        # 无效格式
        with pytest.raises(ValidationError) as exc_info:
            validate_output_format("invalid")
        assert "不支持的输出格式" in str(exc_info.value)
        
    def test_yaml_handling(self, tmp_path: Path):
        """测试 YAML 处理"""
        # 写入 YAML
        config = {
            "name": "测试",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        yaml_file = tmp_path / "test.yaml"
        
        with open(yaml_file, "w") as f:
            yaml.dump(config, f, allow_unicode=True)
            
        # 读取 YAML
        with open(yaml_file) as f:
            loaded = yaml.safe_load(f)
            
        assert loaded == config
        
    def test_json_handling(self, tmp_path: Path):
        """测试 JSON 处理"""
        # 写入 JSON
        data = {
            "name": "测试",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        json_file = tmp_path / "test.json"
        
        with open(json_file, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # 读取 JSON
        with open(json_file) as f:
            loaded = json.load(f)
            
        assert loaded == data
        
    def test_path_handling(self, tmp_path: Path):
        """测试路径处理"""
        # 创建嵌套目录
        nested_dir = tmp_path / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)
        
        # 创建文件
        file_path = nested_dir / "test.txt"
        file_path.touch()
        
        # 测试路径操作
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert file_path.exists()
        assert file_path.is_file()
        assert file_path.parent == nested_dir
        
    def test_file_operations(self, tmp_path: Path):
        """测试文件操作"""
        # 创建目录
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        # 创建文件
        files = []
        for i in range(3):
            file_path = test_dir / f"test_{i}.txt"
            file_path.write_text(f"内容 {i}")
            files.append(file_path)
            
        # 列出文件
        found_files = list(test_dir.glob("*.txt"))
        assert len(found_files) == 3
        
        # 读取内容
        for i, file_path in enumerate(files):
            assert file_path.read_text() == f"内容 {i}"
            
        # 删除文件
        for file_path in files:
            file_path.unlink()
            assert not file_path.exists() 