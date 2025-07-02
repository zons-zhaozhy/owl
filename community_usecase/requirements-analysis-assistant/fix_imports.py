#!/usr/bin/env python3
"""
智能导入修复脚本
修复未定义的名称、重复导入、缺失导入等问题
"""

import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 常见的导入映射
IMPORT_MAPPINGS = {
    # 基础类型
    'Dict': 'from typing import Dict',
    'List': 'from typing import List', 
    'Optional': 'from typing import Optional',
    'Any': 'from typing import Any',
    'Union': 'from typing import Union',
    'Tuple': 'from typing import Tuple',
    'Set': 'from typing import Set',
    'Callable': 'from typing import Callable',
    
    # OWL/CAMEL相关
    'BaseAgent': 'from camel.agents import BaseAgent',
    'ChatAgent': 'from camel.agents import ChatAgent', 
    'BaseMessage': 'from camel.messages import BaseMessage',
    'RolePlaying': 'from camel.societies import RolePlaying',
    
    # 项目内部模块
    'SystemConfig': 'from ..core.config import SystemConfig',
    'LLMConfig': 'from ..core.config import LLMConfig',
    'LLMProvider': 'from ..utils.enums import LLMProvider',
    'AgentStatus': 'from ..utils.enums import AgentStatus',
    'DocumentFormat': 'from ..utils.enums import DocumentFormat',
    'ProcessingStatus': 'from ..utils.enums import ProcessingStatus',
    
    # 异常类
    'RequirementsAnalysisError': 'from ..core.exceptions import RequirementsAnalysisError',
    'LLMServiceError': 'from ..core.exceptions import LLMServiceError',
    'ConfigurationError': 'from ..core.exceptions import ConfigurationError',
    'ValidationError': 'from ..core.exceptions import ValidationError',
    
    # 服务和管理器
    'LLMManager': 'from ..services.llm_manager import LLMManager',
    'get_llm_manager': 'from ..services.llm_manager import get_llm_manager',
    
    # 工具和实用程序
    'extract_json_from_text': 'from ..utils.json_utils import extract_json_from_text',
    'format_json_output': 'from ..utils.json_utils import format_json_output',
    'load_template': 'from ..utils.template_manager import load_template',
    'TemplateManager': 'from ..utils.template_manager import TemplateManager',
    
    # 协调器
    'coordinator': 'from ..core.coordinator import get_coordinator',
    'RequirementsCoordinator': 'from ..core.coordinator import RequirementsCoordinator',
    'get_coordinator': 'from ..core.coordinator import get_coordinator',
}

def analyze_file_imports(filepath: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """分析文件的导入情况"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"  ⚠️ 语法错误 {filepath}: {e}")
            return set(), set(), set()
        
        imported_names = set()
        used_names = set()
        defined_names = set()
        
        # 收集导入的名称
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                if node.names:
                    for alias in node.names:
                        if alias.name != '*':
                            name = alias.asname if alias.asname else alias.name
                            imported_names.add(name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                elif isinstance(node.ctx, ast.Store):
                    defined_names.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
        
        return imported_names, used_names, defined_names
        
    except Exception as e:
        print(f"  ⚠️ 分析文件失败 {filepath}: {e}")
        return set(), set(), set()

def find_missing_imports(filepath: str) -> List[str]:
    """查找缺失的导入"""
    imported_names, used_names, defined_names = analyze_file_imports(filepath)
    
    # 找到使用但未导入且未定义的名称
    missing_names = used_names - imported_names - defined_names
    
    # 过滤掉内置名称
    builtin_names = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
    missing_names = missing_names - builtin_names
    
    # 过滤掉一些常见的局部变量
    common_vars = {'self', 'cls', 'args', 'kwargs', 'e', 'i', 'j', 'k', 'v', 'key', 'value', 'item', 'line', 'result'}
    missing_names = missing_names - common_vars
    
    missing_imports = []
    for name in missing_names:
        if name in IMPORT_MAPPINGS:
            missing_imports.append(IMPORT_MAPPINGS[name])
    
    return missing_imports

def add_missing_imports(filepath: str, missing_imports: List[str]) -> bool:
    """添加缺失的导入"""
    if not missing_imports:
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到导入区域的结束位置
        import_end_line = 0
        in_docstring = False
        docstring_quotes = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 处理模块级文档字符串
            if i < 5 and (stripped.startswith('"""') or stripped.startswith("'''")):
                if not in_docstring:
                    in_docstring = True
                    docstring_quotes = stripped[:3]
                    if len(stripped) > 3 and stripped.endswith(docstring_quotes):
                        in_docstring = False
                elif stripped.endswith(docstring_quotes):
                    in_docstring = False
                continue
            
            if in_docstring:
                continue
            
            # 跳过注释和空行
            if stripped.startswith('#') or not stripped:
                continue
            
            # 如果是导入语句，更新结束位置
            if stripped.startswith(('import ', 'from ')):
                import_end_line = i + 1
            elif stripped and not stripped.startswith(('import ', 'from ')):
                # 遇到非导入语句，停止搜索
                break
        
        # 在导入区域末尾添加缺失的导入
        new_lines = lines[:import_end_line]
        
        # 添加缺失的导入
        for import_stmt in missing_imports:
            new_lines.append(import_stmt + '\n')
        
        # 如果添加了导入，确保有空行分隔
        if missing_imports and import_end_line < len(lines):
            if lines[import_end_line].strip():  # 如果下一行不是空行
                new_lines.append('\n')
        
        new_lines.extend(lines[import_end_line:])
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"  ✅ 添加了 {len(missing_imports)} 个导入")
        return True
        
    except Exception as e:
        print(f"  ⚠️ 添加导入失败: {e}")
        return False

