from typing import Any
from typing import Dict
from typing import List
from typing import Optional

"""
A2A (Agent-to-Agent) Communication Framework for OWL
基于OWL/CAMEL框架的智能体间通信系统

符合OWL框架规范：
- 基于CAMEL的ChatAgent架构
- 使用BaseMessage进行消息传递
- 集成RolePlaying社会结构
- 支持工具包系统
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import logging

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.societies import RolePlaying

logger = logging.getLogger(__name__)


class A2AMessageType(Enum):
    """A2A消息类型"""

    _CLARIFICATION_REQUEST = "clarification_request"  # 澄清请求
    _CLARIFICATION_RESPONSE = "clarification_response"  # 澄清响应
    _QUALITY_FEEDBACK = "quality_feedback"  # 质量反馈
    _COLLABORATION_REQUEST = "collaboration_request"  # 协作请求
    _COLLABORATION_RESPONSE = "collaboration_response"  # 协作响应
    _WORKFLOW_UPDATE = "workflow_update"  # 工作流更新


class A2AWorkflowType(Enum):
    """A2A工作流类型"""

    _REQUIREMENTS_CLARIFICATION = "requirements_clarification"
    _QUALITY_IMPROVEMENT = "quality_improvement"
    _COLLABORATIVE_ANALYSIS = "collaborative_analysis"


@dataclass
class A2AMessage:
    """A2A消息结构 - 基于CAMEL BaseMessage"""

    message_type: A2AMessageType
    workflow_id: str
    sender_agent: str
    receiver_agent: str
    content: Dict[str, Any]
    timestamp: str = None
    correlation_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())

    def to_base_message(self, role_name: str = "user") -> BaseMessage:
        """转换为CAMEL BaseMessage"""
        content = """
