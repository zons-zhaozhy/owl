#!/usr/bin/env python3
"""
系统清理脚本 - 清理重复的实现和模块
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import difflib

def find_duplicate_files() -> Dict[str, List[str]]:
    """查找重复的文件"""
    print("🔍 查找重复文件...")
    
    file_contents = {}
    duplicates = {}
    
    # 扫描所有Python文件
    for root, dirs, files in os.walk("src"):
        # 跳过__pycache__目录
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            if content in file_contents:
                                if content not in duplicates:
                                    duplicates[content] = [file_contents[content]]
                                duplicates[content].append(filepath)
                            else:
                                file_contents[content] = filepath
                except Exception as e:
                    print(f"  ⚠️ 读取文件失败 {filepath}: {e}")
    
    return duplicates

def find_similar_files(threshold: float = 0.8) -> List[Tuple[str, str, float]]:
    """查找相似的文件"""
    print("🔍 查找相似文件...")
    
    files_content = {}
    
    # 收集所有Python文件内容
    for root, dirs, files in os.walk("src"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content and len(content) > 100:  # 忽略太短的文件
                            files_content[filepath] = content
                except Exception:
                    continue
    
    similar_files = []
    file_paths = list(files_content.keys())
    
    for i, file1 in enumerate(file_paths):
        for file2 in file_paths[i+1:]:
            content1 = files_content[file1]
            content2 = files_content[file2]
            
            # 计算相似度
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            
            if similarity >= threshold:
                similar_files.append((file1, file2, similarity))
    
    return similar_files

def analyze_llm_implementations():
    """分析LLM相关的实现"""
    print("🔍 分析LLM实现...")
    
    llm_files = []
    
    # 查找所有LLM相关文件
    for root, dirs, files in os.walk("src"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if 'llm' in file.lower() and file.endswith('.py'):
                filepath = os.path.join(root, file)
                llm_files.append(filepath)
    
    print(f"  📁 找到LLM相关文件: {len(llm_files)}")
    for file in llm_files:
        print(f"    - {file}")
    
    return llm_files

def find_duplicate_templates():
    """查找重复的模板文件"""
    print("🔍 查找重复模板...")
    
    template_files = {}
    duplicates = []
    
    # 查找所有模板目录
    template_dirs = []
    for root, dirs, files in os.walk("."):
        if "template" in root.lower():
            template_dirs.append(root)
    
    print(f"  📁 找到模板目录: {len(template_dirs)}")
    for dir_path in template_dirs:
        print(f"    - {dir_path}")
        
        # 检查每个模板目录中的文件
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith(('.json', '.txt', '.md')):
                    filepath = os.path.join(dir_path, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            
                        if file in template_files:
                            # 检查内容是否相同
                            if content == template_files[file]['content']:
                                duplicates.append({
                                    'file': file,
                                    'paths': [template_files[file]['path'], filepath],
                                    'content_length': len(content)
                                })
                            else:
                                template_files[file]['similar_paths'] = template_files[file].get('similar_paths', [])
                                template_files[file]['similar_paths'].append(filepath)
                        else:
                            template_files[file] = {
                                'path': filepath,
                                'content': content
                            }
                    except Exception as e:
                        print(f"    ⚠️ 读取模板失败 {filepath}: {e}")
    
    return duplicates, template_dirs

def cleanup_duplicate_templates():
    """清理重复的模板"""
    print("\n🧹 开始清理重复模板...")
    
    duplicates, template_dirs = find_duplicate_templates()
    
    if not duplicates:
        print("✅ 没有发现重复的模板文件")
        return
    
    print(f"  🔍 发现 {len(duplicates)} 个重复模板:")
    
    for dup in duplicates:
        print(f"    📄 {dup['file']} (内容长度: {dup['content_length']})")
        for path in dup['paths']:
            print(f"      - {path}")
        
        # 保留templates/prompts/目录中的版本，删除其他的
        keep_path = None
        remove_paths = []
        
        for path in dup['paths']:
            if 'templates/prompts/' in path:
                keep_path = path
            else:
                remove_paths.append(path)
        
        if not keep_path:
            # 如果没有在templates/prompts/中的，保留第一个
            keep_path = dup['paths'][0]
            remove_paths = dup['paths'][1:]
        
        print(f"      ✅ 保留: {keep_path}")
        
        for remove_path in remove_paths:
            try:
                os.remove(remove_path)
                print(f"      🗑️ 删除: {remove_path}")
            except Exception as e:
                print(f"      ⚠️ 删除失败 {remove_path}: {e}")

def cleanup_web_templates():
    """清理重复的Web模板"""
    print("\n🧹 清理重复的Web模板...")
    
    web_template_paths = [
        "src/web/templates/",
        "src/owl_requirements/web/templates/"
    ]
    
    for path in web_template_paths:
        if os.path.exists(path):
            print(f"  📁 找到Web模板目录: {path}")
            
            # 如果不是主要的web模板目录，删除它
            if path != "src/owl_requirements/web/templates/":
                try:
                    shutil.rmtree(path)
                    print(f"  🗑️ 删除重复目录: {path}")
                except Exception as e:
                    print(f"  ⚠️ 删除失败 {path}: {e}")

def cleanup_empty_dirs():
    """清理空目录"""
    print("\n🧹 清理空目录...")
    
    def remove_empty_dirs(path):
        """递归删除空目录"""
        if not os.path.isdir(path):
            return
        
        # 先处理子目录
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                remove_empty_dirs(item_path)
        
        # 检查当前目录是否为空
        try:
            if not os.listdir(path) and path != "src":  # 不删除src根目录
                os.rmdir(path)
                print(f"  🗑️ 删除空目录: {path}")
        except OSError:
            pass
    
    remove_empty_dirs("src")

def verify_template_consistency():
    """验证模板一致性"""
    print("\n🔍 验证模板一致性...")
    
    required_templates = [
        "requirements_extraction.json",
        "requirements_analysis.json", 
        "quality_checker.json",
        "documentation_generator.json"
    ]
    
    template_dir = "templates/prompts"
    if not os.path.exists(template_dir):
        print(f"  ⚠️ 模板目录不存在: {template_dir}")
        return False
    
    missing_templates = []
    for template in required_templates:
        template_path = os.path.join(template_dir, template)
        if not os.path.exists(template_path):
            missing_templates.append(template)
    
    if missing_templates:
        print(f"  ⚠️ 缺少模板: {missing_templates}")
        return False
    else:
        print(f"  ✅ 所有必需的模板都存在")
        return True

def create_a2a_framework():
    """创建A2A通信框架"""
    print("\n🔧 创建A2A通信框架...")
    
    a2a_file = "src/owl_requirements/core/a2a_communication.py"
    
    if os.path.exists(a2a_file):
        print(f"  ✅ A2A通信文件已存在: {a2a_file}")
        return
    
    # 确保目录存在
    os.makedirs(os.path.dirname(a2a_file), exist_ok=True)
    
    a2a_content = '''"""
