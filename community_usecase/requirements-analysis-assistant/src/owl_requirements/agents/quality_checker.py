"""Quality checker agent implementation."""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.base import BaseAgent
from ..services.base import BaseLLMService
from ..core.config import SystemConfig
from ..core.models import QualityReport
from ..utils.enums import AgentRole

logger = logging.getLogger(__name__)

class QualityChecker(BaseAgent):
    """Quality checker agent implementation."""
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        config: SystemConfig
    ):
        """Initialize quality checker.
        
        Args:
            llm_service: LLM service instance
            config: Agent configuration
        """
        super().__init__(config.get_agent_config(AgentRole.QUALITY_CHECKER).to_dict())
        self.system_config = config
        self.llm_service = llm_service
        self.max_retries = self.system_config.max_retries
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        template_path = Path(self.system_config.templates_dir) / "quality_checker.json"
        
        current_file_dir = Path(__file__).parent
        project_root = current_file_dir.parent.parent.parent
        absolute_template_path = project_root / template_path

        if not absolute_template_path.exists():
            # 使用默认模板
            return """请检查以下需求和分析的质量。

需求:
{requirements}

分析:
{analysis}

{context_info}

请以JSON格式返回质量检查结果，包含以下字段:
1. quality_score: 质量评分
   - requirements_quality: 需求质量评分
   - analysis_quality: 分析质量评分
2. issues: 发现的问题
3. suggestions: 改进建议

示例输出:
{
    "quality_score": {
        "requirements_quality": {
            "score": 85,
            "details": []
        },
        "analysis_quality": {
            "score": 90,
            "details": []
        }
    },
    "issues": [],
    "suggestions": []
}"""
            
        with open(absolute_template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["template"]
        
    async def check(self, requirements: Dict[str, Any], analysis: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> QualityReport:
        """Check requirements quality.
        
        Args:
            requirements: Requirements to check
            analysis: Requirements analysis
            context: Optional context information
            
        Returns:
            Quality check results
        """
        return await self.process({
            "requirements": requirements,
            "analysis": analysis,
            "context": context
        })
        
    async def process(self, input_data: Dict[str, Any]) -> QualityReport:
        """Process input data.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processing results
        """
        logger.info(f"Processing input: {json.dumps(input_data, indent=2)}")
        
        # Generate prompt
        prompt = await self._generate_prompt(input_data)
        logger.info(f"Generated prompt: {prompt}")
        
        # Process with retries
        error_msg = None
        for attempt in range(self.max_retries):
            try:
                # Call LLM service with minimal parameters
                response = await self.llm_service.generate(
                    prompt=prompt,
                    temperature=0.1,  # Keep only essential parameters
                    max_tokens=4000
                )
                
                # Extract and validate JSON using Pydantic
                result = self._extract_json(response)
                return result
                    
            except Exception as e:
                error_msg = f"Unexpected error (attempt {attempt + 1}): {str(e)}"
                logger.error(error_msg, exc_info=True)
                continue
                
        # If we get here, all attempts failed
        error_msg = error_msg or "Failed to process input"
        logger.error(f"Quality check failed after {self.max_retries} attempts: {error_msg}")
        raise ValueError(error_msg)
        
    async def _generate_prompt(self, input_data: Dict[str, Any]) -> str:
        """Generate prompt from template.
        
        Args:
            input_data: Input data
            
        Returns:
            Generated prompt
        """
        try:
            # Get requirements and analysis
            requirements = input_data.get("requirements")
            analysis = input_data.get("analysis")
            context = input_data.get("context", {})
            
            if not requirements or not analysis:
                raise ValueError("Missing requirements or analysis")
            
            logger.debug(f"Requirements for prompt: {requirements}")
            logger.debug(f"Analysis for prompt: {analysis}")
            
            requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)
            analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
            
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
                context_info=context_info
            )
            
        except Exception as e:
            logger.error(f"Failed to generate prompt: {e}", exc_info=True)
            raise ValueError(f"Failed to generate prompt: {str(e)}")
        
    def _extract_json(self, response: Any) -> QualityReport:
        """Extract JSON from LLM response.
        
        Args:
            response: LLM response object or text
            
        Returns:
            Extracted JSON
            
        Raises:
            ValueError: If no valid JSON found
        """
        logger.debug(f"Raw LLM response: {response}")
        # Handle response
        text = response if isinstance(response, str) else str(response)
        if not text:
            raise ValueError("Empty response from LLM")
            
        # First try to find JSON between triple backticks
        json_patterns = [
            r"```json\s*([\s\S]*?)\s*```",  # ```json ... ```
            r"```\s*([\s\S]*?)\s*```",      # ``` ... ```
            r"\{[\s\S]*\}"                   # Raw JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    json_str = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    # Clean up the string
                    json_str = json_str.strip()
                    # Remove any markdown formatting artifacts
                    json_str = re.sub(r'^```\s*json\s*', '', json_str)
                    json_str = re.sub(r'```\s*$', '', json_str)
                    # Remove any Chinese punctuation that might interfere
                    json_str = re.sub(r'[""''，。：；？！]', lambda x: {
                        '"': '"', '"': '"', ''': "'", ''': "'",
                        '，': ',', '。': '.', '：': ':',
                        '；': ';', '？': '?', '！': '!'
                    }[x.group()], json_str)
                    
                    logger.info(f"Attempting to parse JSON string: {json_str}")
                    # Parse JSON and validate with Pydantic
                    result = json.loads(json_str)
                    
                    # Use Pydantic to validate and return the model
                    validated_result = QualityReport.model_validate(result)
                    return validated_result
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON match: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Unexpected error parsing JSON or validating with Pydantic: {e}")
                    continue
                    
        raise ValueError("No valid JSON found in response")
        
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate result format.
        
        This method is now redundant as Pydantic validation is handled in _extract_json.
        However, it must remain as BaseAgent expects it.
        """
        return True