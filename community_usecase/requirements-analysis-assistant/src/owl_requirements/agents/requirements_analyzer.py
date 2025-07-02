"""Requirements analyzer agent implementation."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.base import BaseAgent
from ..services.base import BaseLLMService
from ..core.config import OWLJSONEncoder, SystemConfig
from ..utils.enums import AgentRole

logger = logging.getLogger(__name__)

class RequirementsAnalyzer(BaseAgent):
    """Requirements analyzer agent implementation."""
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        config: SystemConfig
    ):
        """Initialize requirements analyzer.
        
        Args:
            llm_service: LLM service instance
            config: Agent configuration
        """
        super().__init__(config.get_agent_config(AgentRole.REQUIREMENTS_ANALYZER).to_dict())
        self.system_config = config
        self.llm_service = llm_service
        self.max_retries = self.system_config.max_retries
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load prompt template from file.
        
        Args:
            None
            
        Returns:
            Prompt template string
        """
        current_file_dir = Path(__file__).parent
        project_root = current_file_dir.parent.parent.parent # Navigate up to requirements-analysis-assistant
        
        template_path = project_root / self.system_config.templates_dir / "requirements_analysis.json"
        
        logger.debug(f"Attempting to load prompt template from: {template_path.resolve()}")
        logger.debug(f"Current working directory: {os.getcwd()}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data["template"]
        except Exception as e:
            logger.error(f"Failed to load prompt template: {e}")
            # 使用默认模板
            return """请分析以下需求，提供详细的分析结果。

需求:
{requirements}

{context_info}

请以JSON格式返回分析结果，包含以下字段:
1. functional_analysis: 功能需求分析
2. non_functional_analysis: 非功能需求分析
3. dependencies: 依赖关系
4. risks: 风险评估
5. recommendations: 建议

示例输出:
{
    "functional_analysis": {
        "core_features": [],
        "optional_features": [],
        "user_interfaces": []
    },
    "non_functional_analysis": {
        "performance": {},
        "security": {},
        "scalability": {}
    },
    "dependencies": [],
    "risks": [],
    "recommendations": []
}"""

    async def _prepare_prompt(self, requirements: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare prompt for LLM.
        
        Args:
            requirements: Requirements to analyze
            context: Optional context information
            
        Returns:
            Prepared prompt string
        """
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
        
        return self.prompt_template.format(
            requirements=json.dumps(requirements, indent=2, ensure_ascii=False),
            context_info=context_info
        )

    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Placeholder for the abstract process method, calls analyze."""
        return await self.analyze(input_data, context)

    async def analyze(self, requirements: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process requirements and perform analysis.
        
        Args:
            requirements: Requirements to analyze
            context: Optional context information
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing requirements: {json.dumps(requirements, cls=OWLJSONEncoder, indent=2)}")
        
        # 准备 prompt
        prompt = await self._prepare_prompt(requirements, context)
        
        # 调用 LLM 服务
        for i in range(self.max_retries):
            try:
                response = await self.llm_service.generate(prompt)
                logger.debug(f"LLM response: {json.dumps({'response': response}, cls=OWLJSONEncoder, indent=2)}")
                
                # 清理Markdown代码块标记
                if response.startswith("```json") and response.endswith("```"):
                    response = response[len("```json\n"):-len("```")].strip()
                elif response.startswith("```") and response.endswith("```"):
                    response = response[len("```\n"):-len("```")].strip()

                # 解析响应
                try:
                    result = json.loads(response)
                    logger.info(f"Successfully analyzed requirements: {json.dumps(result, cls=OWLJSONEncoder, indent=2)}")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response as JSON: {e}")
                    if i == self.max_retries - 1:
                        raise
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to analyze requirements (attempt {i+1}/{self.max_retries}): {e}")
                if i == self.max_retries - 1:
                    raise
                    
        raise RuntimeError("Failed to analyze requirements after maximum retries") 