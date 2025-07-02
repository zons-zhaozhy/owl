import json
import logging
from ..core.config import SystemConfig
from ..utils.exceptions import AnalysisError
from .llm_manager import LLMManager
from .base import BaseService
from typing import Any
from typing import Dict
from typing import List


class AnalyzerService(BaseService):
    """需求分析服务"""

    def __init__(self, config: SystemConfig):
        super().__init__(config)
        self.llm_manager = LLMManager(config)

    async def initialize(self) -> None:
        """初始化服务"""
        await self.llm_manager.initialize()

    async def cleanup(self) -> None:
        """清理服务"""
        await self.llm_manager.cleanup()

    async def analyze(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析需求列表"""
        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(requirements)

            # 调用LLM进行分析
            response = await self.llm_manager.generate_text(prompt)

            # 解析分析结果
            result = self._parse_analysis_result(response)

            return result
        except Exception as e:
            logging.error(f"需求分析失败: {str(e)}")
            raise AnalysisError(f"需求分析失败: {str(e)}")

    def _build_analysis_prompt(self, requirements: List[Dict[str, Any]]) -> str:
        """构建分析提示"""
        prompt = "请分析以下需求列表，提供详细的分析结果：\n\n"

        for i, req in enumerate(requirements, 1):
            prompt += f"{i}. {req.get('title', '未命名需求')}\n"
            prompt += f"   描述: {req.get('description', '无描述')}\n"
            prompt += f"   优先级: {req.get('priority', '未指定')}\n"
            if req.get("dependencies"):
                prompt += f"   依赖: {', '.join(req['dependencies'])}\n"
            prompt += "\n"

        prompt += """请提供以下方面的分析：
1. 需求完整性评估
2. 需求间的依赖关系
3. 实现复杂度评估
4. 潜在风险分析
5. 建议的实现方案

请以JSON格式返回分析结果，包含以下字段：
{
    "completeness": float,  # 完整性评分（0-1）
    "dependencies": [{"from": "需求A", "to": "需求B"}],  # 依赖关系
    "complexity": {  # 复杂度评估
        "overall": string,  # 总体复杂度
        "details": {}  # 具体分析
    },
    "risks": [  # 风险列表
        {
            "description": string,
            "severity": string,
            "mitigation": string
        }
    ],
    "recommendations": [  # 建议列表
        {
            "aspect": string,
            "suggestion": string
        }
    ]
}"""

        return prompt

    def _parse_analysis_result(self, response: str) -> Dict[str, Any]:
        """解析分析结果"""
        try:
            # 提取JSON部分
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("响应中未找到JSON数据")

            json_str = response[start:end]
            result = json.loads(json_str)

            # 验证必要字段
            required_fields = [
                "completeness",
                "dependencies",
                "complexity",
                "risks",
                "recommendations",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"缺少必要字段: {field}")

            return result
        except json.JSONDecodeError as e:
            raise AnalysisError(f"无法解析分析结果: {str(e)}")
        except Exception as e:
            raise AnalysisError(f"处理分析结果时出错: {str(e)}")


# 保持向后兼容
class RequirementsAnalyzer(AnalyzerService):
    """需求分析器 - 保持向后兼容"""

    def __init__(self, config: SystemConfig):
        super().__init__(config)
        self.llm_factory = self.llm_manager  # 兼容性别名