A2A消息：
类型：{self.message_type.value}
工作流：{self.workflow_id}
发送者：{self.sender_agent}
内容：{json.dumps(self.content, ensure_ascii=False, indent=2)}
"""
        return BaseMessage.make_user_message(role_name=role_name, content=content)


class RequirementsClarificationWorkflow:
    """需求澄清工作流 - A2A的核心应用场景"""

    def __init__(self, extractor_agent: ChatAgent, analyzer_agent: ChatAgent):
        self.extractor_agent = extractor_agent
        self.analyzer_agent = analyzer_agent
        self.workflow_id = str(uuid.uuid4())
        self.clarification_history: List[A2AMessage] = []
        self.status = "initialized"

    async def start_clarification(
        self, unclear_requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """启动需求澄清流程"""
        logger.info(f"启动需求澄清工作流: {self.workflow_id}")

        # 创建澄清请求消息
        clarification_request = A2AMessage(
            message_type=A2AMessageType.CLARIFICATION_REQUEST,
            workflow_id=self.workflow_id,
            sender_agent="requirements_extractor",
            receiver_agent="requirements_analyzer",
            content={
                "unclear_requirements": unclear_requirements,
                "clarification_needed": [
                    "请分析这些需求的完整性",
                    "识别可能的歧义和缺失信息",
                    "提供具体的澄清建议",
                ],
            },
        )

        self.clarification_history.append(clarification_request)

        # 将A2A消息转换为BaseMessage并发送给分析智能体
        base_message = clarification_request.to_base_message("user")

        try:
            # 使用分析智能体处理澄清请求
            analyzer_response = await self.analyzer_agent.astep(base_message)

            if analyzer_response.msgs:
                # 解析分析智能体的响应
                response_content = analyzer_response.msgs[0].content
                clarification_suggestions = self._parse_clarification_response(
                    response_content
                )

                # 创建澄清响应消息
                clarification_response = A2AMessage(
                    message_type=A2AMessageType.CLARIFICATION_RESPONSE,
                    workflow_id=self.workflow_id,
                    sender_agent="requirements_analyzer",
                    receiver_agent="requirements_extractor",
                    content=clarification_suggestions,
                    _correlation_id=clarification_request.correlation_id,
                )

                self.clarification_history.append(clarification_response)
                self.status = "clarification_provided"

                return {
                    "workflow_id": self.workflow_id,
                    "status": self.status,
                    "clarification_suggestions": clarification_suggestions,
                    "conversation_history": [
                        asdict(msg) for msg in self.clarification_history
                    ],
                }

        except Exception as e:
            logger.error(f"澄清工作流出错: {e}")
            self.status = "error"
            return {
                "workflow_id": self.workflow_id,
                "status": self.status,
                "error": str(e),
            }

    def _parse_clarification_response(self, response_content: str) -> Dict[str, Any]:
        """解析澄清响应内容"""
        try:
            # 尝试从响应中提取JSON
            import re

            json_match = re.search(r"\{[\s\S]*\}", response_content)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果没有JSON，返回文本分析
                return {
                    "clarification_type": "text_analysis",
                    "suggestions": response_content,
                    "recommended_actions": [
                        "请根据分析建议补充需求细节",
                        "明确业务场景和用户故事",
                        "定义验收标准",
                    ],
                }
        except Exception as e:
            logger.warning(f"解析澄清响应失败: {e}")
            return {
                "clarification_type": "fallback",
                "suggestions": response_content,
                "parsing_error": str(e),
            }


class QualityFeedbackWorkflow:
    """质量反馈工作流"""

    def __init__(self, checker_agent: ChatAgent, target_agent: ChatAgent):
        self.checker_agent = checker_agent
        self.target_agent = target_agent
        self.workflow_id = str(uuid.uuid4())
        self.feedback_history: List[A2AMessage] = []

    async def provide_quality_feedback(
        self, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提供质量反馈"""
        logger.info(f"启动质量反馈工作流: {self.workflow_id}")

        # 创建质量反馈消息
        feedback_message = A2AMessage(
            _message_type=A2AMessageType.QUALITY_FEEDBACK,
            workflow_id=self.workflow_id,
            _sender_agent="quality_checker",
            _receiver_agent="target_agent",
            content={
                "analysis_results": analysis_results,
                "feedback_request": "请评估分析质量并提供改进建议",
            },
        )

        self.feedback_history.append(feedback_message)

        # 转换为BaseMessage并处理
        _base_message = feedback_message.to_base_message("user")

        try:
            checker_response = await self.checker_agent.astep(base_message)

            if checker_response.msgs:
                feedback_content = checker_response.msgs[0].content
                quality_assessment = self._parse_quality_feedback(feedback_content)

                return {
                    "workflow_id": self.workflow_id,
                    "quality_assessment": quality_assessment,
                    "feedback_provided": True,
                }

        except Exception as e:
            logger.error(f"质量反馈工作流出错: {e}")
            return {
                "workflow_id": self.workflow_id,
                "error": str(e),
                "feedback_provided": False,
            }

    def _parse_quality_feedback(self, feedback_content: str) -> Dict[str, Any]:
        """解析质量反馈内容"""
        return {
            "feedback_type": "quality_assessment",
            "content": feedback_content,
            "timestamp": datetime.now().isoformat(),
        }


