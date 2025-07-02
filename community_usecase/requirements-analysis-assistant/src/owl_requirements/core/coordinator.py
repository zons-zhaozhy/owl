from typing import Any
from typing import Dict
from typing import Optional

"""Coordinator for the multi-agent requirements analysis workflow."""

import json
import logging
from datetime import datetime
from pathlib import Path
import uuid

from loguru import logger

from ..agents.requirements_extractor import RequirementsExtractor
from ..agents.requirements_analyzer import RequirementsAnalyzer
from ..agents.quality_checker import QualityChecker
from ..agents.documentation_generator import DocumentationGenerator
from .config import SystemConfig
from .exceptions import CoordinatorError
from ..services.llm_manager import LLMManager, get_llm_manager


class DialogueContext:
    """对话上下文管理"""

    def __init__(self):
        self.requirements = []
        self.clarifications = []
        self.current_analysis = None
        self.conversation_history = []
        self.needs_clarification = False
        self.current_clarification = None
        self.is_complete = False

    def add_requirement(self, req):
        """添加需求"""
        self.requirements.append(req)

    def add_clarification(self, question: str, answer: str):
        """添加澄清记录

        Args:
            question: 澄清问题
            answer: 用户的回答
        """
        self.clarifications.append(
            {
                "question": question,
                "answer": answer,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_conversation_entry(self, role: str, content: str):
        """添加对话记录"""
        self.conversation_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_full_context(self):
        """获取完整上下文"""
        return {
            "requirements": self.requirements,
            "clarifications": self.clarifications,
            "current_analysis": self.current_analysis,
            "conversation_history": self.conversation_history,
            "needs_clarification": self.needs_clarification,
            "current_clarification": self.current_clarification,
            "is_complete": self.is_complete,
        }

    def set_needs_clarification(self, clarification: str):
        """设置需要澄清的状态

        Args:
            clarification: 澄清问题
        """
        self.needs_clarification = True
        self.current_clarification = clarification

    def clear_clarification_state(self):
        """清除澄清状态"""
        self.needs_clarification = False
        self.current_clarification = None


class AgentCoordinator:
    """协调多智能体需求分析工作流。"""

    def __init__(
        self,
        extractor: RequirementsExtractor,
        analyzer: RequirementsAnalyzer,
        checker: QualityChecker,
        generator: DocumentationGenerator,
    ):
        """初始化协调器。

        Args:
            extractor: 需求提取智能体
            analyzer: 需求分析智能体
            checker: 质量检查智能体
            generator: 文档生成智能体
        """
        self.agents = {
            "extractor": extractor,
            "analyzer": analyzer,
            "checker": checker,
            "generator": generator,
        }
        self.dialogue_contexts = {}  # 存储多个会话的上下文

        # 工作流指标
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0,
        }

    def create_dialogue_session(self) -> str:
        """创建新的对话会话"""
        session_id = str(uuid.uuid4())
        self.dialogue_contexts[session_id] = DialogueContext()
        return session_id

    def get_dialogue_context(self, session_id: str) -> Optional[DialogueContext]:
        """获取对话上下文"""
        return self.dialogue_contexts.get(session_id)

    async def process_input(self, session_id: str, input_text: str) -> Dict[str, Any]:
        """处理用户输入，支持多轮交互

        Args:
            session_id: 会话ID
            input_text: 用户输入文本

        Returns:
            处理结果，包括可能的澄清问题
        """
        context = self.get_dialogue_context(session_id)
        if not context:
            context = DialogueContext()
            self.dialogue_contexts[session_id] = context

        # 记录用户输入
        context.add_conversation_entry("user", input_text)

        try:
            # 如果当前需要澄清，这个输入是对之前问题的回答
            if context.needs_clarification:
                context.add_clarification(context.current_clarification, input_text)
                context.clear_clarification_state()

            # 1. 提取需求
            extraction_result = await self.agents["extractor"].process(
                {
                    "input_text": input_text,
                    "context": context.get_full_context(),
                }
            )

            # 检查提取是否成功
            if extraction_result.get("status") != "success":
                error_msg = extraction_result.get("error", "需求提取失败")
                return {
                    "needs_clarification": False,
                    "is_complete": False,
                    "error": error_msg,
                    "context": context.get_full_context(),
                }

            # 2. 获取需求信息
            requirements_data = extraction_result.get("requirements", {})

            # 3. 更新需求到上下文
            if requirements_data.get("functional_requirements"):
                for req in requirements_data["functional_requirements"]:
                    context.add_requirement(req)
            if requirements_data.get("non_functional_requirements"):
                for req in requirements_data["non_functional_requirements"]:
                    context.add_requirement(req)

            # 4. 简化逻辑：直接进行完整分析
            context.is_complete = True
            analysis_result = await self.analyze(input_text, context=context)
            context.current_analysis = analysis_result

            # 生成文档
            documentation = await self.generate_documentation(
                requirements={"requirements": context.requirements},
                analysis=analysis_result,
                context=context,
            )

            return {
                "needs_clarification": False,
                "is_complete": True,
                "analysis": analysis_result,
                "documentation": documentation,
                "context": context.get_full_context(),
            }

        except Exception as e:
            logger.error(f"处理输入失败: {str(e)}", exc_info=True)
            raise

    async def analyze(
        self, input_text: str, context: Optional[DialogueContext] = None
    ) -> Dict[str, Any]:
        """分析需求

        Args:
            input_text: 输入文本
            context: 可选的对话上下文

        Returns:
            分析结果
        """
        start_time = datetime.now()
        workflow_successful = False

        try:
            # 使用上下文中的需求或重新提取
            if context and context.requirements:
                requirements = {"requirements": context.requirements}
            else:
                extraction_result = await self.agents["extractor"].process(
                    {
                        "input_text": input_text,
                        "context": (context.get_full_context() if context else None),
                    }
                )
                if extraction_result.get("status") == "success":
                    requirements_data = extraction_result.get("requirements", {})
                    requirements = {"requirements": requirements_data}
                else:
                    raise Exception(
                        f"需求提取失败: {extraction_result.get('error', '未知错误')}"
                    )

            logger.info(f"需求提取完成，共 {len(requirements['requirements'])} 条需求")

            # 分析需求
            logger.info("开始需求分析...")
            analysis = await self.agents["analyzer"].process(
                {
                    "requirements": requirements,
                    "context": context.get_full_context() if context else None,
                }
            )
            logger.info("需求分析完成")

            _workflow_successful = True
            self._update_workflow_metrics(
                successful=workflow_successful,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

            return analysis

        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}", exc_info=True)
            self._update_workflow_metrics(
                successful=False,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )
            raise

    async def generate_documentation(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any],
        context: Optional[DialogueContext] = None,
    ) -> Dict[str, Any]:
        """生成文档

        Args:
            requirements: 需求数据
            analysis: 分析结果
            context: 可选的对话上下文

        Returns:
            生成的文档
        """
        try:
            # 质量检查
            logger.info("开始质量检查...")
            quality_report = await self.agents["checker"].process(
                {
                    "requirements": requirements,
                    "analysis": analysis,
                    "context": context.get_full_context() if context else None,
                }
            )
            logger.info("质量检查完成")

            # 生成文档
            logger.info("开始生成文档...")
            documentation = await self.agents["generator"].process(
                {
                    "requirements": requirements,
                    "analysis": analysis,
                    "quality_check": quality_report,
                    "context": context.get_full_context() if context else None,
                }
            )
            logger.info("文档生成完成")

            # 保存文档
            json_output_path = "output/requirements_document.json"
            Path(json_output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(documentation, f, ensure_ascii=False, indent=2)
            logger.info(f"需求文档已保存到: {json_output_path}")

            return documentation

        except Exception as e:
            logger.error(f"文档生成失败: {str(e)}", exc_info=True)
            raise

    def _update_workflow_metrics(
        self, successful: bool, processing_time: float
    ) -> None:
        """更新工作流指标。

        Args:
            successful: 工作流是否成功
            processing_time: 处理时间（秒）
        """
        self.metrics["total_workflows"] += 1
        if successful:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1

        # 更新平均处理时间
        current_total = self.metrics["average_workflow_time"] * (
            self.metrics["total_workflows"] - 1
        )
        new_average = (current_total + processing_time) / self.metrics[
            "total_workflows"
        ]
        self.metrics["average_workflow_time"] = new_average

    async def get_metrics(self) -> Dict[str, Any]:
        """获取当前工作流指标。

        Returns:
            当前指标
        """
        return {
            "total_workflows": self.metrics["total_workflows"],
            "successful_workflows": self.metrics["successful_workflows"],
            "failed_workflows": self.metrics["failed_workflows"],
            "success_rate": (
                self.metrics["successful_workflows"] / self.metrics["total_workflows"]
                if self.metrics["total_workflows"] > 0
                else 0
            ),
            "average_workflow_time": self.metrics["average_workflow_time"],
        }


class RequirementsCoordinator:
    """需求分析协调器"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.llm_factory = LLMManager(config.llm)
        self.extractor = RequirementsExtractor(config)
        self.analyzer = RequirementsAnalyzer(config)
        self._status = {"state": "ready", "progress": 0, "message": "准备就绪"}

    async def process(self, text: str) -> Dict[str, Any]:
        """处理需求文本"""
        try:
            # 更新状态
            self._update_status("extracting", 0, "正在提取需求...")

            # 提取需求
            requirements = await self.extractor.process(text)
            self._update_status("analyzing", 50, "正在分析需求...")

            # 分析需求
            analysis = await self.analyzer.analyze(requirements)
            self._update_status("completed", 100, "分析完成")

            return {
                "requirements": requirements,
                "analysis": analysis,
                "status": self._status,
            }

        except Exception as e:
            logging.error(f"需求处理失败: {str(e)}")
            self._update_status("error", 0, f"处理失败: {str(e)}")
            raise CoordinatorError(f"需求处理失败: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self._status

    def _update_status(self, state: str, progress: int, message: str) -> None:
        """更新状态"""
        self._status = {
            "state": state,
            "progress": progress,
            "message": message,
        }
        logging.info(f"状态更新: {message} ({progress}%)")
