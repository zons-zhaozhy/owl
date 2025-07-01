"""
需求分析助手启动脚本
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.owl_requirements.core.settings import Settings
from src.owl_requirements.core.logging import setup_logging, get_logger

async def main():
    """主函数"""
    try:
        # 初始化设置
        settings = Settings()
        
        # 初始化日志记录器
        setup_logging()
        logger = get_logger("owl.run")
        logger.info("启动需求分析助手")
        
        # 创建需求分析助手实例
        assistant = RequirementsAnalysisAssistant(settings)
        
        # 获取用户输入
        print("\n请输入您的需求描述:")
        user_input = input().strip()
        
        # 处理用户输入
        results = await assistant.analyze_requirements(user_input)
        
        # 保存结果
        if results["status"] == "success":
            # 打印摘要
            print("\n=== 处理结果摘要 ===")
            print(f"- 原始需求数量: {results['summary']['total_requirements']}")
            print(f"- 优化后需求数量: {results['summary']['optimized_count']}")
            print(f"- 是否有变更: {'是' if results['summary']['has_changes'] else '否'}")
            print(f"- 质量评分: {results['summary']['quality_score']:.2f}")
            print(f"- 发现问题数: {results['summary']['identified_issues']}")
            print(f"- 详细结果已保存到: {os.path.join(str(assistant.output_dir), 'analysis_results.json')}")
            
            # 如果有问题，打印问题列表
            if results['summary']['identified_issues'] > 0:
                print("\n=== 发现的问题 ===")
                for issue in results['validation_results']['issues']:
                    print(f"- {issue['description']}")
                    if issue.get('suggestion'):
                        print(f"  建议: {issue['suggestion']}")
        else:
            print(f"\n处理失败: {results['error']}")
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 