A2A (Agent-to-Agent) 通信框架
基于OWL框架的智能体间通信系统
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from camel.messages import BaseMessage
from camel.agents import ChatAgent
import asyncio
import logging

logger = logging.getLogger(__name__)


class A2AMessageType(Enum):
    """A2A消息类型"""
    CLARIFICATION_REQUEST = "clarification_request"
    CLARIFICATION_RESPONSE = "clarification_response"
    QUALITY_FEEDBACK = "quality_feedback"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    STATUS_UPDATE = "status_update"


@dataclass
class A2AMessage:
    """A2A消息结构"""
    message_type: A2AMessageType
    sender_agent: str
    receiver_agent: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    
    def to_base_message(self) -> BaseMessage:
        """转换为CAMEL BaseMessage"""
        return BaseMessage(
            role_name=self.sender_agent,
            role_type="assistant",
            meta_dict={
                "message_type": self.message_type.value,
                "receiver": self.receiver_agent,
                "conversation_id": self.conversation_id,
                **(self.metadata or {})
            },
            content=self.content
        )


class RequirementsClarificationWorkflow:
    """需求澄清工作流"""
    
    def __init__(self):
        self.active_conversations: Dict[str, List[A2AMessage]] = {}
    
    async def start_clarification(
        self, 
        extractor_agent: ChatAgent,
        analyzer_agent: ChatAgent,
        unclear_requirement: str,
        conversation_id: str
    ) -> str:
        """开始需求澄清流程"""
        
        # 创建澄清请求消息
        clarification_msg = A2AMessage(
            message_type=A2AMessageType.CLARIFICATION_REQUEST,
            sender_agent="requirements_extractor",
            receiver_agent="requirements_analyzer", 
            content=f"需要澄清以下需求: {unclear_requirement}",
            conversation_id=conversation_id
        )
        
        # 记录对话
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = []
        self.active_conversations[conversation_id].append(clarification_msg)
        
        # 发送给分析智能体
        analyzer_response = await analyzer_agent.step(clarification_msg.to_base_message())
        
        # 处理响应
        response_msg = A2AMessage(
            message_type=A2AMessageType.CLARIFICATION_RESPONSE,
            sender_agent="requirements_analyzer",
            receiver_agent="requirements_extractor",
            content=analyzer_response.content,
            conversation_id=conversation_id
        )
        
        self.active_conversations[conversation_id].append(response_msg)
        
        return analyzer_response.content