def fix_undefined_names(filepath: str) -> bool:
    """修复未定义的名称"""
    print(f"  修复未定义名称: {filepath}")
    
    # 特殊处理某些文件
    if 'coordinator.py' in filepath:
        return fix_coordinator_issues(filepath)
    
    missing_imports = find_missing_imports(filepath)
    if missing_imports:
        print(f"    发现缺失导入: {missing_imports}")
        return add_missing_imports(filepath, missing_imports)
    
    return False

def fix_coordinator_issues(filepath: str) -> bool:
    """修复coordinator文件的特殊问题"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加coordinator全局变量的定义
        if 'coordinator' in content and 'global coordinator' not in content:
            # 在文件开头添加全局变量声明
            lines = content.split('\n')
            
            # 找到合适的位置插入全局变量定义
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('class ') or line.strip().startswith('def '):
                    insert_pos = i
                    break
            
            if insert_pos > 0:
                lines.insert(insert_pos, '')
                lines.insert(insert_pos + 1, '# 全局协调器实例')
                lines.insert(insert_pos + 2, '_coordinator_instance = None')
                lines.insert(insert_pos + 3, '')
                lines.insert(insert_pos + 4, 'def get_coordinator():')
                lines.insert(insert_pos + 5, '    """获取全局协调器实例"""')
                lines.insert(insert_pos + 6, '    global _coordinator_instance')
                lines.insert(insert_pos + 7, '    if _coordinator_instance is None:')
                lines.insert(insert_pos + 8, '        from .config import SystemConfig')
                lines.insert(insert_pos + 9, '        config = SystemConfig()')
                lines.insert(insert_pos + 10, '        _coordinator_instance = RequirementsCoordinator(config)')
                lines.insert(insert_pos + 11, '    return _coordinator_instance')
                lines.insert(insert_pos + 12, '')
                
                # 替换所有使用coordinator的地方
                content = '\n'.join(lines)
                content = re.sub(r'\bcoordinator\b', 'get_coordinator()', content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return True
    
    except Exception as e:
        print(f"    ⚠️ 修复coordinator失败: {e}")
    
    return False

def remove_duplicate_imports(filepath: str) -> bool:
    """移除重复的导入"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        seen_imports = set()
        new_lines = []
        modified = False
        
        for line in lines:
            stripped = line.strip()
            
            # 检查是否是导入语句
            if stripped.startswith(('import ', 'from ')):
                if stripped in seen_imports:
                    # 跳过重复的导入
                    modified = True
                    continue
                else:
                    seen_imports.add(stripped)
            
            new_lines.append(line)
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  ✅ 移除了重复导入")
            return True
            
    except Exception as e:
        print(f"  ⚠️ 移除重复导入失败: {e}")
    
    return False

