"""Requirements extractor agent implementation."""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.base import BaseAgent
from ..services.base import BaseLLMService
from ..core.config import OWLJSONEncoder, SystemConfig
from ..utils.enums import AgentRole

logger = logging.getLogger(__name__)

class RequirementsExtractor(BaseAgent):
    """Requirements extractor agent implementation."""
    
    def __init__(
        self,
        llm_service: BaseLLMService,
        config: SystemConfig
    ):
        """Initialize requirements extractor.
        
        Args:
            llm_service: LLM service instance
            config: Agent configuration
        """
        super().__init__(config.get_agent_config(AgentRole.REQUIREMENTS_EXTRACTOR).to_dict())
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
        template_path = Path(self.system_config.templates_dir) / "requirements_extraction.json"
        
        current_file_dir = Path(__file__).parent
        project_root = current_file_dir.parent.parent.parent
        absolute_template_path = project_root / template_path

        if not absolute_template_path.exists():
            # 如果模板文件不存在，使用默认模板
            return """你是一个专业的需求分析师，请分析以下输入文本，提取关键需求。如果需要澄清，请提出具体问题。

用户输入:
{text}

{context}

请以JSON格式返回结果，包含以下字段:
1. requirements: 提取的需求列表，每个需求应包含:
   - id: 需求ID (如 REQ-001)
   - title: 需求标题
   - description: 需求描述
   - priority: 优先级 (high/medium/low)
   - type: 需求类型 (functional/non-functional)
2. clarification_needed: 如果需要澄清，提供具体问题
3. requirements_complete: 布尔值，表示需求是否完整

示例输出:
{
    "requirements": [
        {
            "id": "REQ-001",
            "title": "用户登录功能",
            "description": "系统需要提供用户登录功能，包括用户名和密码验证",
            "priority": "high",
            "type": "functional"
        }
    ],
    "clarification_needed": "请问系统需要支持第三方登录吗？",
    "requirements_complete": false
}"""
            
        with open(absolute_template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["template"]
            
    async def _prepare_prompt(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare prompt for LLM.
        
        Args:
            input_text: Input text to process
            context: Optional context information
            
        Returns:
            Prepared prompt string
        """
        context_info = ""
        if context:
            context_info = "\n当前上下文:\n"
            if context.get("requirements"):
                context_info += "已收集的需求:\n"
                for req in context["requirements"]:
                    if isinstance(req, dict):
                        context_info += f"- [{req.get('id', 'N/A')}] {req.get('title', 'N/A')}: {req.get('description', 'N/A')}\n"
                    else:
                        context_info += f"- {req}\n"
            if context.get("clarifications"):
                context_info += "\n历史澄清:\n"
                for c in context["clarifications"]:
                    context_info += f"Q: {c['question']}\nA: {c['answer']}\n"
        
        return self.prompt_template.format(
            input=input_text,
            context=context_info
        )
        
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from content."""
        # 清理中文标点符号
        content = content.replace("，", ",").replace("：", ":")
        
        # 尝试提取 JSON 格式的内容
        patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",      # ``` ... ```
            r"\{.*\}"                   # {...}
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                try:
                    result = json.loads(matches[0])
                    return result
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON with pattern {pattern}: {e}")
                    continue
        
        raise ValueError("No valid JSON found in content")
        
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate extraction result."""
        if not isinstance(result, dict):
            return False
            
        # 检查是否包含必要的字段
        required_fields = ["requirements"]
        for field in required_fields:
            if field not in result:
                return False
                
        # 验证需求列表的格式
        requirements = result["requirements"]
        if not isinstance(requirements, list):
            return False
            
        for req in requirements:
            if not isinstance(req, dict):
                return False
            required_req_fields = ["id", "title", "description", "priority", "type"]
            for field in required_req_fields:
                if field not in req:
                    return False
                    
        return True
        
    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process input text and extract requirements.
        
        Args:
            input_text: Input text to process
            context: Optional context information
            
        Returns:
            Extracted requirements
        """
        logger.info(f"Processing input: {json.dumps({'text': input_text}, cls=OWLJSONEncoder, indent=2)}")
        
        # 准备 prompt
        prompt = await self._prepare_prompt(input_text, context)
        
        # 调用 LLM 服务
        for i in range(self.max_retries):
            try:
                response = await self.llm_service.generate(prompt)
                logger.debug(f"LLM response: {json.dumps({'response': response.text}, cls=OWLJSONEncoder, indent=2)}")
                
                # 提取并验证结果
                result = self._extract_json(response.text)
                if self._validate_result(result):
                    logger.info(f"Successfully extracted requirements: {json.dumps(result, cls=OWLJSONEncoder, indent=2)}")
                    return result
                    
                logger.warning("Invalid result format")
                
            except Exception as e:
                logger.error(f"Failed to process input (attempt {i+1}/{self.max_retries}): {e}")
                if i == self.max_retries - 1:
                    raise
                    
        raise RuntimeError("Failed to process input after maximum retries")
            
    async def extract(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract requirements from input text.
        
        Args:
            input_text: Input text to process
            context: Optional context information
            
        Returns:
            Extracted requirements
        """
        logger.info(f"Extracting requirements from: {json.dumps({'text': input_text}, indent=2, cls=OWLJSONEncoder)}")
        
        for attempt in range(self.max_retries):
            try:
                return await self.process(input_text, context)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to extract requirements after {self.max_retries} attempts")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                continue 