#!/usr/bin/env python3
"""
OWL Requirements Analysis Assistant
需求分析助手主程序
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import argparse
import asyncio
import logging
import json
from typing import Optional, Dict, Any

from src.owl_requirements.services.llm_manager import LLMManager
from src.owl_requirements.agents.requirements_extractor import RequirementsExtractor
from src.owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from src.owl_requirements.agents.quality_checker import QualityChecker
from src.owl_requirements.agents.documentation_generator import DocumentationGenerator
from src.owl_requirements.core.logging import setup_logging
from src.owl_requirements.core.coordinator import AgentCoordinator
from src.owl_requirements.core.config import SystemConfig

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

class RequirementsAnalysisSystem:
    """需求分析系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.llm_manager = LLMManager()
        self.extractor = RequirementsExtractor()
        self.analyzer = RequirementsAnalyzer()
        self.quality_checker = QualityChecker()
        self.doc_generator = DocumentationGenerator()
        
        logger.info("需求分析系统初始化完成")
    
    async def analyze_requirements_once(self, input_text: str, provider: str = None) -> dict:
        """单次需求分析"""
        try:
            if provider:
                # 设置LLM提供商
                self.llm_manager.set_provider(provider)
                logger.info(f"使用LLM提供商: {provider}")
            
            logger.info("开始需求分析流程")
            
            # 1. 需求提取
            logger.info("步骤1: 提取需求")
            extraction_result = await self.extractor.process({
                "input_text": input_text
            })
            
            if extraction_result["status"] != "success":
                return extraction_result
            
            requirements = extraction_result["requirements"]
            
            # 2. 需求分析
            logger.info("步骤2: 分析需求")
            analysis_result = await self.analyzer.process({
                "requirements": requirements
            })
            
            # 3. 质量检查
            logger.info("步骤3: 质量检查")
            quality_result = await self.quality_checker.process({
                "requirements": requirements,
                "analysis": analysis_result.get("analysis", {})
            })
            
            # 4. 文档生成
            logger.info("步骤4: 生成文档")
            doc_result = await self.doc_generator.process({
                "requirements": requirements,
                "analysis": analysis_result.get("analysis", {}),
                "quality_report": quality_result.get("quality_report", {})
            })
            
            # 整合结果
            final_result = {
                "status": "success",
                "input_text": input_text,
                "extraction": extraction_result,
                "analysis": analysis_result,
                "quality": quality_result,
                "documentation": doc_result,
                "provider_used": self.llm_manager.current_provider,
                "available_providers": self.llm_manager.get_available_providers()
            }
            
            logger.info("需求分析流程完成")
            return final_result
            
        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "input_text": input_text
            }
    
    async def close(self):
        """关闭系统资源"""
        await self.llm_manager.close()
        await self.extractor.close()
        await self.analyzer.close()
        await self.quality_checker.close()
        await self.doc_generator.close()

async def run_once_mode(args):
    """单次执行模式"""
    print("🦉 OWL需求分析助手 - 单次模式")
    print("=" * 50)
    
    system = RequirementsAnalysisSystem()
    
    try:
        # 获取输入文本
        input_text = args.text
        if not input_text:
            input_text = input("请输入需求描述: ")
        
        if not input_text.strip():
            print("❌ 错误: 输入文本不能为空")
            return
        
        print(f"📝 输入文本: {input_text[:100]}...")
        print(f"🤖 LLM提供商: {args.provider or '默认'}")
        print()
        
        # 执行分析
        result = await system.analyze_requirements_once(input_text, args.provider)
        
        # 输出结果
        if result["status"] == "success":
            print("✅ 分析完成!")
            print()
            
            # 提取结果
            extraction = result["extraction"]["requirements"]
            print(f"📋 功能需求: {len(extraction.get('functional_requirements', []))} 个")
            print(f"⚙️ 非功能需求: {len(extraction.get('non_functional_requirements', []))} 个")
            print(f"🚫 约束条件: {len(extraction.get('constraints', []))} 个")
            print()
            
            # 保存结果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"💾 结果已保存到: {args.output}")
            
            # 详细输出
            if args.verbose:
                print("\n📊 详细结果:")
                print("-" * 30)
                
                # 功能需求
                if extraction.get('functional_requirements'):
                    print("\n功能需求:")
                    for req in extraction['functional_requirements']:
                        print(f"  • {req.get('description', '')}")
                
                # 非功能需求
                if extraction.get('non_functional_requirements'):
                    print("\n非功能需求:")
                    for req in extraction['non_functional_requirements']:
                        print(f"  • {req.get('description', '')}")
                
                # 约束条件
                if extraction.get('constraints'):
                    print("\n约束条件:")
                    for constraint in extraction['constraints']:
                        print(f"  • {constraint.get('description', '')}")
        else:
            print(f"❌ 分析失败: {result.get('error', '未知错误')}")
    
    finally:
        await system.close()

