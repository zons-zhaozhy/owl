"""需求提取智能体"""

import json
import logging
from typing import Dict, Any, List, Optional

from ..core.base_agent import BaseAgent
from ..core.exceptions import ExtractionError
from ..services.llm_manager import get_llm_manager
from ..utils.json_utils import extract_json_safely

logger = logging.getLogger(__name__)

class RequirementsExtractor(BaseAgent):
    """需求提取智能体，负责从输入文本中提取结构化需求。"""

    def __init__(self, config: Dict[str, Any]):
        """初始化需求提取智能体。

        Args:
            config: 配置字典
        """
        super().__init__(config)
        self.llm_manager = get_llm_manager()
        self.extraction_prompt = config.get("extraction_prompt", "default_extraction_prompt")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据，提取需求。

        这是智能体的主要处理方法，实现了BaseAgent的抽象方法。

        Args:
            input_data: 输入数据字典，必须包含：
                - input_text: 输入文本
                - context: 可选的对话上下文

        Returns:
            Dict[str, Any]: 提取结果，包含：
                - status: 处理状态 ("success" 或 "error")
                - requirements: 提取的需求（如果成功）
                - error: 错误信息（如果失败）

        Raises:
            ExtractionError: 提取过程中出错
        """
        try:
            # 验证输入
            if "input_text" not in input_data:
                raise ValueError("缺少必要的input_text字段")

            input_text = input_data["input_text"]
            context = input_data.get("context", {})

            # 记录开始处理
            self.logger.info(f"开始处理输入文本，长度: {len(input_text)}")

            # 准备提示
            prompt = self._prepare_extraction_prompt(input_text, context)

            # 调用LLM
            response = await self.llm_manager.generate_text(prompt)

            # 提取JSON
            requirements = extract_json_safely(response)
            if not requirements:
                raise ExtractionError("无法从LLM响应中提取有效的JSON")

            # 验证提取结果
            self._validate_requirements(requirements)

            # 记录成功
            self.logger.info("需求提取成功")
            return {
                "status": "success",
                "requirements": requirements
            }

        except Exception as e:
            # 记录错误
            await self.handle_error(e)
            return {
                "status": "error",
                "error": str(e)
            }

    def _prepare_extraction_prompt(self, text: str, context: Dict[str, Any]) -> str:
        """准备提取提示。

        Args:
            text: 输入文本
            context: 对话上下文

        Returns:
            str: 格式化的提示
        """
        # 这里可以根据上下文调整提示
        base_prompt = """请分析以下文本，提取所有需求并按以下JSON格式返回：
{
    "functional_requirements": [
        {
            "id": "FR1",
            "description": "需求描述",
            "priority": "高/中/低",
            "category": "功能类别"
        }
    ],
    "non_functional_requirements": [
        {
            "id": "NFR1",
            "description": "需求描述",
            "type": "性能/安全/可用性等",
            "constraint": "具体约束"
        }
    ]
}