def fix_redefinition_issues(filepath: str) -> bool:
    """修复重复定义问题"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # 修复typer重复导入
        if 'cli/app.py' in filepath:
            # 移除重复的typer导入
            lines = content.split('\n')
            new_lines = []
            typer_imported = False
            
            for line in lines:
                if 'import typer' in line or 'from typer import' in line:
                    if not typer_imported:
                        new_lines.append(line)
                        typer_imported = True
                    else:
                        modified = True
                        continue
                else:
                    new_lines.append(line)
            
            if modified:
                content = '\n'.join(new_lines)
        
        # 修复其他重复定义
        # 这里可以添加更多特定的修复逻辑
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"  ⚠️ 修复重复定义失败: {e}")
    
    return False

def fix_syntax_errors(filepath: str) -> bool:
    """修复语法错误"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有语法错误
        try:
            ast.parse(content)
            return False  # 没有语法错误
        except IndentationError as e:
            print(f"  修复缩进错误: {e}")
            # 尝试修复缩进问题
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # 简单的缩进修复：将制表符转换为空格
                fixed_line = line.expandtabs(4)
                fixed_lines.append(fixed_line)
            
            fixed_content = '\n'.join(fixed_lines)
            
            # 验证修复结果
            try:
                ast.parse(fixed_content)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"  ✅ 修复了缩进错误")
                return True
            except:
                pass
        
        except SyntaxError as e:
            print(f"  ⚠️ 语法错误无法自动修复: {e}")
    
    except Exception as e:
        print(f"  ⚠️ 检查语法错误失败: {e}")
    
    return False

def fix_file_imports(filepath: str) -> bool:
    """修复单个文件的导入问题"""
    print(f"修复文件: {filepath}")
    
    modified = False
    
    # 1. 修复语法错误
    if fix_syntax_errors(filepath):
        modified = True
    
    # 2. 移除重复导入
    if remove_duplicate_imports(filepath):
        modified = True
    
    # 3. 修复重复定义
    if fix_redefinition_issues(filepath):
        modified = True
    
    # 4. 修复未定义的名称
    if fix_undefined_names(filepath):
        modified = True
    
    return modified

def create_missing_enums():
    """创建缺失的枚举定义"""
    print("创建缺失的枚举定义...")
    
    enums_file = "src/owl_requirements/utils/enums.py"
    
    try:
        with open(enums_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否缺少AgentStatus
        if 'class AgentStatus' not in content:
            content += '''

class AgentStatus(Enum):
    """智能体状态"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"
'''
        
        # 检查是否缺少ProcessingStatus
        if 'class ProcessingStatus' not in content:
            content += '''

class ProcessingStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
'''
        
        with open(enums_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ 枚举定义已更新")
        
    except Exception as e:
        print(f"  ⚠️ 创建枚举失败: {e}")

def main():
    """主函数"""
    print("🚀 开始修复导入和定义问题...")
    
    # 1. 创建缺失的枚举定义
    create_missing_enums()
    
    # 2. 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk("src"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 3. 修复每个文件
    success_count = 0
    for filepath in python_files:
        if fix_file_imports(filepath):
            success_count += 1
    
    print(f"成功修复 {success_count} 个文件")
    
    # 4. 再次检查错误
    print("\n检查修复结果...")
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "src/", "--count", "--statistics", "--max-line-length=88"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 所有导入错误已修复！")
        else:
            error_lines = [line for line in result.stdout.split('\n') if ':' in line and 'src/' in line]
            print(f"📊 剩余错误数量: {len(error_lines)}")
            
            # 显示主要错误类型
            error_types = {}
            for line in error_lines:
                if ' F' in line:  # F开头的错误
                    match = re.search(r' (F\d+) ', line)
                    if match:
                        error_code = match.group(1)
                        error_types[error_code] = error_types.get(error_code, 0) + 1
            
            if error_types:
                print("主要错误类型:")
                for error_code, count in sorted(error_types.items()):
                    print(f"  {error_code}: {count} 个")
    
    except Exception as e:
        print(f"检查失败: {e}")
    
    print("🎉 导入修复完成！")

if __name__ == "__main__":
    main() 