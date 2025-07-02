"""Documentation generator agent implementation."""

import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from loguru import logger

from ..services.llm import LLMService
from ..core.models import QualityReport
from ..core.config import SystemConfig
from ..core.base import BaseAgent
from ..utils.enums import AgentRole

class DocumentationGenerator(BaseAgent):
    """Documentation generator agent implementation."""
    
    def __init__(self, llm_service: LLMService, config: SystemConfig):
        """Initialize documentation generator.
        
        Args:
            llm_service: LLM service instance
            config: Agent configuration
        """
        super().__init__(config.get_agent_config(AgentRole.DOCUMENT_GENERATOR).to_dict())
        self.llm_service = llm_service
        self.system_config = config
        self.max_retries = self.system_config.max_retries
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        template_path = Path(self.system_config.templates_dir) / "documentation_generator.json"
        
        current_file_dir = Path(__file__).parent
        project_root = current_file_dir.parent.parent.parent
        absolute_template_path = project_root / template_path

        if not absolute_template_path.exists():
            # 使用默认模板
            return """请根据以下信息生成完整的需求文档。

需求:
{requirements}

分析:
{analysis}

质量检查:
{quality_check}

{context_info}

请以JSON格式返回文档，包含以下字段:
1. project_overview: 项目概述
2. executive_summary: 执行摘要
3. requirements_specification: 需求规格
4. analysis_results: 分析结果
5. quality_assessment: 质量评估
6. implementation_plan: 实施计划

示例输出:
{
    "documentation": {
        "project_overview": {
            "title": "项目名称",
            "version": "1.0.0",
            "date": "2024-03-21",
            "status": "草稿",
            "authors": ["需求分析师"],
            "reviewers": ["质量检查员"],
            "approvers": ["项目经理"]
        },
        "executive_summary": {
            "background": "项目背景描述...",
            "objectives": ["目标1", "目标2"],
            "scope": {
                "in_scope": ["范围1", "范围2"],
                "out_of_scope": ["排除1", "排除2"]
            },
            "stakeholders": ["干系人1", "干系人2"]
        }
    }
}"""
            
        with open(absolute_template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["template"]
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data.

        Args:
            input_data: Input data to process

        Returns:
            Processing results
        """
        requirements = input_data.get("requirements")
        analysis = input_data.get("analysis")
        quality_check = input_data.get("quality_check")
        context = input_data.get("context")

        if not all([requirements, analysis, quality_check]):
            raise ValueError("Missing requirements, analysis, or quality_check data for documentation generation.")

        return await self.generate(requirements, analysis, quality_check, context)

    async def generate(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any],
        quality_check: QualityReport,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate documentation from requirements, analysis and quality check.
        
        Args:
            requirements: Requirements data
            analysis: Analysis results
            quality_check: Quality check results
            context: Optional context information
            
        Returns:
            Generated documentation
            
        Raises:
            ValueError: If generation fails
        """
        try:
            # Format prompt
            quality_check_dict = quality_check.model_dump()
            prompt = await self._format_prompt(requirements, analysis, quality_check_dict, context)
            
            # Generate documentation
            response = await self.llm_service.generate(prompt)
            if not response:
                raise ValueError("Failed to generate documentation")
                
            # Extract JSON from response
            documentation = self._extract_json_from_text(response)
            if not documentation:
                raise ValueError("Failed to extract documentation from response")
                
            # Validate documentation structure
            if not self._validate_documentation(documentation):
                raise ValueError("Invalid documentation structure")
                
            return documentation
            
        except Exception as e:
            logger.error(f"Failed to generate documentation: {str(e)}")
            raise ValueError(f"Documentation generation failed: {str(e)}")
            
    async def _format_prompt(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any],
        quality_check: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format prompt for documentation generation.
        
        Args:
            requirements: Requirements data
            analysis: Analysis results
            quality_check: Quality check results
            context: Optional context information
            
        Returns:
            Formatted prompt
        """
        try:
            # 准备基本数据
            requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)
            analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
            quality_check_json = json.dumps(quality_check, indent=2, ensure_ascii=False)
            
            # 准备上下文信息
            context_info = ""
            if context:
                context_info = "\n当前上下文:\n"
                if context.get("clarifications"):
                    context_info += "需求澄清历史:\n"
                    for c in context["clarifications"]:
                        context_info += f"Q: {c['question']}\nA: {c['answer']}\n"
                if context.get("current_analysis"):
                    context_info += "\n当前分析状态:\n"
                    context_info += json.dumps(context["current_analysis"], indent=2, ensure_ascii=False)
            
            # Format template
            return self.prompt_template.format(
                requirements=requirements_json,
                analysis=analysis_json,
                quality_check=quality_check_json,
                context_info=context_info
            )
            
        except Exception as e:
            logger.error(f"Failed to format prompt: {str(e)}")
            raise ValueError(f"Failed to format prompt: {str(e)}")
            
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response.
        
        Args:
            text: Text to extract JSON from
            
        Returns:
            Extracted JSON
            
        Raises:
            ValueError: If no valid JSON found
        """
        # 清理中文标点符号
        text = text.replace("，", ",").replace("：", ":")
        
        # 尝试提取 JSON 格式的内容
        patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",      # ``` ... ```
            r"\{.*\}"                   # {...}
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                try:
                    result = json.loads(matches[0])
                    return result
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON with pattern {pattern}: {e}")
                    continue
        
        raise ValueError("No valid JSON found in content")
        
    def _validate_documentation(self, documentation: Dict[str, Any]) -> bool:
        """Validate documentation structure.
        
        Args:
            documentation: Documentation to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "project_overview",
            "executive_summary",
            "requirements_specification",
            "analysis_results",
            "quality_assessment",
            "implementation_plan"
        ]
        
        if not isinstance(documentation, dict):
            return False
            
        doc = documentation.get("documentation", {})
        if not isinstance(doc, dict):
            return False
            
        for field in required_fields:
            if field not in doc:
                return False
                
        return True
        
    async def save_documentation(
        self,
        documentation: Dict[str, Any],
        output_path: str
    ) -> None:
        """Save documentation to file.
        
        Args:
            documentation: Documentation to save
            output_path: Path to save documentation to
            
        Raises:
            ValueError: If saving fails
        """
        try:
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存 JSON 格式
            json_path = Path(output_path).with_suffix(".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(documentation, f, indent=2, ensure_ascii=False)
                
            # 保存 Markdown 格式
            md_path = Path(output_path).with_suffix(".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(self._generate_markdown(documentation))
                
            logger.info(f"Documentation saved to {json_path} and {md_path}")
            
        except Exception as e:
            logger.error(f"Failed to save documentation: {str(e)}")
            raise ValueError(f"Failed to save documentation: {str(e)}")
            
    def _generate_markdown(self, documentation: Dict[str, Any]) -> str:
        """Generate Markdown from documentation.
        
        Args:
            documentation: Documentation to convert
            
        Returns:
            Markdown string
        """
        doc = documentation.get("documentation", {})
        
        md = []
        
        # 项目概述
        overview = doc.get("project_overview", {})
        md.append(f"# {overview.get('title', '需求文档')}")
        md.append(f"\n**版本:** {overview.get('version', '1.0.0')}")
        md.append(f"**日期:** {overview.get('date', datetime.now().strftime('%Y-%m-%d'))}")
        md.append(f"**状态:** {overview.get('status', '草稿')}\n")
        
        # 执行摘要
        summary = doc.get("executive_summary", {})
        md.append("## 执行摘要")
        md.append(f"\n### 背景\n{summary.get('background', '')}")
        
        if "objectives" in summary:
            md.append("\n### 目标")
            for obj in summary["objectives"]:
                md.append(f"- {obj}")
                
        # 需求规格
        reqs = doc.get("requirements_specification", {})
        md.append("\n## 需求规格")
        
        if "functional_requirements" in reqs:
            md.append("\n### 功能需求")
            for req in reqs["functional_requirements"]:
                md.append(f"\n#### {req.get('title', '')}")
                md.append(f"- ID: {req.get('id', '')}")
                md.append(f"- 优先级: {req.get('priority', '')}")
                md.append(f"- 状态: {req.get('status', '')}")
                md.append(f"\n{req.get('description', '')}")
                
                if "acceptance_criteria" in req:
                    md.append("\n验收标准:")
                    for ac in req["acceptance_criteria"]:
                        md.append(f"- {ac}")
                        
        # 分析结果
        analysis = doc.get("analysis_results", {})
        md.append("\n## 分析结果")
        
        if "feasibility" in analysis:
            md.append("\n### 可行性分析")
            for key, value in analysis["feasibility"].items():
                md.append(f"\n#### {key.title()}")
                md.append(f"- 评分: {value.get('score', '')}")
                md.append(f"- 总结: {value.get('summary', '')}")
                
                if "challenges" in value:
                    md.append("\n挑战:")
                    for challenge in value["challenges"]:
                        md.append(f"- {challenge}")
                        
                if "recommendations" in value:
                    md.append("\n建议:")
                    for rec in value["recommendations"]:
                        md.append(f"- {rec}")
                        
        # 质量评估
        quality = doc.get("quality_assessment", {})
        md.append("\n## 质量评估")
        md.append(f"\n总体评分: {quality.get('overall_score', '')}")
        md.append(f"\n总结: {quality.get('summary', '')}")
        
        if "metrics" in quality:
            for key, value in quality["metrics"].items():
                md.append(f"\n### {key.title()}")
                md.append(f"- 评分: {value.get('score', '')}")
                
                if "findings" in value:
                    md.append("\n发现:")
                    for finding in value["findings"]:
                        md.append(f"- {finding}")
                        
                if "recommendations" in value:
                    md.append("\n建议:")
                    for rec in value["recommendations"]:
                        md.append(f"- {rec}")
                        
        # 实施计划
        plan = doc.get("implementation_plan", {})
        md.append("\n## 实施计划")
        
        if "phases" in plan:
            for phase in plan["phases"]:
                md.append(f"\n### {phase.get('name', '')}")
                md.append(f"- 周期: {phase.get('duration', '')}")
                
                if "deliverables" in phase:
                    md.append("\n交付物:")
                    for deliverable in phase["deliverables"]:
                        md.append(f"- {deliverable}")
                        
                if "milestones" in phase:
                    md.append("\n里程碑:")
                    for milestone in phase["milestones"]:
                        md.append(f"- {milestone}")
                        
        return "\n".join(md) 