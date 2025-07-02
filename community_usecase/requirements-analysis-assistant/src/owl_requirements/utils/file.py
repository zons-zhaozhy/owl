from typing import Optional, List, Dict, Any
import os
import json
import yaml
from pathlib import Path
from ..utils.exceptions import StorageError


def ensure_directory_exists(path: str) -> None:
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        raise StorageError(f"创建目录失败: {str(e)}")


def ensure_directory(path: str) -> None:
    """确保目录存在 - 保持向后兼容"""
    ensure_directory_exists(path)


def read_file_safe(file_path: str) -> str:
    """安全读取文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise StorageError(f"读取文件失败: {str(e)}")


def write_file_safe(file_path: str, content: str) -> None:
    """安全写入文件内容"""
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise StorageError(f"写入文件失败: {str(e)}")


def get_file_extension(file_path: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(file_path)[1].lower()


def list_files_by_extension(directory: str, extension: str) -> List[str]:
    """根据扩展名列出文件"""
    try:
        path = Path(directory)
        if not extension.startswith("."):
            extension = "." + extension
        return [str(f) for f in path.glob(f"*{extension}")]
    except Exception as e:
        raise StorageError(f"列出文件失败: {str(e)}")


def read_file(file_path: str) -> str:
    """读取文件内容"""
    return read_file_safe(file_path)


def read_json(file_path: str) -> Dict[str, Any]:
    """读取JSON文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise StorageError(f"读取JSON文件失败: {str(e)}")


def write_json(file_path: str, data: Dict[str, Any]) -> None:
    """写入JSON文件"""
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise StorageError(f"写入JSON文件失败: {str(e)}")


def read_yaml(file_path: str) -> Dict[str, Any]:
    """读取YAML文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise StorageError(f"读取YAML文件失败: {str(e)}")


def write_yaml(file_path: str, data: Dict[str, Any]) -> None:
    """写入YAML文件"""
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        raise StorageError(f"写入YAML文件失败: {str(e)}")


def read_text(file_path: str) -> str:
    """读取文本文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise StorageError(f"读取文本文件失败: {str(e)}")


def write_text(file_path: str, content: str) -> None:
    """写入文本文件"""
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise StorageError(f"写入文本文件失败: {str(e)}")


def list_files(directory: str, pattern: Optional[str] = None) -> List[str]:
    """列出目录中的文件"""
    try:
        path = Path(directory)
        if pattern:
            return [str(f) for f in path.glob(pattern)]
        return [str(f) for f in path.iterdir() if f.is_file()]
    except Exception as e:
        raise StorageError(f"列出文件失败: {str(e)}")


def delete_file(file_path: str) -> None:
    """删除文件"""
    try:
        os.remove(file_path)
    except Exception as e:
        raise StorageError(f"删除文件失败: {str(e)}")


def copy_file(src: str, dst: str) -> None:
    """复制文件"""
    try:
        import shutil

        ensure_directory_exists(os.path.dirname(dst))
        shutil.copy2(src, dst)
    except Exception as e:
        raise StorageError(f"复制文件失败: {str(e)}")


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        raise StorageError(f"获取文件大小失败: {str(e)}")


def get_file_mtime(file_path: str) -> float:
    """获取文件最后修改时间（时间戳）"""
    try:
        return os.path.getmtime(file_path)
    except Exception as e:
        raise StorageError(f"获取文件修改时间失败: {str(e)}")


def is_file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(file_path)


def is_dir_exists(dir_path: str) -> bool:
    """检查目录是否存在"""
    return os.path.isdir(dir_path)


def write_file(file_path: str, content: str) -> None:
    """写入文件内容"""
    write_file_safe(file_path, content)


def remove_file(file_path: str) -> None:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        raise StorageError(f"删除文件失败: {str(e)}")
