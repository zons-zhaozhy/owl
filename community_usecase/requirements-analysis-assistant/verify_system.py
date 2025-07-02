#!/usr/bin/env python3
"""
系统验证脚本 - 验证清理后的系统状态
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any

def check_template_consistency() -> Dict[str, Any]:
    """检查模板一致性"""
    print("🔍 检查模板一致性...")
    
    template_dir = "templates/prompts"
    required_templates = [
        "requirements_extraction.json",
        "requirements_analysis.json", 
        "quality_checker.json",
        "documentation_generator.json"
    ]
    
    results = {
        "template_dir_exists": os.path.exists(template_dir),
        "found_templates": [],
        "missing_templates": [],
        "total_templates": 0
    }
    
    if results["template_dir_exists"]:
        for template in required_templates:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                results["found_templates"].append(template)
            else:
                results["missing_templates"].append(template)
        
        # 统计所有模板文件
        if os.path.exists(template_dir):
            all_templates = [f for f in os.listdir(template_dir) if f.endswith('.json')]
            results["total_templates"] = len(all_templates)
            results["all_templates"] = all_templates
    
    return results

def check_a2a_implementation() -> Dict[str, Any]:
    """检查A2A实现"""
    print("🔍 检查A2A实现...")
    
    a2a_file = "src/owl_requirements/core/a2a_communication.py"
    results = {
        "a2a_file_exists": os.path.exists(a2a_file),
        "classes_found": [],
        "missing_classes": []
    }
    
    expected_classes = [
        "A2AMessageType",
        "A2AMessage", 
        "RequirementsClarificationWorkflow",
        "QualityFeedbackWorkflow",
        "A2ACoordinator",
        "A2AAgentMixin"
    ]
    
    if results["a2a_file_exists"]:
        try:
            with open(a2a_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for class_name in expected_classes:
                if f"class {class_name}" in content:
                    results["classes_found"].append(class_name)
                else:
                    results["missing_classes"].append(class_name)
                    
        except Exception as e:
            results["error"] = str(e)
    
    return results

def check_system_imports() -> Dict[str, Any]:
    """检查系统导入"""
    print("🔍 检查系统导入...")
    
    results = {
        "import_tests": [],
        "successful_imports": 0,
        "failed_imports": 0
    }
    
    # 测试关键模块的导入
    test_imports = [
        "src.owl_requirements.core.config",
        "src.owl_requirements.core.coordinator", 
        "src.owl_requirements.agents.requirements_extractor",
        "src.owl_requirements.agents.requirements_analyzer",
        "src.owl_requirements.agents.quality_checker",
        "src.owl_requirements.agents.documentation_generator",
        "src.owl_requirements.services.llm_manager",
        "src.owl_requirements.core.a2a_communication"
    ]
    
    for module_name in test_imports:
        try:
            # 尝试导入模块
            module = importlib.import_module(module_name)
            results["import_tests"].append({
                "module": module_name,
                "status": "success",
                "error": None
            })
            results["successful_imports"] += 1
        except Exception as e:
            results["import_tests"].append({
                "module": module_name,
                "status": "failed", 
                "error": str(e)
            })
            results["failed_imports"] += 1
    
    return results

def check_linter_errors() -> Dict[str, Any]:
    """检查linter错误"""
    print("🔍 检查linter错误...")
    
    results = {
        "total_errors": 0,
        "error_types": {},
        "critical_errors": 0,
        "status": "unknown"
    }
    
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "src/", "--count", "--statistics", "--max-line-length=88"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            results["status"] = "clean"
            results["total_errors"] = 0
        else:
            # 解析错误输出
            lines = result.stdout.strip().split('\n')
            error_lines = [line for line in lines if ':' in line and 'src/' in line]
            results["total_errors"] = len(error_lines)
            
            # 统计错误类型
            for line in lines:
                if line.strip() and not ':' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        count = parts[0]
                        error_type = ' '.join(parts[1:])
                        try:
                            results["error_types"][error_type] = int(count)
                        except ValueError:
                            continue
            
            # 检查关键错误
            critical_patterns = ['E999', 'F821', 'E902']
            for error_type, count in results["error_types"].items():
                if any(pattern in error_type for pattern in critical_patterns):
                    results["critical_errors"] += count
            
            results["status"] = "has_errors"
            
    except Exception as e:
        results["error"] = str(e)
        results["status"] = "check_failed"
    
    return results

def check_file_structure() -> Dict[str, Any]:
    """检查文件结构"""
    print("🔍 检查文件结构...")
    
    results = {
        "core_files": [],
        "missing_files": [],
        "duplicate_files": []
    }
    
    expected_files = [
        "src/owl_requirements/__init__.py",
        "src/owl_requirements/core/__init__.py",
        "src/owl_requirements/core/config.py",
        "src/owl_requirements/core/coordinator.py",
        "src/owl_requirements/core/a2a_communication.py",
        "src/owl_requirements/agents/__init__.py",
        "src/owl_requirements/services/__init__.py",
        "src/owl_requirements/services/llm_manager.py",
        "src/owl_requirements/utils/__init__.py",
        "templates/prompts/requirements_extraction.json",
        "main.py"
    ]
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            results["core_files"].append(file_path)
        else:
            results["missing_files"].append(file_path)
    
    # 检查是否还有重复的LLM文件
    llm_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if 'llm' in file.lower() and file.endswith('.py'):
                llm_files.append(os.path.join(root, file))
    
    results["llm_files"] = llm_files
    
    return results

def run_quick_functionality_test() -> Dict[str, Any]:
    """运行快速功能测试"""
    print("🔍 运行快速功能测试...")
    
    results = {
        "once_mode": {"status": "unknown", "error": None},
        "cli_help": {"status": "unknown", "error": None},
        "web_import": {"status": "unknown", "error": None}
    }
    
    # 测试once模式
    try:
        result = subprocess.run(
            ["python", "main.py", "-m", "once", "-t", "测试需求"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "需求分析流程完成" in result.stdout:
            results["once_mode"]["status"] = "working"
        elif result.returncode == 0:
            results["once_mode"]["status"] = "partial"
        else:
            results["once_mode"]["status"] = "failed"
            results["once_mode"]["error"] = result.stderr
            
    except subprocess.TimeoutExpired:
        results["once_mode"]["status"] = "timeout"
    except Exception as e:
        results["once_mode"]["status"] = "error"
        results["once_mode"]["error"] = str(e)
    
    # 测试CLI帮助
    try:
        result = subprocess.run(
            ["python", "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "usage:" in result.stdout:
            results["cli_help"]["status"] = "working"
        else:
            results["cli_help"]["status"] = "failed"
            results["cli_help"]["error"] = result.stderr
            
    except Exception as e:
        results["cli_help"]["status"] = "error"
        results["cli_help"]["error"] = str(e)
    
    # 测试Web模块导入
    try:
        import owl_requirements.web.app
        results["web_import"]["status"] = "working"
    except Exception as e:
        results["web_import"]["status"] = "failed"
        results["web_import"]["error"] = str(e)
    
    return results

def generate_report(results: Dict[str, Any]) -> None:
    """生成验证报告"""
    print("\n" + "="*60)
    print("🦉 OWL需求分析系统 - 验证报告")
    print("="*60)
    
    # 模板一致性
    template_results = results["templates"]
    print(f"\n📋 模板系统:")
    if template_results["template_dir_exists"]:
        print(f"  ✅ 模板目录存在")
        print(f"  📁 找到模板: {len(template_results['found_templates'])}")
        for template in template_results["found_templates"]:
            print(f"    - {template}")
        if template_results["missing_templates"]:
            print(f"  ⚠️ 缺失模板: {template_results['missing_templates']}")
    else:
        print(f"  ❌ 模板目录不存在")
    
    # A2A实现
    a2a_results = results["a2a"]
    print(f"\n🤖 A2A通信框架:")
    if a2a_results["a2a_file_exists"]:
        print(f"  ✅ A2A文件存在")
        print(f"  🔧 找到类: {len(a2a_results['classes_found'])}")
        for class_name in a2a_results["classes_found"]:
            print(f"    - {class_name}")
        if a2a_results["missing_classes"]:
            print(f"  ⚠️ 缺失类: {a2a_results['missing_classes']}")
    else:
        print(f"  ❌ A2A文件不存在")
    
    # 系统导入
    import_results = results["imports"]
    print(f"\n📦 系统导入:")
    print(f"  ✅ 成功导入: {import_results['successful_imports']}")
    print(f"  ❌ 失败导入: {import_results['failed_imports']}")
    
    if import_results["failed_imports"] > 0:
        print("  失败的导入:")
        for test in import_results["import_tests"]:
            if test["status"] == "failed":
                print(f"    - {test['module']}: {test['error']}")
    
    # Linter错误
    linter_results = results["linter"]
    print(f"\n🔍 代码质量:")
    print(f"  状态: {linter_results['status']}")
    print(f"  总错误数: {linter_results['total_errors']}")
    print(f"  关键错误: {linter_results['critical_errors']}")
    
    if linter_results["error_types"]:
        print("  错误类型:")
        for error_type, count in sorted(linter_results["error_types"].items()):
            print(f"    - {error_type}: {count}")
    
    # 文件结构
    structure_results = results["structure"]
    print(f"\n📁 文件结构:")
    print(f"  ✅ 核心文件: {len(structure_results['core_files'])}")
    print(f"  ❌ 缺失文件: {len(structure_results['missing_files'])}")
    print(f"  🔧 LLM文件: {len(structure_results['llm_files'])}")
    
    if structure_results["missing_files"]:
        print("  缺失的文件:")
        for file_path in structure_results["missing_files"]:
            print(f"    - {file_path}")
    
    # 功能测试
    func_results = results["functionality"]
    print(f"\n⚡ 功能测试:")
    print(f"  Once模式: {func_results['once_mode']['status']}")
    print(f"  CLI帮助: {func_results['cli_help']['status']}")
    print(f"  Web导入: {func_results['web_import']['status']}")
    
    # 总体评估
    print(f"\n🎯 总体评估:")
    
    score = 0
    max_score = 6
    
    if template_results["template_dir_exists"] and len(template_results["found_templates"]) >= 3:
        score += 1
        print("  ✅ 模板系统正常")
    
    if a2a_results["a2a_file_exists"] and len(a2a_results["classes_found"]) >= 5:
        score += 1
        print("  ✅ A2A框架完整")
    
    if import_results["successful_imports"] >= import_results["failed_imports"]:
        score += 1
        print("  ✅ 导入基本正常")
    
    if linter_results["total_errors"] < 100:
        score += 1
        print("  ✅ 代码质量可接受")
    
    if len(structure_results["missing_files"]) < 3:
        score += 1
        print("  ✅ 文件结构完整")
    
    if func_results["once_mode"]["status"] in ["working", "partial"]:
        score += 1
        print("  ✅ 基本功能可用")
    
    print(f"\n📊 系统健康度: {score}/{max_score} ({score/max_score*100:.1f}%)")
    
    if score >= 5:
        print("🎉 系统状态良好！")
    elif score >= 3:
        print("⚠️ 系统基本可用，但需要改进")
    else:
        print("❌ 系统存在严重问题，需要修复")

def main():
    """主函数"""
    print("🚀 开始系统验证...")
    
    # 添加src目录到Python路径
    sys.path.insert(0, os.path.abspath('src'))
    
    results = {}
    
    # 运行各项检查
    results["templates"] = check_template_consistency()
    results["a2a"] = check_a2a_implementation()
    results["imports"] = check_system_imports()
    results["linter"] = check_linter_errors()
    results["structure"] = check_file_structure()
    results["functionality"] = run_quick_functionality_test()
    
    # 生成报告
    generate_report(results)

if __name__ == "__main__":
    main()