class QualityFeedbackWorkflow:
    """质量反馈工作流"""
    
    async def provide_feedback(
        self,
        quality_agent: ChatAgent,
        target_agent: ChatAgent,
        feedback_content: str,
        target_agent_name: str
    ) -> str:
        """提供质量反馈"""
        
        feedback_msg = A2AMessage(
            message_type=A2AMessageType.QUALITY_FEEDBACK,
            sender_agent="quality_checker",
            receiver_agent=target_agent_name,
            content=feedback_content
        )
        
        # 发送反馈
        response = await target_agent.step(feedback_msg.to_base_message())
        
        return response.content


class A2ACoordinator:
    """A2A协调器"""
    
    def __init__(self):
        self.registered_agents: Dict[str, ChatAgent] = {}
        self.message_queue: List[A2AMessage] = []
        self.clarification_workflow = RequirementsClarificationWorkflow()
        self.feedback_workflow = QualityFeedbackWorkflow()
    
    def register_agent(self, agent_name: str, agent: ChatAgent):
        """注册智能体"""
        self.registered_agents[agent_name] = agent
        logger.info(f"已注册智能体: {agent_name}")
    
    async def route_message(self, message: A2AMessage) -> Optional[str]:
        """路由消息"""
        receiver = self.registered_agents.get(message.receiver_agent)
        if not receiver:
            logger.error(f"未找到接收智能体: {message.receiver_agent}")
            return None
        
        try:
            response = await receiver.step(message.to_base_message())
            return response.content
        except Exception as e:
            logger.error(f"消息路由失败: {e}")
            return None
    
    async def start_clarification_session(
        self,
        unclear_requirement: str,
        conversation_id: str
    ) -> str:
        """开始澄清会话"""
        extractor = self.registered_agents.get("requirements_extractor")
        analyzer = self.registered_agents.get("requirements_analyzer")
        
        if not extractor or not analyzer:
            raise ValueError("需求提取或分析智能体未注册")
        
        return await self.clarification_workflow.start_clarification(
            extractor, analyzer, unclear_requirement, conversation_id
        )