def run_cli_mode(args):
    """CLI交互模式"""
    print("🦉 OWL需求分析助手 - CLI模式")
    print("=" * 50)
    print("输入 'help' 查看帮助，输入 'quit' 退出")
    print()
    
    # 这是一个测试注释，用于强制更新文件
    # 导入CLI应用和相关依赖
    from src.owl_requirements.cli.app import create_cli_app
    from src.owl_requirements.core.coordinator import AgentCoordinator
    from src.owl_requirements.core.config import SystemConfig
    from src.owl_requirements.services.llm_manager import LLMManager
    from src.owl_requirements.agents.requirements_extractor import RequirementsExtractor
    from src.owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
    from src.owl_requirements.agents.quality_checker import QualityChecker
    from src.owl_requirements.agents.documentation_generator import DocumentationGenerator

    try:
        # 初始化配置和LLM管理器
        config = SystemConfig()
        llm_manager = LLMManager()

        # 实例化智能体，只传递配置字典
        extractor = RequirementsExtractor()
        analyzer = RequirementsAnalyzer()
        checker = QualityChecker()
        generator = DocumentationGenerator()

        # 初始化协调器，只传递智能体实例
        coordinator = AgentCoordinator(extractor, analyzer, checker, generator)

        # 创建CLI应用
        cli_app_runnable = create_cli_app(coordinator, config)
        
        # 运行CLI应用
        asyncio.run(cli_app_runnable())

    except ImportError:
        print("❌ 错误: 缺少typer依赖，请运行: pip install typer")
        logger.error("缺少typer依赖")
    except Exception as e:
        print(f"❌ CLI启动失败: {str(e)}")
        logger.error(f"CLI启动失败: {e}")

def run_web_mode(args):
    """Web服务模式"""
    print("🦉 OWL需求分析助手 - Web模式")
    print("=" * 50)
    
    # 导入Web应用
    from src.owl_requirements.web.app import create_app
    from src.owl_requirements.core.config import SystemConfig
    from src.owl_requirements.services.llm_manager import LLMManager
    
    try:
        import uvicorn
        
        # 初始化配置和LLM管理器
        config = SystemConfig()
        llm_manager = LLMManager()
        
        # 创建应用
        app = create_app(config, llm_manager)
        
        # 配置参数
        host = args.host or "127.0.0.1"
        port = args.port or 8080
        
        print(f"🌐 启动Web服务: http://{host}:{port}")
        print("按 Ctrl+C 停止服务")
        print()
        
        # 启动服务
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=args.reload,
            log_level="info"
        )
        
    except ImportError:
        print("❌ 错误: 缺少Web依赖，请运行: pip install fastapi uvicorn")
    except Exception as e:
        print(f"❌ Web服务启动失败: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OWL需求分析助手 - 基于多智能体的需求分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # Web模式（默认）
  python main.py
  
  # CLI交互模式
  python main.py --mode cli
  
  # 单次执行模式
  python main.py --mode once --text "开发一个在线购物系统"
  
  # 指定LLM提供商
  python main.py --mode once --text "需求描述" --provider deepseek
  
  # Web模式自定义配置
  python main.py --mode web --host 0.0.0.0 --port 8000
        """
    )
    
    # 基本参数
    parser.add_argument(
        "--mode", "-m",
        choices=["web", "cli", "once"],
        default="web",
        help="运行模式 (默认: web)"
    )
    
    parser.add_argument(
        "--provider", "-p",
        choices=["deepseek", "openai", "ollama", "anthropic"],
        help="LLM提供商"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    # Once模式参数
    parser.add_argument(
        "--text", "-t",
        help="需求描述文本（once模式）"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（once模式）"
    )
    
    # Web模式参数
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Web服务器主机 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web服务器端口 (默认: 8080)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用热重载（开发模式）"
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(level=args.log_level)
    
    # 显示系统信息
    print("🦉 OWL需求分析助手")
    print(f"📁 项目目录: {current_dir}")
    print(f"🔧 运行模式: {args.mode}")
    
    # 检查LLM提供商
    try:
        llm_manager = LLMManager()
        available_providers = llm_manager.get_available_providers()
        print(f"🤖 可用LLM: {', '.join(available_providers)}")
        
        if args.provider:
            if args.provider in available_providers:
                llm_manager.set_provider(args.provider)
                print(f"✅ 使用LLM: {args.provider}")
            else:
                print(f"⚠️ 警告: LLM提供商 {args.provider} 不可用，使用默认")
    except Exception as e:
        print(f"⚠️ 警告: LLM初始化失败: {str(e)}")
    
    print()
    
    # 根据模式运行
    try:
        if args.mode == "once":
            asyncio.run(run_once_mode(args))
        elif args.mode == "cli":
            run_cli_mode(args)
        elif args.mode == "web":
            run_web_mode(args)
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 运行错误: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 