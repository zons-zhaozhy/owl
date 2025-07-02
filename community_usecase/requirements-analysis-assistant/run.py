"""
需求分析助手启动脚本
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from owl_requirements.core.config import SystemConfig, AgentRole
from owl_requirements.core.logging import setup_logging, get_logger
from owl_requirements.core.coordinator import AgentCoordinator
from owl_requirements.services.llm_factory import create_llm_service
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.agents.documentation_generator import DocumentationGenerator

async def main():
    """主函数"""
    try:
        # 初始化设置
        settings = SystemConfig.from_yaml("config.yaml")
        
        # 初始化日志记录器
        setup_logging(settings.log_level, settings.log_file)
        logger = get_logger("owl.run")
        logger.info("启动需求分析助手")
        
        # 创建LLM服务
        llm_service = create_llm_service({
            "provider": settings.provider,
            "model": settings.model,
            "api_key": settings.api_key,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        })
        
        # 创建智能体
        extractor = RequirementsExtractor(llm_service, {
            "name": "需求提取智能体",
            "prompt_template": "templates/extractor.txt",
            "max_retries": 3
        })
        analyzer = RequirementsAnalyzer(llm_service, {
            "name": "需求分析智能体",
            "prompt_template": "templates/analyzer.txt",
            "max_retries": 3
        })
        checker = QualityChecker(llm_service, {
            "name": "质量检查智能体",
            "prompt_template": "templates/checker.txt",
            "max_retries": 3
        })
        generator = DocumentationGenerator(llm_service, {
            "name": "文档生成智能体",
            "prompt_template": "templates/generator.txt",
            "max_retries": 3
        })
        
        # 创建协调器
        coordinator = AgentCoordinator(
            extractor=extractor,
            analyzer=analyzer,
            checker=checker,
            generator=generator
        )
        
        # 获取用户输入
        print("\n请输入您的需求描述:")
        user_input = input().strip()
        
        # 处理用户输入
        results = await coordinator.analyze(user_input)
        
        # 保存结果
        if results.get("metrics", {}).get("workflow", {}).get("successful", False):
            # 打印摘要
            print("\n=== 处理结果摘要 ===")
            print(f"- 需求数量: {len(results['requirements'].get('requirements', []))}")
            print(f"- 分析完成: {'是' if results['analysis'] else '否'}")
            print(f"- 质量评分: {results['quality_check']['summary']['overall_quality']}")
            print(f"- 文档生成: {'是' if results['documentation'] else '否'}")
            print(f"- 处理时间: {results['metrics']['workflow']['processing_time']:.2f}秒")
            
            # 如果有问题，打印问题列表
            if results['quality_check']['issues']:
                print("\n=== 发现的问题 ===")
                for issue in results['quality_check']['issues']:
                    print(f"- {issue['description']}")
                    if issue.get('recommendation'):
                        print(f"  建议: {issue['recommendation']}")
        else:
            print(f"\n处理失败: {results.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 