#!/usr/bin/env python3
"""
测试运行脚本
提供多种测试执行选项和报告生成功能
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Optional

def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """运行命令并返回退出码"""
    print(f"执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=False,
            text=True
        )
        return result.returncode
    except Exception as e:
        print(f"命令执行失败: {e}")
        return 1

def run_unit_tests(verbose: bool = False) -> int:
    """运行单元测试"""
    print("🧪 运行单元测试...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def run_integration_tests(verbose: bool = False) -> int:
    """运行集成测试"""
    print("🔗 运行集成测试...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def run_performance_tests(verbose: bool = False) -> int:
    """运行性能测试"""
    print("⚡ 运行性能测试...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=0"
    ])
    
    return run_command(cmd)

def run_all_tests(verbose: bool = False, coverage: bool = False) -> int:
    """运行所有测试"""
    print("🚀 运行所有测试...")
    
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def run_specific_test(test_path: str, verbose: bool = False) -> int:
    """运行特定测试"""
    print(f"🎯 运行特定测试: {test_path}")
    
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes"
    ])
    
    return run_command(cmd)

def run_fast_tests(verbose: bool = False) -> int:
    """运行快速测试（排除慢速测试）"""
    print("⚡ 运行快速测试...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "not slow"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def run_external_tests(verbose: bool = False) -> int:
    """运行需要外部服务的测试"""
    print("🌐 运行外部服务测试...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-m", "external"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def run_parallel_tests(workers: int = 4, verbose: bool = False) -> int:
    """并行运行测试"""
    print(f"🔄 并行运行测试 (workers: {workers})...")
    
    cmd = ["python", "-m", "pytest", "tests/", "-n", str(workers)]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--durations=10"
    ])
    
    return run_command(cmd)

def generate_test_report(output_dir: str = "test_reports") -> int:
    """生成测试报告"""
    print("📊 生成测试报告...")
    
    # 创建报告目录
    report_dir = Path(output_dir)
    report_dir.mkdir(exist_ok=True)
    
    # 生成HTML报告
    cmd = [
        "python", "-m", "pytest", "tests/",
        "--html", str(report_dir / "report.html"),
        "--self-contained-html",
        "--cov=src",
        "--cov-report=html:" + str(report_dir / "coverage"),
        "--cov-report=xml:" + str(report_dir / "coverage.xml"),
        "--junit-xml=" + str(report_dir / "junit.xml")
    ]
    
    return run_command(cmd)

def check_test_dependencies() -> bool:
    """检查测试依赖"""
    print("🔍 检查测试依赖...")
    
    required_packages = [
        "pytest",
        "pytest-cov",
        "pytest-html",
        "pytest-xdist",
        "pytest-mock"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "pytest-xdist":
                __import__("xdist")
            elif package == "pytest-html":
                __import__("pytest_html")
            elif package == "pytest-mock":
                __import__("pytest_mock")
            elif package == "pytest-cov":
                __import__("pytest_cov")
            else:
                __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有测试依赖已安装")
    return True

def clean_test_artifacts():
    """清理测试产物"""
    print("🧹 清理测试产物...")
    
    patterns = [
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        ".coverage",
        "htmlcov",
        "test_reports",
        ".tox"
    ]
    
    for pattern in patterns:
        if pattern.startswith("."):
            # 删除目录
            for path in Path(".").rglob(pattern):
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"删除目录: {path}")
        else:
            # 删除文件
            for path in Path(".").rglob(pattern):
                if path.is_file():
                    path.unlink()
                    print(f"删除文件: {path}")

def setup_test_environment():
    """设置测试环境"""
    print("⚙️ 设置测试环境...")
    
    # 设置环境变量
    os.environ["OWL_ENV"] = "test"
    os.environ["OWL_LOG_LEVEL"] = "DEBUG"
    os.environ["PYTHONPATH"] = str(Path.cwd())
    
    # 创建必要的目录
    test_dirs = ["logs", "cache", "temp"]
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("✅ 测试环境设置完成")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="需求分析助手测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_tests.py --all                    # 运行所有测试
  python run_tests.py --unit --verbose         # 运行单元测试（详细输出）
  python run_tests.py --integration            # 运行集成测试
  python run_tests.py --performance            # 运行性能测试
  python run_tests.py --test tests/test_cli.py # 运行特定测试文件
  python run_tests.py --fast --parallel 8     # 并行运行快速测试
  python run_tests.py --report                 # 生成测试报告
  python run_tests.py --clean                  # 清理测试产物
        """
    )
    
    # 测试类型选项
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--all", action="store_true", help="运行所有测试")
    test_group.add_argument("--unit", action="store_true", help="运行单元测试")
    test_group.add_argument("--integration", action="store_true", help="运行集成测试")
    test_group.add_argument("--performance", action="store_true", help="运行性能测试")
    test_group.add_argument("--fast", action="store_true", help="运行快速测试")
    test_group.add_argument("--external", action="store_true", help="运行外部服务测试")
    test_group.add_argument("--test", type=str, help="运行特定测试文件")
    
    # 运行选项
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--parallel", "-p", type=int, default=4, help="并行运行测试的进程数")
    
    # 工具选项
    parser.add_argument("--report", action="store_true", help="生成测试报告")
    parser.add_argument("--clean", action="store_true", help="清理测试产物")
    parser.add_argument("--check-deps", action="store_true", help="检查测试依赖")
    parser.add_argument("--setup", action="store_true", help="设置测试环境")
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # 处理工具选项
    if args.clean:
        clean_test_artifacts()
        return 0
    
    if args.check_deps:
        return 0 if check_test_dependencies() else 1
    
    if args.setup:
        setup_test_environment()
        return 0
    
    if args.report:
        return generate_test_report()
    
    # 检查依赖
    if not check_test_dependencies():
        return 1
    
    # 设置测试环境
    setup_test_environment()
    
    # 记录开始时间
    start_time = time.time()
    
    # 运行测试
    exit_code = 0
    
    try:
        if args.all:
            exit_code = run_all_tests(args.verbose, args.coverage)
        elif args.unit:
            exit_code = run_unit_tests(args.verbose)
        elif args.integration:
            exit_code = run_integration_tests(args.verbose)
        elif args.performance:
            exit_code = run_performance_tests(args.verbose)
        elif args.fast:
            if args.parallel > 1:
                exit_code = run_parallel_tests(args.parallel, args.verbose)
            else:
                exit_code = run_fast_tests(args.verbose)
        elif args.external:
            exit_code = run_external_tests(args.verbose)
        elif args.test:
            exit_code = run_specific_test(args.test, args.verbose)
        else:
            # 默认运行快速测试
            exit_code = run_fast_tests(args.verbose)
            
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
        exit_code = 130
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        exit_code = 1
    
    # 计算运行时间
    end_time = time.time()
    duration = end_time - start_time
    
    # 输出结果
    if exit_code == 0:
        print(f"\n✅ 测试完成 (耗时: {duration:.2f}秒)")
    else:
        print(f"\n❌ 测试失败 (耗时: {duration:.2f}秒)")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 