class A2ACoordinator:
    """A2A协调器 - 管理智能体间的协作"""

    def __init__(self):
        self.active_workflows: Dict[str, Any] = {}
        self.agents: Dict[str, ChatAgent] = {}
        self.workflow_history: List[Dict[str, Any]] = []

    def register_agent(self, agent_name: str, agent: ChatAgent):
        """注册智能体"""
        self.agents[agent_name] = agent
        logger.info(f"注册智能体: {agent_name}")

    async def start_clarification_workflow(
        self,
        extractor_name: str,
        analyzer_name: str,
        unclear_requirements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """启动澄清工作流"""
        if extractor_name not in self.agents or analyzer_name not in self.agents:
            raise ValueError("智能体未注册")

        workflow = RequirementsClarificationWorkflow(
            self.agents[extractor_name], self.agents[analyzer_name]
        )

        self.active_workflows[workflow.workflow_id] = workflow

        result = await workflow.start_clarification(unclear_requirements)
        self.workflow_history.append(result)

        return result

    async def start_quality_feedback_workflow(
        self,
        checker_name: str,
        target_name: str,
        analysis_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """启动质量反馈工作流"""
        if checker_name not in self.agents or target_name not in self.agents:
            raise ValueError("智能体未注册")

        workflow = QualityFeedbackWorkflow(
            self.agents[checker_name], self.agents[target_name]
        )

        self.active_workflows[workflow.workflow_id] = workflow

        result = await workflow.provide_quality_feedback(analysis_results)
        self.workflow_history.append(result)

        return result

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "type": type(workflow).__name__,
                "status": getattr(workflow, "status", "unknown"),
            }
        return None

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """获取所有工作流历史"""
        return self.workflow_history


class A2AAgentMixin:
    """A2A智能体混入类 - 为基于CAMEL的智能体添加A2A能力"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a2a_coordinator: Optional[A2ACoordinator] = None
        self.agent_name = getattr(self, "name", self.__class__.__name__)

    def set_a2a_coordinator(self, coordinator: A2ACoordinator):
        """设置A2A协调器"""
        self.a2a_coordinator = coordinator
        coordinator.register_agent(self.agent_name, self)
        logger.info(f"智能体 {self.agent_name} 已连接到A2A协调器")

    async def request_clarification(
        self, target_agent: str, unclear_requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """请求澄清"""
        if not self.a2a_coordinator:
            raise RuntimeError("A2A协调器未设置")

        return await self.a2a_coordinator.start_clarification_workflow(
            self.agent_name, target_agent, unclear_requirements
        )

    async def provide_quality_feedback(
        self, target_agent: str, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提供质量反馈"""
        if not self.a2a_coordinator:
            raise RuntimeError("A2A协调器未设置")

        return await self.a2a_coordinator.start_quality_feedback_workflow(
            self.agent_name, target_agent, analysis_results
        )


# 全局A2A协调器实例
_a2a_coordinator_instance: Optional[A2ACoordinator] = None


def get_a2a_coordinator() -> A2ACoordinator:
    """获取全局A2A协调器实例"""
    global _a2a_coordinator_instance
    if _a2a_coordinator_instance is None:
        _a2a_coordinator_instance = A2ACoordinator()
    return _a2a_coordinator_instance


async def initialize_a2a_system():
    """初始化A2A通信系统"""
    coordinator = get_a2a_coordinator()
    logger.info("A2A通信系统已初始化（基于OWL/CAMEL框架）")
    return coordinator


# 使用示例和集成指南


class A2AIntegrationExample:
    """A2A集成示例"""

    @staticmethod
    async def example_requirements_clarification():
        """需求澄清示例"""
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        # 创建智能体（基于CAMEL框架）
        model = ModelFactory.create(
            _model_platform=ModelPlatformType.OPENAI, model_type="gpt-3.5-turbo"
        )

        extractor_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="requirements_extractor", content="你是需求提取专家"
            ),
            model=model,
        )

        analyzer_agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                _role_name="requirements_analyzer", content="你是需求分析专家"
            ),
            model=model,
        )

        # 初始化A2A系统
        coordinator = await initialize_a2a_system()
        coordinator.register_agent("extractor", extractor_agent)
        coordinator.register_agent("analyzer", analyzer_agent)

        # 启动澄清工作流
        unclear_requirements = [
            {
                "requirement": "系统应该快速响应",
                "clarity_issue": "未定义具体的响应时间标准",
            }
        ]

        result = await coordinator.start_clarification_workflow(
            "extractor", "analyzer", unclear_requirements
        )

        return result
