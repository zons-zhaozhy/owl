import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import uuid

from loguru import logger

from ..agents.requirements_extractor import RequirementsExtractor
from ..agents.requirements_analyzer import RequirementsAnalyzer
from ..agents.quality_checker import QualityChecker
from ..agents.documentation_generator import DocumentationGenerator

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
        
    def add_clarification(self, question: Dict[str, Any], answer: str):
        """添加澄清记录
        
        Args:
            question: 包含问题详情的字典，格式为:
                {
                    "question": str,
                    "options": List[str],
                    "context": str
                }
            answer: 用户的回答
        """
        self.clarifications.append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_conversation_entry(self, role: str, content: str):
        """添加对话记录"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_full_context(self):
        """获取完整上下文"""
        return {
            "requirements": self.requirements,
            "clarifications": self.clarifications,
            "current_analysis": self.current_analysis,
            "conversation_history": self.conversation_history,
            "needs_clarification": self.needs_clarification,
            "current_clarification": self.current_clarification,
            "is_complete": self.is_complete
        }
        
    def set_needs_clarification(self, clarification: Dict[str, Any]):
        """设置需要澄清的状态
        
        Args:
            clarification: 澄清问题详情，格式为:
                {
                    "question": str,
                    "options": List[str],
                    "context": str
                }
        """
        self.needs_clarification = True
        self.current_clarification = clarification
        
    def clear_clarification_state(self):
        """清除澄清状态"""
        self.needs_clarification = False
        self.current_clarification = None

class AgentCoordinator:
    """Coordinates the multi-agent requirements analysis workflow."""
    
    def __init__(
        self,
        extractor: RequirementsExtractor,
        analyzer: RequirementsAnalyzer,
        checker: QualityChecker,
        generator: DocumentationGenerator
    ):
        """Initialize the coordinator.
        
        Args:
            extractor: Requirements extractor agent
            analyzer: Requirements analyzer agent
            checker: Quality checker agent
            generator: Documentation generator agent
        """
        self.extractor = extractor
        self.analyzer = analyzer
        self.checker = checker
        self.generator = generator
        self.dialogue_contexts = {}  # 存储多个会话的上下文
        
        # Workflow metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0
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
            extraction_result = await self.extractor.extract(
                input_text, 
                context=context.get_full_context()
            )
            
            # 2. 检查是否需要澄清
            if "clarification_needed" in extraction_result:
                clarification = extraction_result["clarification_needed"]
                context.set_needs_clarification(clarification)
                
                # 构造友好的澄清响应
                response = {
                    "needs_clarification": True,
                    "clarification": {
                        "question": clarification["question"],
                        "options": clarification.get("options", []),
                        "context": clarification.get("context", ""),
                        "type": "choice" if clarification.get("options") else "text"
                    },
                    "context": context.get_full_context()
                }
                
                context.add_conversation_entry(
                    "assistant",
                    f"需要澄清: {clarification['question']}\n" +
                    (f"背景: {clarification['context']}\n" if clarification.get("context") else "") +
                    (f"选项:\n" + "\n".join(f"- {opt}" for opt in clarification["options"]) if clarification.get("options") else "")
                )
                
                return response
                
            # 3. 更新需求
            if "requirements" in extraction_result:
                for req in extraction_result["requirements"]:
                    context.add_requirement(req)
                    
            # 4. 如果需求完整，进行分析
            if extraction_result.get("requirements_complete", False):
                context.is_complete = True
                analysis_result = await self.analyze(input_text, context=context)
                context.current_analysis = analysis_result
                
                # 生成文档
                documentation = await self.generate_documentation(
                    requirements={"requirements": context.requirements},
                    analysis=analysis_result,
                    context=context
                )
                
                return {
                    "needs_clarification": False,
                    "is_complete": True,
                    "analysis": analysis_result,
                    "documentation": documentation,
                    "context": context.get_full_context()
                }
                
            return {
                "needs_clarification": False,
                "is_complete": False,
                "status": "requirements_updated",
                "context": context.get_full_context()
            }
            
        except Exception as e:
            logger.error(f"处理输入失败: {str(e)}", exc_info=True)
            raise

    async def analyze(self, input_text: str, context: Optional[DialogueContext] = None) -> Dict[str, Any]:
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
                requirements = await self.extractor.extract(input_text, context=context.get_full_context() if context else None)
                
            logger.info(f"需求提取完成，共 {len(requirements['requirements'])} 条需求")
            
            # Step 2: Analyze requirements
            logger.info("开始需求分析...")
            analysis = await self.analyzer.analyze(requirements, context=context.get_full_context() if context else None)
            logger.info("需求分析完成")
            
            workflow_successful = True
            self._update_workflow_metrics(
                successful=workflow_successful,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}", exc_info=True)
            self._update_workflow_metrics(
                successful=False,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            raise
            
    async def generate_documentation(
        self,
        requirements: Dict[str, Any],
        analysis: Dict[str, Any],
        context: Optional[DialogueContext] = None
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
            # Step 1: Check quality
            logger.info("开始质量检查...")
            quality_report = await self.checker.check(
                requirements,
                analysis,
                context=context.get_full_context() if context else None
            )
            logger.info("质量检查完成")
            
            # Step 2: Generate documentation
            logger.info("开始生成文档...")
            documentation = await self.generator.generate(
                requirements=requirements,
                analysis=analysis,
                quality_check=quality_report,
                context=context.get_full_context() if context else None
            )
            logger.info("文档生成完成")
            
            # Step 3: Save documentation
            json_output_path = "output/requirements_document.json"
            await self.generator.save_documentation(documentation, json_output_path)
            logger.info(f"需求文档已保存到: {json_output_path}")
            
            return documentation
            
        except Exception as e:
            logger.error(f"文档生成失败: {str(e)}", exc_info=True)
            raise
            
    def _update_workflow_metrics(
        self,
        successful: bool,
        processing_time: float
    ) -> None:
        """Update workflow metrics.
        
        Args:
            successful: Whether the workflow was successful
            processing_time: Time taken to process the workflow
        """
        self.metrics["total_workflows"] += 1
        if successful:
            self.metrics["successful_workflows"] += 1
        else:
            self.metrics["failed_workflows"] += 1
            
        # Update average processing time
        current_total = (self.metrics["average_workflow_time"] * 
                        (self.metrics["total_workflows"] - 1))
        new_average = (current_total + processing_time) / self.metrics["total_workflows"]
        self.metrics["average_workflow_time"] = new_average
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics.
        
        Returns:
            Current metrics
        """
        return {
            "total_workflows": self.metrics["total_workflows"],
            "successful_workflows": self.metrics["successful_workflows"],
            "failed_workflows": self.metrics["failed_workflows"],
            "success_rate": (self.metrics["successful_workflows"] / 
                           self.metrics["total_workflows"] if self.metrics["total_workflows"] > 0 else 0),
            "average_workflow_time": self.metrics["average_workflow_time"]
        }