输入文本：
"""
        return f"{base_prompt}\n{text}"

    def _validate_requirements(self, requirements: Dict[str, Any]) -> None:
        """验证提取的需求。

        Args:
            requirements: 需求字典

        Raises:
            ExtractionError: 验证失败
        """
        required_keys = ["functional_requirements", "non_functional_requirements"]
        for key in required_keys:
            if key not in requirements:
                raise ExtractionError(f"缺少必要的需求类别: {key}")

            if not isinstance(requirements[key], list):
                raise ExtractionError(f"需求类别 {key} 必须是列表")

        # 验证功能需求
        for req in requirements["functional_requirements"]:
            if not all(k in req for k in ["id", "description", "priority", "category"]):
                raise ExtractionError("功能需求缺少必要字段")

        # 验证非功能需求
        for req in requirements["non_functional_requirements"]:
            if not all(k in req for k in ["id", "description", "type", "constraint"]):
                raise ExtractionError("非功能需求缺少必要字段")

    def get_required_config_fields(self) -> List[str]:
        """获取必需的配置字段。

        Returns:
            List[str]: 必需的配置字段列表
        """
        return ["name", "extraction_prompt"]

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response)
            
        except json.JSONDecodeError:
            # 如果不是JSON，尝试提取JSON部分
            return self._extract_json_from_text(response)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取JSON"""
        try:
            # 查找JSON代码块
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            
            # 如果找不到JSON，返回结构化的文本解析结果
            return self._parse_text_response(text)
            
        except Exception as e:
            logger.warning(f"JSON提取失败: {str(e)}")
            return self._parse_text_response(text)
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """解析文本响应为结构化格式"""
        # 基本的文本解析逻辑
        lines = text.split('\n')
        
        functional_requirements = []
        non_functional_requirements = []
        constraints = []
        assumptions = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 识别章节
            if "功能需求" in line or "functional" in line.lower():
                current_section = "functional"
                continue
            elif "非功能需求" in line or "non-functional" in line.lower():
                current_section = "non_functional"
                continue
            elif "约束" in line or "constraint" in line.lower():
                current_section = "constraints"
                continue
            elif "假设" in line or "assumption" in line.lower():
                current_section = "assumptions"
                continue
            
            # 添加到相应章节
            if line.startswith(('-', '*', '•')) or line[0].isdigit():
                content = line.lstrip('-*•0123456789. ')
                
                if current_section == "functional":
                    functional_requirements.append({
                        "id": f"FR_{len(functional_requirements) + 1:03d}",
                        "description": content,
                        "priority": "medium",
                        "category": "general"
                    })
                elif current_section == "non_functional":
                    non_functional_requirements.append({
                        "id": f"NFR_{len(non_functional_requirements) + 1:03d}",
                        "type": "general",
                        "description": content,
                        "metrics": ""
                    })
                elif current_section == "constraints":
                    constraints.append({
                        "type": "general",
                        "description": content
                    })
                elif current_section == "assumptions":
                    assumptions.append(content)
        
        return {
            "functional_requirements": functional_requirements,
            "non_functional_requirements": non_functional_requirements,
            "constraints": constraints,
            "assumptions": assumptions,
            "dependencies": []
        }
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化需求"""
        validated = {
            "functional_requirements": [],
            "non_functional_requirements": [],
            "constraints": [],
            "assumptions": [],
            "dependencies": []
        }
        
        # 验证功能需求
        for req in requirements.get("functional_requirements", []):
            if isinstance(req, dict) and "description" in req:
                validated_req = {
                    "id": req.get("id", f"FR_{len(validated['functional_requirements']) + 1:03d}"),
                    "description": req["description"],
                    "priority": req.get("priority", "medium"),
                    "category": req.get("category", "general")
                }
                validated["functional_requirements"].append(validated_req)
            elif isinstance(req, str):
                validated["functional_requirements"].append({
                    "id": f"FR_{len(validated['functional_requirements']) + 1:03d}",
                    "description": req,
                    "priority": "medium",
                    "category": "general"
                })
        
        # 验证非功能需求
        for req in requirements.get("non_functional_requirements", []):
            if isinstance(req, dict) and "description" in req:
                validated_req = {
                    "id": req.get("id", f"NFR_{len(validated['non_functional_requirements']) + 1:03d}"),
                    "type": req.get("type", "general"),
                    "description": req["description"],
                    "metrics": req.get("metrics", "")
                }
                validated["non_functional_requirements"].append(validated_req)
            elif isinstance(req, str):
                validated["non_functional_requirements"].append({
                    "id": f"NFR_{len(validated['non_functional_requirements']) + 1:03d}",
                    "type": "general",
                    "description": req,
                    "metrics": ""
                })
        
        # 验证约束条件
        for constraint in requirements.get("constraints", []):
            if isinstance(constraint, dict):
                validated["constraints"].append({
                    "type": constraint.get("type", "general"),
                    "description": constraint.get("description", "")
                })
            elif isinstance(constraint, str):
                validated["constraints"].append({
                    "type": "general",
                    "description": constraint
                })
        
        # 验证假设
        validated["assumptions"] = [
            assumption for assumption in requirements.get("assumptions", [])
            if isinstance(assumption, str) and assumption.strip()
        ]
        
        # 验证依赖关系
        for dep in requirements.get("dependencies", []):
            if isinstance(dep, dict) and "from" in dep and "to" in dep:
                validated["dependencies"].append({
                    "from": dep["from"],
                    "to": dep["to"],
                    "type": dep.get("type", "depends_on")
                })
        
        return validated
    
    async def extract_from_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """便捷方法：从文本提取需求"""
        return await self.process({
            "input_text": text,
            **kwargs
        })
    
    async def extract_from_document(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """从文档文件提取需求"""
        try:
            # 这里可以添加文档解析逻辑
            # 目前简单读取文本文件
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return await self.extract_from_text(text, **kwargs)
            
        except Exception as e:
            logger.error(f"文档读取失败: {str(e)}")
            return {
                "status": "error",
                "error": f"文档读取失败: {str(e)}",
                "requirements": None
            }
    
    def get_extraction_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """获取提取统计信息"""
        if result.get("status") != "success" or not result.get("requirements"):
            return {"error": "无效的提取结果"}
        
        requirements = result["requirements"]
        
        return {
            "functional_requirements_count": len(requirements.get("functional_requirements", [])),
            "non_functional_requirements_count": len(requirements.get("non_functional_requirements", [])),
            "constraints_count": len(requirements.get("constraints", [])),
            "assumptions_count": len(requirements.get("assumptions", [])),
            "dependencies_count": len(requirements.get("dependencies", [])),
            "total_requirements": (
                len(requirements.get("functional_requirements", [])) +
                len(requirements.get("non_functional_requirements", []))
            )
        }
    
    async def extract(self, input_text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """提取需求的接口方法，供AgentCoordinator调用
        
        Args:
            input_text: 输入文本
            context: 可选的上下文信息
            
        Returns:
            提取结果
        """
        input_data = {
            "input_text": input_text
        }
        if context:
            input_data["context"] = context
            
        return await self.process(input_data) 