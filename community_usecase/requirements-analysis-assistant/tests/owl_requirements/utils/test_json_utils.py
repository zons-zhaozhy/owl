"""Test JSON utilities."""

import pytest
import json
from pathlib import Path
from owl_requirements.utils.json_utils import load_json_safe, save_json_safe

def test_load_json_safe_valid_file(tmp_path: Path):
    """Test loading valid JSON file."""
    # Create test file
    test_data = {"key": "value"}
    test_file = tmp_path / "test.json"
    with test_file.open('w', encoding='utf-8') as f:
        json.dump(test_data, f)
    
    # Load and verify
    result = load_json_safe(test_file)
    assert result == test_data

def test_load_json_safe_invalid_json(tmp_path: Path):
    """Test loading invalid JSON file."""
    # Create invalid JSON file
    test_file = tmp_path / "invalid.json"
    with test_file.open('w', encoding='utf-8') as f:
        f.write("invalid json")
    
    # Should raise ValueError
    with pytest.raises(ValueError):
        load_json_safe(test_file)

def test_load_json_safe_nonexistent_file():
    """Test loading nonexistent file."""
    with pytest.raises(FileNotFoundError):
        load_json_safe(Path("nonexistent.json"))

def test_save_json_safe_valid_data(tmp_path: Path):
    """Test saving valid JSON data."""
    test_data = {"key": "value"}
    output_file = tmp_path / "output.json"
    
    # Save data
    save_json_safe(test_data, output_file)
    
    # Verify file exists and content
    assert output_file.exists()
    with output_file.open('r', encoding='utf-8') as f:
        saved_data = json.load(f)
        assert saved_data == test_data

def test_save_json_safe_invalid_path():
    """Test saving to invalid path."""
    test_data = {"key": "value"}
    with pytest.raises(OSError):
        save_json_safe(test_data, Path("/invalid/path/file.json"))

def test_save_json_safe_invalid_data(tmp_path: Path):
    """Test saving invalid JSON data."""
    class UnserializableObject:
        pass
    
    test_data = {"key": UnserializableObject()}
    output_file = tmp_path / "output.json"
    
    with pytest.raises(TypeError):
        save_json_safe(test_data, output_file)

def test_save_json_safe_with_nested_path(tmp_path: Path):
    """测试保存到嵌套路径"""
    test_data = {"test": "data"}
    nested_path = tmp_path / "a" / "b" / "c" / "test.json"
    
    save_json_safe(test_data, nested_path)
    
    assert nested_path.exists()
    with nested_path.open('r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == test_data

def test_save_json_safe_with_chinese_characters(tmp_path: Path):
    """测试保存包含中文字符的数据"""
    test_data = {
        "name": "测试名称",
        "description": "这是一段中文描述",
        "items": ["项目一", "项目二", "项目三"]
    }
    output_path = tmp_path / "chinese.json"
    
    save_json_safe(test_data, output_path)
    
    assert output_path.exists()
    with output_path.open('r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    assert loaded_data == test_data

def test_save_and_load_with_different_indentation(tmp_path: Path):
    """测试不同缩进的保存和加载"""
    test_data = {
        "level1": {
            "level2": {
                "level3": ["a", "b", "c"]
            }
        }
    }
    output_path = tmp_path / "indented.json"
    
    # 使用4空格缩进保存
    save_json_safe(test_data, output_path, indent=4)
    
    # 验证文件内容格式
    content = output_path.read_text(encoding='utf-8')
    assert "    " in content  # 应该包含4空格缩进
    
    # 加载并验证数据
    loaded_data = load_json_safe(output_path)
    assert loaded_data == test_data 