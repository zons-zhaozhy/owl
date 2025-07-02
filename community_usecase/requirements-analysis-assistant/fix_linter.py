#!/usr/bin/env python3
"""
Linter错误修复脚本
自动修复flake8检测到的代码风格问题
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

def get_flake8_errors() -> List[Tuple[str, str, str, str]]:
    """获取flake8错误列表"""
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "src/", "--max-line-length=88", "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s"],
            capture_output=True,
            text=True
        )
        
        errors = []
        for line in result.stdout.strip().split('\n'):
            if line:
                match = re.match(r'([^:]+):(\d+):(\d+): (\w+) (.+)', line)
                if match:
                    filepath, row, col, code, message = match.groups()
                    errors.append((filepath, int(row), int(col), code, message))
        
        return errors
    except Exception as e:
        print(f"获取flake8错误失败: {e}")
        return []

def fix_unused_imports(filepath: str, lines: List[str]) -> List[str]:
    """修复未使用的导入"""
    print(f"  修复未使用的导入: {filepath}")
    
    # 获取该文件的未使用导入
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", filepath, "--select=F401"],
            capture_output=True,
            text=True
        )
        
        unused_imports = []
        for line in result.stdout.strip().split('\n'):
            if line and 'F401' in line:
                match = re.search(r"'([^']+)' imported but unused", line)
                if match:
                    unused_imports.append(match.group(1))
    except Exception:
        pass
    
    if not unused_imports:
        return lines
    
    new_lines = []
    for line in lines:
        should_remove = False
        
        # 检查是否是未使用的导入行
        for unused_import in unused_imports:
            # 处理各种导入格式
            patterns = [
                rf'^import\s+{re.escape(unused_import)}$',
                rf'^from\s+[^\s]+\s+import\s+{re.escape(unused_import)}$',
                rf'^from\s+[^\s]+\s+import\s+[^,]*{re.escape(unused_import)}[^,]*$',
            ]
            
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    should_remove = True
                    break
            
            if should_remove:
                break
        
        if not should_remove:
            new_lines.append(line)
    
    return new_lines

def fix_whitespace_issues(lines: List[str]) -> List[str]:
    """修复空白字符问题"""
    new_lines = []
    
    for line in lines:
        # W291: 移除行尾空白
        line = line.rstrip()
        # W293: 移除空行中的空白
        if not line.strip():
            line = ""
        new_lines.append(line)
    
    # W292: 确保文件以换行符结尾
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    
    return new_lines

def fix_blank_lines(lines: List[str]) -> List[str]:
    """修复空行问题"""
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # E302: 类和函数定义前需要2个空行
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if (next_line.startswith('class ') or 
                next_line.startswith('def ') or
                next_line.startswith('async def ')):
                
                # 检查前面有多少空行
                blank_count = 0
                j = i
                while j >= 0 and not lines[j].strip():
                    blank_count += 1
                    j -= 1
                
                # 如果不是文件开头，需要2个空行
                if j > 0 and blank_count < 2:
                    new_lines.extend([''] * (2 - blank_count))
        
        # E305: 类和函数定义后需要2个空行
        if (line.strip().startswith('class ') or 
            line.strip().startswith('def ') or
            line.strip().startswith('async def ')):
            
            # 找到函数/类的结束
            indent_level = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines):
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent_level:
                    break
                j += 1
            
            # 检查后面的空行
            if j < len(lines):
                blank_count = 0
                k = j
                while k < len(lines) and not lines[k].strip():
                    blank_count += 1
                    k += 1
                
                if k < len(lines) and blank_count < 2:
                    # 在适当位置插入空行
                    pass  # 这个比较复杂，暂时跳过
        
        i += 1
    
    return new_lines

def fix_line_length(lines: List[str], max_length: int = 88) -> List[str]:
    """修复行长度问题"""
    new_lines = []
    
    for line in lines:
        if len(line) <= max_length:
            new_lines.append(line)
            continue
        
        # 尝试在合适的地方断行
        if ' import ' in line and len(line) > max_length:
            # 处理长导入语句
            if 'from ' in line and ' import ' in line:
                parts = line.split(' import ')
                if len(parts) == 2:
                    from_part = parts[0]
                    import_part = parts[1]
                    
                    # 如果导入部分很长，尝试多行导入
                    if ',' in import_part:
                        imports = [imp.strip() for imp in import_part.split(',')]
                        new_lines.append(from_part + ' import (')
                        for imp in imports[:-1]:
                            new_lines.append(f'    {imp},')
                        new_lines.append(f'    {imports[-1]}')
                        new_lines.append(')')
                        continue
        
        # 其他情况保持原样，避免破坏代码
        new_lines.append(line)
    
    return new_lines

def fix_other_issues(lines: List[str]) -> List[str]:
    """修复其他问题"""
    new_lines = []
    
    for line in lines:
        # F541: 修复空的f-string
        line = re.sub(r'f"([^{]*)"', r'"\1"', line)
        line = re.sub(r"f'([^{]*)'", r"'\1'", line)
        
        # E203: 修复切片中的空格
        line = re.sub(r'\s+:', ':', line)
        
        new_lines.append(line)
    
    return new_lines

def remove_unused_variables(lines: List[str]) -> List[str]:
    """移除未使用的变量"""
    new_lines = []
    
    for line in lines:
        # F841: 未使用的变量，添加下划线前缀
        if '=' in line and not line.strip().startswith('#'):
            # 简单的变量赋值检测
            match = re.match(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line)
            if match:
                indent, var_name = match.groups()
                if not var_name.startswith('_'):
                    # 检查变量是否在后续行中使用
                    var_used = False
                    for future_line in lines[lines.index(line)+1:]:
                        if var_name in future_line and '=' not in future_line.split(var_name)[0]:
                            var_used = True
                            break
                    
                    if not var_used:
                        line = line.replace(var_name, f'_{var_name}', 1)
        
        new_lines.append(line)
    
    return new_lines

def fix_file(filepath: str) -> bool:
    """修复单个文件"""
    print(f"修复文件: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 移除换行符但保留原始行结构
        lines = [line.rstrip('\n\r') for line in lines]
        
        # 应用各种修复
        lines = fix_unused_imports(filepath, lines)
        lines = fix_whitespace_issues(lines)
        lines = fix_other_issues(lines)
        lines = remove_unused_variables(lines)
        lines = fix_line_length(lines)
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        return True
        
    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False

def apply_black_formatting():
    """应用black格式化"""
    print("应用black格式化...")
    try:
        subprocess.run(["python", "-m", "black", "src/", "--line-length=88"], 
                      check=False, capture_output=True)
        print("  ✅ black格式化完成")
    except Exception as e:
        print(f"  ⚠️ black格式化失败: {e}")

def fix_specific_errors():
    """修复特定的已知错误"""
    print("修复特定错误...")
    
    # 修复重复定义的问题
    files_to_fix = [
        "src/owl_requirements/agents/requirements_extractor.py",
        "src/owl_requirements/core/config.py",
        "src/owl_requirements/cli/app.py"
    ]
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            print(f"  修复特定错误: {filepath}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 移除重复的函数定义
                if 'requirements_extractor.py' in filepath:
                    # 移除重复的_validate_requirements定义
                    lines = content.split('\n')
                    new_lines = []
                    in_duplicate_function = False
                    
                    for i, line in enumerate(lines):
                        if 'def _validate_requirements(' in line and i > 200:  # 第二个定义
                            in_duplicate_function = True
                            continue
                        
                        if in_duplicate_function:
                            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                                in_duplicate_function = False
                                new_lines.append(line)
                            continue
                        
                        new_lines.append(line)
                    
                    content = '\n'.join(new_lines)
                
                # 移除重复的导入和定义
                if 'config.py' in filepath:
                    # 移除重复的AgentStatus定义
                    content = re.sub(r'\n\nclass AgentStatus\(Enum\):.*?(?=\n\n|\n$)', '', content, flags=re.DOTALL)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"    ⚠️ 修复失败: {e}")

def main():
    """主函数"""
    print("🚀 开始修复linter错误...")
    
    # 1. 修复特定的已知错误
    fix_specific_errors()
    
    # 2. 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk("src"):
        # 跳过__pycache__目录
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 3. 逐个修复文件
    success_count = 0
    for filepath in python_files:
        if fix_file(filepath):
            success_count += 1
    
    print(f"成功修复 {success_count}/{len(python_files)} 个文件")
    
    # 4. 应用black格式化
    apply_black_formatting()
    
    # 5. 再次检查错误数量
    print("\n检查修复结果...")
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "src/", "--count", "--statistics", "--max-line-length=88"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 所有linter错误已修复！")
        else:
            error_count = len([line for line in result.stdout.split('\n') if ':' in line and 'src/' in line])
            print(f"📊 剩余错误数量: {error_count}")
            print("主要错误类型:")
            print(result.stdout.split('\n')[-10:])  # 显示最后几行统计信息
            
    except Exception as e:
        print(f"检查失败: {e}")
    
    print("🎉 Linter修复完成！")

if __name__ == "__main__":
    main() 