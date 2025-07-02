"""
JSON 工具模块

提供安全的 JSON 文件操作功能。
"""

import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


def extract_json_safely(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中安全地提取JSON对象。

    Args:
        text: 包含JSON的文本

    Returns:
        Optional[Dict[str, Any]]: 提取的JSON对象，如果提取失败则返回None
    """
    if not text:
        logger.warning("输入文本为空")
        return None

    # 尝试从代码块中提取
    code_block_patterns = [
        r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
        r"```\s*([\s\S]*?)\s*```",  # ``` ... ```
    ]

    for pattern in code_block_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                json_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                json_str = clean_json_string(json_str)
                result = json.loads(json_str)
                if isinstance(result, dict):
                    return result
            except Exception as e:
                logger.debug(f"从代码块提取JSON失败: {e}")
                continue

    # 尝试直接提取JSON对象
    try:
        json_pattern = r"\{(?:[^{}]|(?R))*\}"
        matches = re.finditer(json_pattern, text)
        largest_json = None
        max_length = 0

        for match in matches:
            try:
                json_str = match.group(0)
                if len(json_str) > max_length:
                    json_str = clean_json_string(json_str)
                    result = json.loads(json_str)
                    if isinstance(result, dict):
                        largest_json = result
                        _max_length = len(json_str)
            except Exception:
                continue

        if largest_json:
            return largest_json

    except Exception as e:
        logger.error(f"JSON提取失败: {e}")

    logger.warning("未找到有效的JSON")
    return None


def clean_json_string(json_str: str) -> str:
    """
    清理JSON字符串，移除可能导致解析错误的字符。

    Args:
        json_str: 原始JSON字符串

    Returns:
        str: 清理后的JSON字符串
    """
    # 移除前后的代码块标记
    json_str = json_str.strip()
    json_str = re.sub(r"^```\s*json\s*", "", json_str)
    json_str = re.sub(r"```\s*$", "", json_str)

    # 替换中文标点为英文标点
    punctuation_map = {
        '"': '"',
        '"': '"',
        """: "'", """: "'",
        "，": ",",
        "。": ".",
        "：": ":",
        "；": ";",
        "？": "?",
        "！": "!",
        "【": "[",
        "】": "]",
        "（": "(",
        "）": ")",
        "「": "{",
        "」": "}",
    }

    for cn_punct, en_punct in punctuation_map.items():
        json_str = json_str.replace(cn_punct, en_punct)

    # 移除不可见字符
    json_str = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", json_str)

    return json_str


def validate_json_structure(
    data: Dict[str, Any], required_fields: Dict[str, type]
) -> bool:
    """
    验证JSON对象的结构。

    Args:
        data: 要验证的JSON对象
        required_fields: 必需字段及其类型的映射

    Returns:
        bool: 验证是否通过
    """
    try:
        for field, field_type in required_fields.items():
            if field not in data:
                logger.warning(f"缺少必需字段: {field}")
                return False

            if not isinstance(data[field], field_type):
                logger.warning(
                    f"字段 {field} 的类型错误: "
                    f"期望 {field_type.__name__}, "
                    f"实际 {type(data[field]).__name__}"
                )
                return False

        return True

    except Exception as e:
        logger.error(f"JSON结构验证失败: {e}")
        return False


def merge_json_objects(*objects: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个JSON对象。

    Args:
        *objects: 要合并的JSON对象

    Returns:
        Dict[str, Any]: 合并后的JSON对象
    """
    result = {}
    for obj in objects:
        if not isinstance(obj, dict):
            logger.warning(f"跳过非字典对象: {type(obj)}")
            continue

        deep_update(result, obj)

    return result


def deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归更新字典。

    Args:
        target: 目标字典
        source: 源字典

    Returns:
        Dict[str, Any]: 更新后的字典
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    return target


def load_json_safe(file_path: Union[str, Path]) -> Any:
    """
    安全地加载JSON文件。

    Args:
        file_path: JSON文件路径，可以是字符串或Path对象

    Returns:
        解析后的JSON数据

    Raises:
        FileNotFoundError: 文件不存在时抛出
        json.JSONDecodeError: JSON格式无效时抛出
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_safe(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    安全地保存数据到JSON文件。

    Args:
        data: 要保存的数据
        file_path: 目标文件路径，可以是字符串或Path对象
        indent: JSON缩进空格数，默认为2

    Raises:
        TypeError: 数据不可序列化时抛出
        OSError: 文件系统操作错误时抛出
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # 确保父目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    验证JSON数据是否符合指定的schema

    Args:
        data: 待验证的JSON数据
        schema: JSON schema定义

    Raises:
        ValidationError: 验证失败时抛出
    """
    try:
        # 验证必需字段
        if "required" in schema:
            missing_fields = [
                field for field in schema["required"] if field not in data
            ]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        # 验证字段类型
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in data:
                    _validate_field_type(data[field], field_schema, field)

    except Exception as e:
        raise ValidationError(f"JSON schema validation failed: {str(e)}")


def _validate_field_type(value: Any, schema: Dict[str, Any], field_name: str) -> None:
    """
    验证字段类型

    Args:
        value: 字段值
        schema: 字段schema
        field_name: 字段名称

    Raises:
        ValidationError: 验证失败时抛出
    """
    if "type" not in schema:
        return

    expected_type = schema["type"]

    if expected_type == "string" and not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string")
    elif expected_type == "number" and not isinstance(value, (int, float)):
        raise ValidationError(f"Field '{field_name}' must be a number")
    elif expected_type == "integer" and not isinstance(value, int):
        raise ValidationError(f"Field '{field_name}' must be an integer")
    elif expected_type == "boolean" and not isinstance(value, bool):
        raise ValidationError(f"Field '{field_name}' must be a boolean")
    elif expected_type == "array" and not isinstance(value, list):
        raise ValidationError(f"Field '{field_name}' must be an array")
    elif expected_type == "object" and not isinstance(value, dict):
        raise ValidationError(f"Field '{field_name}' must be an object")


def clean_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理JSON数据，移除空值和无效值

    Args:
        data: 待清理的JSON数据

    Returns:
        Dict[str, Any]: 清理后的JSON数据
    """
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        # 跳过空值
        if value is None:
            continue

        # 递归清理嵌套字典
        if isinstance(value, dict):
            cleaned_value = clean_json_data(value)
            if cleaned_value:  # 只保留非空字典
                cleaned[key] = cleaned_value

        # 清理列表
        elif isinstance(value, list):
            cleaned_list = [
                clean_json_data(item) if isinstance(item, dict) else item
                for item in value
                if item is not None
            ]
            if cleaned_list:  # 只保留非空列表
                cleaned[key] = cleaned_list

        # 保留其他非空值
        else:
            cleaned[key] = value

    return cleaned


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中提取JSON数据。

    这是extract_json_safely的别名，保持向后兼容性。

    Args:
        text: 包含JSON的文本

    Returns:
        Optional[Dict[str, Any]]: 提取的JSON数据，失败时返回None
    """
    return extract_json_safely(text)


def format_json_output(data: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
    """
    格式化JSON输出。

    Args:
        data: 要格式化的数据
        indent: 缩进空格数，默认为2
        ensure_ascii: 是否确保ASCII编码，默认为False

    Returns:
        str: 格式化后的JSON字符串

    Raises:
        TypeError: 数据不可序列化时抛出
    """
    try:
        return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
    except TypeError as e:
        logger.error(f"JSON序列化失败: {e}")
        raise