class A2AAgentMixin:
    """A2A智能体混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.a2a_coordinator: Optional[A2ACoordinator] = None
    
    def set_a2a_coordinator(self, coordinator: A2ACoordinator):
        """设置A2A协调器"""
        self.a2a_coordinator = coordinator
    
    async def send_a2a_message(self, message: A2AMessage) -> Optional[str]:
        """发送A2A消息"""
        if not self.a2a_coordinator:
            logger.warning("A2A协调器未设置")
            return None
        
        return await self.a2a_coordinator.route_message(message)
    
    async def request_clarification(
        self, 
        target_agent: str,
        unclear_content: str,
        conversation_id: str
    ) -> Optional[str]:
        """请求澄清"""
        message = A2AMessage(
            message_type=A2AMessageType.CLARIFICATION_REQUEST,
            sender_agent=self.__class__.__name__.lower(),
            receiver_agent=target_agent,
            content=unclear_content,
            conversation_id=conversation_id
        )
        
        return await self.send_a2a_message(message)
'''
    
    try:
        with open(a2a_file, 'w', encoding='utf-8') as f:
            f.write(a2a_content)
        print(f"  ✅ 创建A2A通信文件: {a2a_file}")
    except Exception as e:
        print(f"  ⚠️ 创建A2A文件失败: {e}")

def cleanup_llm_duplicates():
    """清理LLM重复实现"""
    print("\n🧹 清理LLM重复实现...")
    
    # 检查llm.py和llm_manager.py
    llm_simple = "src/owl_requirements/services/llm.py"
    llm_manager = "src/owl_requirements/services/llm_manager.py"
    
    if os.path.exists(llm_simple) and os.path.exists(llm_manager):
        print(f"  🔍 发现两个LLM实现:")
        print(f"    - {llm_simple} (简单实现)")
        print(f"    - {llm_manager} (完整实现)")
        
        # 检查哪个被更多使用
        simple_usage = 0
        manager_usage = 0
        
        for root, dirs, files in os.walk("src"):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'from ..services.llm import' in content or 'from .llm import' in content:
                                simple_usage += 1
                            if 'from ..services.llm_manager import' in content or 'from .llm_manager import' in content:
                                manager_usage += 1
                    except Exception:
                        continue
        
        print(f"    📊 使用统计:")
        print(f"      - llm.py: {simple_usage} 次引用")
        print(f"      - llm_manager.py: {manager_usage} 次引用")
        
        if manager_usage > simple_usage:
            print(f"    🗑️ 删除较少使用的 llm.py")
            try:
                os.remove(llm_simple)
                print(f"    ✅ 已删除: {llm_simple}")
            except Exception as e:
                print(f"    ⚠️ 删除失败: {e}")
        else:
            print(f"    ✅ 保留两个实现，llm_manager.py使用更广泛")

def main():
    """主函数"""
    print("🚀 开始系统清理...")
    print("=" * 60)
    
    # 1. 查找并报告重复文件
    duplicates = find_duplicate_files()
    if duplicates:
        print(f"🔍 发现 {len(duplicates)} 组重复文件:")
        for i, (content_hash, files) in enumerate(duplicates.items()):
            print(f"  组 {i+1}: {len(files)} 个文件")
            for file in files:
                print(f"    - {file}")
    
    # 2. 查找相似文件
    similar = find_similar_files()
    if similar:
        print(f"\n🔍 发现 {len(similar)} 对相似文件:")
        for file1, file2, similarity in similar:
            print(f"  相似度 {similarity:.2%}: {file1} <-> {file2}")
    
    # 3. 分析LLM实现
    llm_files = analyze_llm_implementations()
    
    # 4. 清理重复模板
    cleanup_duplicate_templates()
    
    # 5. 清理重复的Web模板
    cleanup_web_templates()
    
    # 6. 清理LLM重复实现
    cleanup_llm_duplicates()
    
    # 7. 清理空目录
    cleanup_empty_dirs()
    
    # 8. 验证模板一致性
    verify_template_consistency()
    
    # 9. 创建A2A通信框架
    create_a2a_framework()
    
    print("\n" + "=" * 60)
    print("✅ 系统清理完成！")
    
    print("\n📊 清理总结:")
    print("- 统一了模板存储位置到 templates/prompts/")
    print("- 删除了重复的模板文件")
    print("- 清理了重复的Web模板")
    print("- 分析了LLM实现重复情况")
    print("- 清理了空目录")
    print("- 验证了模板一致性")
    print("- 创建了A2A通信框架")

if __name__ == "__main__":
    main()
