"""文档生成智能体"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseAgent

logger = logging.getLogger(__name__)


class DocumentationGenerator(BaseAgent):
    """文档生成智能体 - 基于需求分析结果生成各种格式的文档"""

    def __init__(self, config: Any = None):
        """初始化文档生成智能体

        Args:
            config: 配置对象（SystemConfig或字典）
        """
        # 处理配置参数
        if config is None:
            config_dict = {}
        elif hasattr(config, "__dict__"):
            # 如果是配置对象，转换为字典
            config_dict = vars(config)
        elif isinstance(config, dict):
            config_dict = config
        else:
            config_dict = {}

        # 调用父类初始化，传递name和config字典
        super().__init__("DocumentationGenerator", config_dict)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文档生成任务

        Args:
            input_data: 包含需求、分析和质量报告的数据

        Returns:
            生成的文档
        """
        try:
            requirements = input_data.get("requirements", {})
            analysis = input_data.get("analysis", {})
            quality_report = input_data.get("quality_report", {})

            if not requirements:
                raise ValueError("需求信息不能为空")

            doc_format = input_data.get("format", "markdown")
            template_type = input_data.get("template", "standard")

            logger.info(f"开始生成{doc_format}格式文档")

            # 使用统一的提示词模板
            response = await self._call_llm_with_template(
                "documentation_generation",
                requirements=json.dumps(requirements, ensure_ascii=False),
                analysis=json.dumps(analysis, ensure_ascii=False),
                quality_report=json.dumps(quality_report, ensure_ascii=False),
                format=doc_format,
                template=template_type,
            )

            # 生成文档内容
            document_content = self._process_document_content(response, doc_format)

            # 生成元数据
            metadata = self._generate_metadata(requirements, analysis, quality_report)

            logger.info("文档生成完成")

            return {
                "status": "success",
                "document": {
                    "content": document_content,
                    "format": doc_format,
                    "template": template_type,
                    "metadata": metadata,
                },
            }

        except Exception as e:
            logger.error(f"文档生成失败: {str(e)}")
            return {"status": "error", "error": str(e), "document": None}

    def _process_document_content(self, response: str, doc_format: str) -> str:
        """处理文档内容"""
        if doc_format == "markdown":
            return self._ensure_markdown_format(response)
        elif doc_format == "html":
            return self._convert_to_html(response)
        elif doc_format == "word":
            return self._prepare_word_content(response)
        else:
            return response

    def _ensure_markdown_format(self, content: str) -> str:
        """确保内容是有效的Markdown格式"""
        lines = content.split("\n")
        processed_lines = []

        for line in lines:
            # 确保标题格式正确
            if (
                line.strip()
                and not line.startswith("#")
                and not line.startswith("-")
                and not line.startswith("*")
            ):
                # 如果看起来像标题，添加#
                if len(line.strip()) < 100 and line.strip().endswith(":"):
                    line = f"## {line.strip()[:-1]}"
                elif line.strip().isupper() and len(line.strip()) < 50:
                    line = f"### {line.strip()}"

            processed_lines.append(line)

        return "\n".join(processed_lines)

    def _convert_to_html(self, content: str) -> str:
        """转换为HTML格式"""
        # 简单的Markdown到HTML转换
        html_content = content

        # 标题转换
        html_content = html_content.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html_content = html_content.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        _html_content = html_content.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)

        # 列表转换
        lines = html_content.split("\n")
        processed_lines = []
        in_list = False

        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    processed_lines.append("<ul>")
                    in_list = True
                processed_lines.append(f"<li>{line.strip()[2:]}</li>")
            else:
                if in_list:
                    processed_lines.append("</ul>")
                    in_list = False
                processed_lines.append(line)

        if in_list:
            processed_lines.append("</ul>")

        return "\n".join(processed_lines)

    def _prepare_word_content(self, content: str) -> str:
        """准备Word文档内容"""
        # 为Word文档添加样式标记
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>需求分析文档</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; }}
        h3 {{ color: #7f8c8d; }}
    </style>
</head>
<body>
{self._convert_to_html(content)}
</body>
</html>
"""

    def _generate_metadata(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any],
        quality_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成文档元数据"""
        return {
            "generated_at": datetime.now().isoformat(),
            "generator": "OWL需求分析助手",
            "version": "1.0",
            "statistics": {
                "functional_requirements": len(
                    requirements.get("functional_requirements", [])
                ),
                "non_functional_requirements": len(
                    requirements.get("non_functional_requirements", [])
                ),
                "constraints": len(requirements.get("constraints", [])),
                "total_requirements": (
                    len(requirements.get("functional_requirements", []))
                    + len(requirements.get("non_functional_requirements", []))
                ),
                "quality_score": (
                    quality_report.get("quality_score", 0.0)
                    if isinstance(quality_report, dict)
                    else 0.0
                ),
            },
        }

    async def generate_markdown(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        quality_report: Dict[str, Any] = None,
    ) -> str:
        """便捷方法：生成Markdown文档"""
        result = await self.process(
            {
                "requirements": requirements,
                "analysis": analysis or {},
                "quality_report": quality_report or {},
                "format": "markdown",
            }
        )

        if result["status"] == "success":
            return result["document"]["content"]
        else:
            return f"文档生成失败: {result.get('error', '未知错误')}"

    async def generate_html(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        quality_report: Dict[str, Any] = None,
    ) -> str:
        """便捷方法：生成HTML文档"""
        result = await self.process(
            {
                "requirements": requirements,
                "analysis": analysis or {},
                "quality_report": quality_report or {},
                "format": "html",
            }
        )

        if result["status"] == "success":
            return result["document"]["content"]
        else:
            return f"<p>文档生成失败: {result.get('error', '未知错误')}</p>"

    def generate_simple_document(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        quality_report: Dict[str, Any] = None,
    ) -> str:
        """生成简单的文档（不使用LLM）"""
        doc_lines = [
            "# 需求分析文档",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 功能需求",
            "",
        ]

        # 功能需求
        for i, req in enumerate(requirements.get("functional_requirements", []), 1):
            if isinstance(req, dict):
                desc = req.get("description", "")
                priority = req.get("priority", "medium")
                doc_lines.append(f"{i}. **{desc}** (优先级: {priority})")
            else:
                doc_lines.append(f"{i}. {req}")

        doc_lines.extend(["", "## 非功能需求", ""])

        # 非功能需求
        for i, req in enumerate(requirements.get("non_functional_requirements", []), 1):
            if isinstance(req, dict):
                desc = req.get("description", "")
                req_type = req.get("type", "general")
                doc_lines.append(f"{i}. **{desc}** (类型: {req_type})")
            else:
                doc_lines.append(f"{i}. {req}")

        # 约束条件
        if requirements.get("constraints"):
            doc_lines.extend(["", "## 约束条件", ""])
            for i, constraint in enumerate(requirements["constraints"], 1):
                if isinstance(constraint, dict):
                    desc = constraint.get("description", "")
                    doc_lines.append(f"{i}. {desc}")
                else:
                    doc_lines.append(f"{i}. {constraint}")

        # 分析结果
        if analysis:
            doc_lines.extend(["", "## 分析结果", ""])

            # 可行性分析
            feasibility = analysis.get("feasibility_analysis", {})
            if feasibility:
                doc_lines.extend(
                    [
                        "### 可行性分析",
                        f"- 技术可行性: {feasibility.get('technical_feasibility', '待评估')}",
                        f"- 资源可行性: {feasibility.get('resource_feasibility', '待评估')}",
                        f"- 时间可行性: {feasibility.get('time_feasibility', '待评估')}",
                        "",
                    ]
                )

            # 风险分析
            risks = analysis.get("risk_analysis", [])
            if risks:
                doc_lines.extend(["### 风险分析", ""])
                for i, risk in enumerate(risks, 1):
                    if isinstance(risk, dict):
                        desc = risk.get("description", "")
                        probability = risk.get("probability", "medium")
                        impact = risk.get("impact", "medium")
                        doc_lines.append(
                            f"{i}. **{desc}** (概率: {probability}, 影响: {impact})"
                        )
                doc_lines.append("")

        # 质量报告
        if quality_report and isinstance(quality_report, dict):
            quality_score = quality_report.get("quality_score", 0.0)
            doc_lines.extend(
                ["## 质量评估", f"**总体质量分数**: {quality_score:.2f}", ""]
            )

        return "\n".join(doc_lines)

    async def generate(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any] = None,
        quality_check: Dict[str, Any] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """生成文档的接口方法，供AgentCoordinator调用

        Args:
            requirements: 需求信息
            analysis: 分析结果
            quality_check: 质量检查结果
            context: 可选的上下文信息

        Returns:
            生成的文档
        """
        input_data = {
            "requirements": requirements,
            "format": "markdown",  # 默认生成markdown格式
        }
        if analysis:
            input_data["analysis"] = analysis
        if quality_check:
            input_data["quality_report"] = quality_check
        if context:
            input_data["context"] = context

        result = await self.process(input_data)
        return result.get("document", {})

    async def save_documentation(
        self, documentation: Dict[str, Any], output_path: str
    ) -> None:
        """保存文档到文件

        Args:
            documentation: 文档内容
            output_path: 输出文件路径
        """
        from pathlib import Path

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 如果是JSON格式，保存为JSON
            if output_path.endswith(".json"):
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(documentation, f, ensure_ascii=False, indent=2)
            # 如果是Markdown格式，提取内容保存
            elif output_path.endswith(".md"):
                content = documentation.get("content", "")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
            # 默认保存为JSON
            else:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(documentation, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存文档失败: {str(e)}")
            raise
