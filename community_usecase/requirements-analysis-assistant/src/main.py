"""Main entry point for the requirements analysis assistant."""

import os
import sys
import asyncio
import typer
from pathlib import Path
from typing import Optional
from loguru import logger

from owl_requirements.core.config import load_config
from owl_requirements.services.llm import create_llm_service
from owl_requirements.agents.requirements_extractor import RequirementsExtractor
from owl_requirements.agents.requirements_analyzer import RequirementsAnalyzer
from owl_requirements.agents.quality_checker import QualityChecker
from owl_requirements.agents.documentation_generator import DocumentationGenerator

# 创建CLI应用
app = typer.Typer()

@app.command()
def analyze(
    input_text: str = typer.Option(..., "--text", "-t", help="需求文本"),
    config_path: str = typer.Option("config/system.yaml", "--config", "-c", help="配置文件路径"),
    output_path: str = typer.Option("output", "--output", "-o", help="输出目录路径"),
    mode: str = typer.Option("once", "--mode", "-m", help="运行模式: once/cli/web")
):
    """分析需求并生成文档。"""
    try:
        # 加载配置
        config = load_config(config_path)
        logger.info(f"已加载配置: {config_path}")
        
        # 创建输出目录
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建LLM服务
        llm_service = create_llm_service(config)
        
        # 创建智能体
        extractor = RequirementsExtractor(config, llm_service)
        analyzer = RequirementsAnalyzer(config, llm_service)
        checker = QualityChecker(config, llm_service)
        doc_generator = DocumentationGenerator(config, llm_service)
        
        # 运行分析流程
        asyncio.run(run_analysis(
            input_text=input_text,
            extractor=extractor,
            analyzer=analyzer,
            checker=checker,
            doc_generator=doc_generator,
            output_dir=output_dir
        ))
        
    except Exception as e:
        logger.error(f"分析过程出错: {e}")
        raise typer.Exit(1)

async def run_analysis(
    input_text: str,
    extractor: RequirementsExtractor,
    analyzer: RequirementsAnalyzer,
    checker: QualityChecker,
    doc_generator: DocumentationGenerator,
    output_dir: Path
):
    """运行需求分析流程。"""
    try:
        # 1. 提取需求
        logger.info("开始提取需求...")
        requirements = await extractor.process({"text": input_text})
        
        # 2. 分析需求
        logger.info("开始分析需求...")
        analysis = await analyzer.process(requirements)
        
        # 3. 质量检查
        logger.info("开始质量检查...")
        quality_check = await checker.process({
            "requirements": requirements,
            "analysis": analysis
        })
        
        # 4. 生成文档
        logger.info("开始生成文档...")
        documentation = await doc_generator.process({
            "requirements": requirements,
            "analysis": analysis,
            "quality_check": quality_check
        })
        
        # 5. 保存结果
        save_results(
            output_dir=output_dir,
            requirements=requirements,
            analysis=analysis,
            quality_check=quality_check,
            documentation=documentation
        )
        
        logger.info(f"分析完成，结果已保存到: {output_dir}")
        
    except Exception as e:
        logger.error(f"分析流程出错: {e}")
        raise

def save_results(
    output_dir: Path,
    requirements: dict,
    analysis: dict,
    quality_check: dict,
    documentation: dict
):
    """保存分析结果。"""
    try:
        # 保存需求提取结果
        requirements_file = output_dir / "requirements.md"
        with open(requirements_file, "w", encoding="utf-8") as f:
            f.write("# 需求提取结果\n\n")
            f.write("## 功能需求\n")
            for req in requirements.get("functional_requirements", []):
                f.write(f"- {req}\n")
            f.write("\n## 非功能需求\n")
            for req in requirements.get("non_functional_requirements", []):
                f.write(f"- {req}\n")
            f.write("\n## 约束条件\n")
            for constraint in requirements.get("constraints", []):
                f.write(f"- {constraint}\n")
        
        # 保存需求分析结果
        analysis_file = output_dir / "analysis.md"
        with open(analysis_file, "w", encoding="utf-8") as f:
            f.write("# 需求分析结果\n\n")
            f.write("## 技术可行性\n")
            for item in analysis.get("technical_feasibility", []):
                f.write(f"- {item}\n")
            f.write("\n## 资源需求\n")
            for item in analysis.get("resource_requirements", []):
                f.write(f"- {item}\n")
            f.write("\n## 风险分析\n")
            for item in analysis.get("risk_analysis", []):
                f.write(f"- {item}\n")
        
        # 保存质量检查结果
        quality_file = output_dir / "quality_check.md"
        with open(quality_file, "w", encoding="utf-8") as f:
            f.write("# 质量检查结果\n\n")
            f.write("## 发现的问题\n")
            for issue in quality_check.get("issues", []):
                f.write(f"- {issue}\n")
            f.write("\n## 改进建议\n")
            for rec in quality_check.get("recommendations", []):
                f.write(f"- {rec}\n")
        
        # 保存最终文档
        doc_file = output_dir / "documentation.md"
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write("# 需求文档\n\n")
            
            f.write("## 项目概述\n")
            for item in documentation.get("project_overview", []):
                f.write(f"{item}\n")
            
            f.write("\n## 需求清单\n")
            for item in documentation.get("requirements_list", []):
                f.write(f"{item}\n")
            
            f.write("\n## 技术方案\n")
            for item in documentation.get("technical_solution", []):
                f.write(f"{item}\n")
            
            f.write("\n## 实现计划\n")
            for item in documentation.get("implementation_plan", []):
                f.write(f"{item}\n")
            
            f.write("\n## 风险管理\n")
            for item in documentation.get("risk_management", []):
                f.write(f"{item}\n")
        
    except Exception as e:
        logger.error(f"保存结果时出错: {e}")
        raise

if __name__ == "__main__":
    app() 