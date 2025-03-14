# Import from the correct module path
from owl.utils import run_society
import os
import gradio as gr
import time
import json
import logging
import datetime
from typing import Tuple, List, Dict, Any
import importlib
from dotenv import load_dotenv, set_key, find_dotenv, unset_key
import threading
import queue
import time
import signal
import sys
import subprocess
import platform

os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志系统
def setup_logging():
    """配置日志系统，将日志输出到文件和内存队列"""
    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 生成日志文件名（使用当前日期）
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"gradio_log_{current_date}.txt")
    
    # 配置根日志记录器（捕获所有日志）
    root_logger = logging.getLogger()
    
    # 清除现有的处理器，避免重复日志
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到根日志记录器
    root_logger.addHandler(file_handler)
    

    
    logging.info("日志系统已初始化，日志文件: %s", log_file)
    return log_file

# 全局变量
LOG_FILE = None
LOG_QUEUE = queue.Queue()
STOP_LOG_THREAD = threading.Event()
CURRENT_PROCESS = None  # 用于跟踪当前运行的进程
STOP_REQUESTED = threading.Event()  # 用于标记是否请求停止
CONVERSATION_UPDATE_QUEUE = queue.Queue()  # 用于实时更新对话历史的队列

# 日志读取和更新函数
def log_reader_thread(log_file):
    """后台线程，持续读取日志文件并将新行添加到队列中"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            while not STOP_LOG_THREAD.is_set():
                line = f.readline()
                if line:
                    LOG_QUEUE.put(line)
                else:
                    # 没有新行，等待一小段时间
                    time.sleep(0.1)
    except Exception as e:
        logging.error(f"日志读取线程出错: {str(e)}")

def get_latest_logs(max_lines=100):
    """从队列中获取最新的日志行，如果队列为空则直接从文件读取
    
    Args:
        max_lines: 最大返回行数
        
    Returns:
        str: 日志内容
    """
    logs = []
    try:
        # 尝试从队列中获取所有可用的日志行
        while not LOG_QUEUE.empty() and len(logs) < max_lines:
            logs.append(LOG_QUEUE.get_nowait())
    except queue.Empty:
        pass
    
    # 如果没有新日志或日志不足，尝试直接从文件读取最后几行
    if len(logs) < max_lines and LOG_FILE and os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # 如果队列中已有一些日志，只读取剩余需要的行数
                remaining_lines = max_lines - len(logs)
                file_logs = all_lines[-remaining_lines:] if len(all_lines) > remaining_lines else all_lines
                # 将文件日志添加到队列日志之前
                logs = file_logs + logs
        except Exception as e:
            error_msg = f"读取日志文件出错: {str(e)}"
            logging.error(error_msg)
            if not logs:  # 只有在没有任何日志的情况下才添加错误消息
                logs = [error_msg]
    
    # 如果仍然没有日志，返回提示信息
    if not logs:
        return "暂无日志记录或日志系统未正确初始化。"
    
    return "".join(logs)

# Dictionary containing module descriptions
MODULE_DESCRIPTIONS = {
    "run": "默认模式：使用OpenAI模型的默认的智能体协作模式，适合大多数任务。",
    "run_mini":"使用使用OpenAI模型最小化配置处理任务",
    "run_deepseek_zh":"使用deepseek模型处理中文任务",
    "run_terminal_zh": "终端模式：可执行命令行操作，支持网络搜索、文件处理等功能。适合需要系统交互的任务，使用OpenAI模型",
    "run_gaia_roleplaying":"GAIA基准测试实现，用于评估Agent能力",
    "run_openai_compatiable_model":"使用openai兼容模型处理任务",
    "run_ollama":"使用本地ollama模型处理任务",
    "run_qwen_mini_zh":"使用qwen模型最小化配置处理任务",
    "run_qwen_zh":"使用qwen模型处理任务",
}

# API帮助信息
API_HELP_INFO = {
    "OPENAI_API_KEY": {
        "name": "OpenAI API",
        "desc": "OpenAI API密钥，用于访问GPT系列模型",
        "url": "https://platform.openai.com/api-keys"
    },
    "QWEN_API_KEY": {
        "name": "通义千问 API",
        "desc": "阿里云通义千问API密钥",
        "url": "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key"
    },
    "DEEPSEEK_API_KEY": {
        "name": "DeepSeek API",
        "desc": "DeepSeek API密钥",
        "url": "https://platform.deepseek.com/api_keys"
    },
    "GOOGLE_API_KEY": {
        "name": "Google Search API",
        "desc": "Google自定义搜索API密钥",
        "url": "https://developers.google.com/custom-search/v1/overview"
    },
    "SEARCH_ENGINE_ID": {
        "name": "Google Search Engine ID",
        "desc": "Google自定义搜索引擎ID",
        "url": "https://developers.google.com/custom-search/v1/overview"
    },
    "HF_TOKEN": {
        "name": "Hugging Face API",
        "desc": "Hugging Face API令牌",
        "url": "https://huggingface.co/join"
    },
    "CHUNKR_API_KEY": {
        "name": "Chunkr API",
        "desc": "Chunkr API密钥",
        "url": "https://chunkr.ai/"
    },
    "FIRECRAWL_API_KEY": {
        "name": "Firecrawl API",
        "desc": "Firecrawl API密钥",
        "url": "https://www.firecrawl.dev/"
    }
}

# 默认环境变量模板
DEFAULT_ENV_TEMPLATE = """# MODEL & API (See https://docs.camel-ai.org/key_modules/models.html#)

# OPENAI API
# OPENAI_API_KEY= ""
# OPENAI_API_BASE_URL=""

# Qwen API (https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key)
# QWEN_API_KEY=""

# DeepSeek API (https://platform.deepseek.com/api_keys)
# DEEPSEEK_API_KEY=""

#===========================================
# Tools & Services API
#===========================================

# Google Search API (https://developers.google.com/custom-search/v1/overview)
GOOGLE_API_KEY=""
SEARCH_ENGINE_ID=""

# Hugging Face API (https://huggingface.co/join)
HF_TOKEN=""

# Chunkr API (https://chunkr.ai/)
CHUNKR_API_KEY=""

# Firecrawl API (https://www.firecrawl.dev/)
FIRECRAWL_API_KEY=""
#FIRECRAWL_API_URL="https://api.firecrawl.dev"
"""

def format_chat_history(chat_history: List[Dict[str, str]]) -> List[List[str]]:
    """将聊天历史格式化为Gradio聊天组件可接受的格式
    
    Args:
        chat_history: 原始聊天历史
        
    Returns:
        List[List[str]]: 格式化后的聊天历史
    """
    formatted_history = []
    for message in chat_history:
        user_msg = message.get("user", "")
        assistant_msg = message.get("assistant", "")
        
        if user_msg:
            formatted_history.append([user_msg, None])
        if assistant_msg and formatted_history:
            formatted_history[-1][1] = assistant_msg
        elif assistant_msg:
            formatted_history.append([None, assistant_msg])
    
    return formatted_history

def validate_input(question: str) -> bool:
    """验证用户输入是否有效
    
    Args:
        question: 用户问题
        
    Returns:
        bool: 输入是否有效
    """
    # 检查输入是否为空或只包含空格
    if not question or question.strip() == "":
        return False
    return True

# 终止运行进程的函数
def terminate_process():
    """停止当前运行的线程，而不是终止整个进程"""
    global CURRENT_PROCESS, STOP_REQUESTED
    
    if CURRENT_PROCESS is None:
        logging.info("没有正在运行的线程")
        return "没有正在运行的线程", "<span class='status-indicator status-success'></span> 已就绪"
    
    try:
        STOP_REQUESTED.set()  # 设置停止标志
        logging.info("已设置停止标志，正在等待线程响应...")
        
        # 如果是线程，只需要设置标志让它自行停止
        if isinstance(CURRENT_PROCESS, threading.Thread) and CURRENT_PROCESS.is_alive():
            logging.info("等待线程处理停止请求...")
            # 不强制终止线程，只设置标志位让线程自行退出
            # 线程应该会定期检查STOP_REQUESTED标志
            return "已请求停止生成", "<span class='status-indicator status-warning'></span> 正在停止..."
        else:
            # 如果不是线程或线程已经不活跃，则重置状态
            CURRENT_PROCESS = None
            logging.info("线程已不活跃")
            return "线程已停止", "<span class='status-indicator status-success'></span> 已就绪"
    
    except Exception as e:
        logging.error(f"停止线程时出错: {str(e)}")
        return f"停止线程时出错: {str(e)}", f"<span class='status-indicator status-error'></span> 错误: {str(e)}"

def run_owl(question: str, example_module: str) -> Tuple[str, List[List[str]], str, str]:
    """运行OWL系统并返回结果
    
    Args:
        question: 用户问题
        example_module: 要导入的示例模块名（如 "run_terminal_zh" 或 "run_deep"）
        
    Returns:
        Tuple[...]: 回答、聊天历史、令牌计数、状态
    """
    global CURRENT_PROCESS, STOP_REQUESTED, CONVERSATION_UPDATE_QUEUE
    
    # 清空对话更新队列
    while not CONVERSATION_UPDATE_QUEUE.empty():
        try:
            CONVERSATION_UPDATE_QUEUE.get_nowait()
        except queue.Empty:
            break
    
    # 重置停止标志
    STOP_REQUESTED.clear()
    
    # 验证输入
    if not validate_input(question):
        logging.warning("用户提交了无效的输入")
        return (
            "请输入有效的问题", 
            [], 
            "0", 
            "❌ 错误: 输入无效"
        )
    
    try:
        # 确保环境变量已加载
        load_dotenv(find_dotenv(), override=True)
        logging.info(f"处理问题: '{question}', 使用模块: {example_module}")
        
        # 检查模块是否在MODULE_DESCRIPTIONS中
        if example_module not in MODULE_DESCRIPTIONS:
            logging.error(f"用户选择了不支持的模块: {example_module}")
            return (
                f"所选模块 '{example_module}' 不受支持", 
                [], 
                "0", 
                f"❌ 错误: 不支持的模块"
            )
            
        # 动态导入目标模块
        module_path = f"owl.examples.{example_module}"
        try:
            logging.info(f"正在导入模块: {module_path}")
            module = importlib.import_module(module_path)
        except ImportError as ie:
            logging.error(f"无法导入模块 {module_path}: {str(ie)}")
            return (
                f"无法导入模块: {module_path}", 
                [], 
                "0", 
                f"❌ 错误: 模块 {example_module} 不存在或无法加载 - {str(ie)}"
            )
        except Exception as e:
            logging.error(f"导入模块 {module_path} 时发生错误: {str(e)}")
            return (
                f"导入模块时发生错误: {module_path}", 
                [], 
                "0", 
                f"❌ 错误: {str(e)}"
            )
        
        # 检查是否包含construct_society函数
        if not hasattr(module, "construct_society"):
            logging.error(f"模块 {module_path} 中未找到 construct_society 函数")
            return (
                f"模块 {module_path} 中未找到 construct_society 函数", 
                [], 
                "0", 
                f"❌ 错误: 模块接口不兼容"
            )
            
        # 构建社会模拟
        try:
            logging.info("正在构建社会模拟...")
            society = module.construct_society(question)
            
            # 添加对话更新回调
            if hasattr(society, 'set_message_callback'):
                def message_callback(role, content):
                    """对话消息回调函数"""
                    try:
                        # 将消息添加到队列
                        CONVERSATION_UPDATE_QUEUE.put((role, content))
                        logging.info(f"对话回调: {role} - {content[:30]}...")
                    except Exception as e:
                        logging.error(f"对话回调处理错误: {str(e)}")
                
                # 设置回调
                society.set_message_callback(message_callback)
                logging.info("已设置对话更新回调")
        except Exception as e:
            logging.error(f"构建社会模拟时发生错误: {str(e)}")
            return (
                f"构建社会模拟时发生错误: {str(e)}", 
                [], 
                "0", 
                f"❌ 错误: 构建失败 - {str(e)}"
            )
        
        # 运行社会模拟
        try:
            logging.info("正在运行社会模拟...")
            answer, chat_history, token_info = run_society(society)
            logging.info("社会模拟运行完成")
        except Exception as e:
            logging.error(f"运行社会模拟时发生错误: {str(e)}")
            return (
                f"运行社会模拟时发生错误: {str(e)}", 
                [], 
                "0", 
                f"❌ 错误: 运行失败 - {str(e)}"
            )
        
        # 格式化聊天历史
        try:
            formatted_chat_history = format_chat_history(chat_history)
        except Exception as e:
            # 如果格式化失败，返回空历史记录但继续处理
            logging.error(f"格式化聊天历史时发生错误: {str(e)}")
            formatted_chat_history = []
        
        # 安全地获取令牌计数
        if not isinstance(token_info, dict):
            token_info = {}
            
        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens
        
        logging.info(f"处理完成，令牌使用: 完成={completion_tokens}, 提示={prompt_tokens}, 总计={total_tokens}")
        
        return (
            answer, 
            formatted_chat_history, 
            f"完成令牌: {completion_tokens:,} | 提示令牌: {prompt_tokens:,} | 总计: {total_tokens:,}", 
            "✅ 成功完成"
        )
        
    except Exception as e:
        logging.error(f"处理问题时发生未捕获的错误: {str(e)}")
        return (
            f"发生错误: {str(e)}", 
            [], 
            "0", 
            f"❌ 错误: {str(e)}"
        )

def update_module_description(module_name: str) -> str:
    """返回所选模块的描述"""
    return MODULE_DESCRIPTIONS.get(module_name, "无可用描述")

# 环境变量管理功能
def init_env_file():
    """初始化.env文件如果不存在"""
    dotenv_path = find_dotenv()
    if not dotenv_path:
        with open(".env", "w") as f:
            f.write(DEFAULT_ENV_TEMPLATE)
        dotenv_path = find_dotenv()
    return dotenv_path

def load_env_vars():
    """加载环境变量并返回字典格式"""
    dotenv_path = init_env_file()
    load_dotenv(dotenv_path, override=True)
    
    env_vars = {}
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars

def save_env_vars(env_vars):
    """保存环境变量到.env文件"""
    try:
        dotenv_path = init_env_file()
        
        # 保存每个环境变量
        for key, value in env_vars.items():
            if key and key.strip():  # 确保键不为空
                set_key(dotenv_path, key.strip(), value.strip())
        
        # 重新加载环境变量以确保生效
        load_dotenv(dotenv_path, override=True)
        
        return True, "环境变量已成功保存！"
    except Exception as e:
        return False, f"保存环境变量时出错: {str(e)}"

def add_env_var(key, value):
    """添加或更新单个环境变量"""
    try:
        if not key or not key.strip():
            return False, "变量名不能为空"
        
        dotenv_path = init_env_file()
        set_key(dotenv_path, key.strip(), value.strip())
        load_dotenv(dotenv_path, override=True)
        
        return True, f"环境变量 {key} 已成功添加/更新！"
    except Exception as e:
        return False, f"添加环境变量时出错: {str(e)}"

def delete_env_var(key):
    """删除环境变量"""
    try:
        if not key or not key.strip():
            return False, "变量名不能为空"
        
        dotenv_path = init_env_file()
        unset_key(dotenv_path, key.strip())
        
        # 从当前进程环境中也删除
        if key in os.environ:
            del os.environ[key]
        
        return True, f"环境变量 {key} 已成功删除！"
    except Exception as e:
        return False, f"删除环境变量时出错: {str(e)}"

def mask_sensitive_value(key: str, value: str) -> str:
    """对敏感信息进行掩码处理
    
    Args:
        key: 环境变量名
        value: 环境变量值
        
    Returns:
        str: 处理后的值
    """
    # 定义需要掩码的敏感关键词
    sensitive_keywords = ['key', 'token', 'secret', 'password', 'api']
    
    # 检查是否包含敏感关键词（不区分大小写）
    is_sensitive = any(keyword in key.lower() for keyword in sensitive_keywords)
    
    if is_sensitive and value:
        # 如果是敏感信息且有值，则显示掩码
        return '*' * 8
    return value

def update_env_table():
    """更新环境变量表格显示，对敏感信息进行掩码处理"""
    env_vars = load_env_vars()
    # 对敏感值进行掩码处理
    masked_env_vars = [[k, mask_sensitive_value(k, v)] for k, v in env_vars.items()]
    return masked_env_vars

def create_ui():
    """创建增强版Gradio界面"""
    
    # 定义日志更新函数
    def update_logs():
        """获取最新日志并返回给前端显示"""
        return get_latest_logs(100)
        
    def clear_log_file():
        """清空日志文件内容"""
        try:
            if LOG_FILE and os.path.exists(LOG_FILE):
                # 清空日志文件内容而不是删除文件
                open(LOG_FILE, 'w').close()
                logging.info("日志文件已清空")
                # 清空日志队列
                while not LOG_QUEUE.empty():
                    try:
                        LOG_QUEUE.get_nowait()
                    except queue.Empty:
                        break
                return "日志文件已清空"
            else:
                return "日志文件不存在或未设置"
        except Exception as e:
            logging.error(f"清空日志文件时出错: {str(e)}")
            return f"清空日志文件时出错: {str(e)}"
    
    # 创建一个实时日志更新函数
    def process_with_live_logs(question, module_name):
        """处理问题并实时更新日志和对话历史"""
        global CURRENT_PROCESS, STOP_REQUESTED, CONVERSATION_UPDATE_QUEUE
        
        # 重置停止标志
        STOP_REQUESTED.clear()
        
        # 创建一个后台线程来处理问题
        result_queue = queue.Queue()
        # 创建一个队列用于实时更新对话历史
        chat_history_queue = queue.Queue()
        
        # 初始化对话历史，添加用户问题
        current_chat_history = [[question, None]]
        
        # 创建一个函数来监听日志中的对话更新
        def monitor_logs_for_chat_updates():
            """监控日志中的对话更新并将其添加到队列中"""
            try:
                # 创建一个单独的日志队列用于监控对话
                chat_log_queue = queue.Queue()
                
                # 打开日志文件进行监控
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    # 移动到文件末尾
                    f.seek(0, 2)
                    
                    while not STOP_REQUESTED.is_set():
                        line = f.readline()
                        if line:
                            # 尝试多种模式来检测对话信息
                            
                            # 模式1: 检查标准的Agent对话格式
                            if "Agent:" in line and ":" in line.split("Agent:")[1]:
                                try:
                                    agent_part = line.split("Agent:")[1].strip()
                                    agent_name = agent_part.split(":")[0].strip()
                                    message = ":".join(agent_part.split(":")[1:]).strip()
                                    
                                    # 将对话信息添加到队列
                                    chat_history_queue.put((agent_name, message))
                                    logging.info(f"检测到对话更新(模式1): {agent_name} - {message[:30]}...")
                                except Exception as e:
                                    logging.error(f"解析对话信息时出错(模式1): {str(e)}")
                            
                            # 模式2: 检查包含角色名和消息的格式
                            elif " - " in line and any(role in line for role in ["用户", "助手", "系统", "User", "Assistant", "System"]):
                                try:
                                    parts = line.split(" - ", 1)
                                    if len(parts) >= 2:
                                        # 尝试提取角色名
                                        log_prefix = parts[0]
                                        message_part = parts[1]
                                        
                                        # 尝试从日志前缀中提取角色名
                                        role_candidates = ["用户", "助手", "系统", "User", "Assistant", "System"]
                                        agent_name = None
                                        for role in role_candidates:
                                            if role in log_prefix:
                                                agent_name = role
                                                break
                                        
                                        if agent_name and message_part.strip():
                                            chat_history_queue.put((agent_name, message_part.strip()))
                                            logging.info(f"检测到对话更新(模式2): {agent_name} - {message_part[:30]}...")
                                except Exception as e:
                                    logging.error(f"解析对话信息时出错(模式2): {str(e)}")
                            
                            # 模式3: 检查JSON格式的对话记录
                            elif '"role"' in line and '"content"' in line and ('"user"' in line.lower() or '"assistant"' in line.lower() or '"system"' in line.lower()):
                                try:
                                    # 尝试提取JSON部分
                                    json_start = line.find("{")
                                    json_end = line.rfind("}")
                                    
                                    if json_start >= 0 and json_end > json_start:
                                        json_str = line[json_start:json_end+1]
                                        message_data = json.loads(json_str)
                                        
                                        if "role" in message_data and "content" in message_data:
                                            agent_name = message_data["role"].capitalize()
                                            message = message_data["content"]
                                            
                                            chat_history_queue.put((agent_name, message))
                                            logging.info(f"检测到对话更新(模式3): {agent_name} - {message[:30]}...")
                                except Exception as e:
                                    # JSON解析错误是常见的，所以这里不记录为错误
                                    pass
                        else:
                            # 没有新行，等待一小段时间
                            time.sleep(0.1)
            except Exception as e:
                logging.error(f"对话监控线程出错: {str(e)}")
        
        def process_in_background():
            try:
                # 检查是否已请求停止
                if STOP_REQUESTED.is_set():
                    result_queue.put((f"操作已取消", [], "0", f"❌ 操作已取消"))
                    return
                
                result = run_owl(question, module_name)
                
                # 再次检查是否已请求停止
                if STOP_REQUESTED.is_set():
                    result_queue.put((f"操作已取消", [], "0", f"❌ 操作已取消"))
                    return
                    
                result_queue.put(result)
            except Exception as e:
                result_queue.put((f"发生错误: {str(e)}", [], "0", f"❌ 错误: {str(e)}"))
        
        # 启动对话监控线程
        chat_monitor_thread = threading.Thread(target=monitor_logs_for_chat_updates, daemon=True)
        chat_monitor_thread.start()
        
        # 启动后台处理线程
        bg_thread = threading.Thread(target=process_in_background)
        CURRENT_PROCESS = bg_thread  # 记录当前进程
        bg_thread.start()
        
        # 在等待处理完成的同时，每秒更新一次日志和对话历史
        while bg_thread.is_alive():
            # 检查是否已请求停止
            if STOP_REQUESTED.is_set():
                logs = get_latest_logs(100)
                yield "操作已取消", current_chat_history, "0", "<span class='status-indicator status-warning'></span> 正在停止...", logs
                break
            
            # 检查是否有新的对话更新（从日志解析）
            updated = False
            while not chat_history_queue.empty():
                try:
                    agent_name, message = chat_history_queue.get_nowait()
                    
                    # 如果是新的对话，添加到历史记录
                    if not current_chat_history or current_chat_history[-1][1] is not None:
                        # 添加新的对话条目
                        current_chat_history.append([f"[{agent_name}]", message])
                    else:
                        # 更新最后一个对话的回复
                        current_chat_history[-1][1] = message
                    
                    updated = True
                except queue.Empty:
                    break
            
            # 检查是否有新的对话更新（从回调机制）
            while not CONVERSATION_UPDATE_QUEUE.empty():
                try:
                    role, content = CONVERSATION_UPDATE_QUEUE.get_nowait()
                    
                    # 格式化角色名称
                    if role.lower() == "user":
                        role_display = "用户"
                    elif role.lower() == "assistant":
                        role_display = "助手"
                    else:
                        role_display = role
                    
                    # 如果是新的对话，添加到历史记录
                    if not current_chat_history or current_chat_history[-1][1] is not None:
                        # 添加新的对话条目
                        current_chat_history.append([f"[{role_display}]", content])
                    else:
                        # 更新最后一个对话的回复
                        current_chat_history[-1][1] = content
                    
                    updated = True
                    logging.info(f"从回调更新对话: {role_display} - {content[:30]}...")
                except queue.Empty:
                    break
            
            # 更新日志显示
            logs = get_latest_logs(100)
            
            # 如果有更新或者每秒都要更新，则yield新状态
            if updated or True:  # 始终更新，可以根据需要调整
                yield None, current_chat_history, None, "<span class='status-indicator status-running'></span> 处理中...", logs
            
            time.sleep(1)
        
        # 如果已请求停止但线程仍在运行
        if STOP_REQUESTED.is_set() and bg_thread.is_alive():
            # 不再强制join线程，让它自然结束
            logs = get_latest_logs(100)
            yield "生成已停止", current_chat_history, "0", "<span class='status-indicator status-warning'></span> 已停止生成", logs
            return
        
        # 处理完成，获取结果
        if not result_queue.empty():
            result = result_queue.get()
            answer, chat_history, token_count, status = result
            
            # 如果有完整的聊天历史，使用它替换我们的临时历史
            if chat_history and len(chat_history) > 0:
                # 但首先确保用户问题已包含在内
                if not any(item[0] == question for item in chat_history):
                    chat_history.insert(0, [question, None])
                current_chat_history = chat_history
            
            # 最后一次更新日志
            logs = get_latest_logs(100)
            
            # 根据状态设置不同的指示器
            if "错误" in status:
                status_with_indicator = f"<span class='status-indicator status-error'></span> {status}"
            else:
                status_with_indicator = f"<span class='status-indicator status-success'></span> {status}"
            
            yield answer, current_chat_history, token_count, status_with_indicator, logs
        else:
            logs = get_latest_logs(100)
            yield "操作已取消或未完成", current_chat_history, "0", "<span class='status-indicator status-error'></span> 已终止", logs
    
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
            gr.Markdown(
                """
                # 🦉 OWL 多智能体协作系统

                基于CAMEL框架开发的先进多智能体协作系统，旨在通过智能体协作解决复杂问题。
                """
            )
            
            # 添加自定义CSS
            gr.HTML("""
            <style>
            /* 聊天容器样式 */
            .chat-container .chatbot {
                height: 500px;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            /* 用户消息样式 */
            .chat-container .user-message {
                background-color: #e6f7ff;
                border-radius: 18px 18px 0 18px;
                padding: 10px 15px;
                margin: 5px 0;
            }
            
            /* 助手消息样式 */
            .chat-container .assistant-message {
                background-color: #f0f0f0;
                border-radius: 18px 18px 18px 0;
                padding: 10px 15px;
                margin: 5px 0;
            }
            
            /* 角色名称样式 */
            .chat-container .role-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            /* 改进标签页样式 */
            .tabs .tab-nav {
                background-color: #f5f5f5;
                border-radius: 8px 8px 0 0;
                padding: 5px;
            }
            
            .tabs .tab-nav button {
                border-radius: 5px;
                margin: 0 3px;
                padding: 8px 15px;
                font-weight: 500;
            }
            
            .tabs .tab-nav button.selected {
                background-color: #2c7be5;
                color: white;
            }
            
            /* 状态指示器样式 */
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .status-running {
                background-color: #ffc107;
                animation: pulse 1.5s infinite;
            }
            
            .status-success {
                background-color: #28a745;
            }
            
            .status-error {
                background-color: #dc3545;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
            </style>
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    question_input = gr.Textbox(
                        lines=5,
                        placeholder="请输入您的问题...",
                        label="问题",
                        elem_id="question_input",
                        show_copy_button=True,
                    )
                    
                    # 增强版模块选择下拉菜单
                    # 只包含MODULE_DESCRIPTIONS中定义的模块
                    module_dropdown = gr.Dropdown(
                        choices=list(MODULE_DESCRIPTIONS.keys()),
                        value="run_terminal_zh",
                        label="选择功能模块",
                        interactive=True
                    )
                    
                    # 模块描述文本框
                    module_description = gr.Textbox(
                        value=MODULE_DESCRIPTIONS["run_terminal_zh"],
                        label="模块描述",
                        interactive=False,
                        elem_classes="module-info"
                    )
                    
                    with gr.Row():
                        run_button = gr.Button("运行", variant="primary", elem_classes="primary")
                        stop_button = gr.Button("停止", variant="stop", elem_classes="stop")
                        
                    status_output = gr.HTML(
                        value="<span class='status-indicator status-success'></span> 已就绪",
                        label="状态"
                    )
                    token_count_output = gr.Textbox(
                        label="令牌计数", 
                        interactive=False,
                        elem_classes="token-count"
                    ) 
                
           
                
                with gr.Tabs():
                    with gr.TabItem("回答"):
                        answer_output = gr.Textbox(
                            label="回答", 
                            lines=10,
                            elem_classes="answer-box"
                        )
                    
                    with gr.TabItem("对话历史", id="chat-history-tab"):
                        chat_output = gr.Chatbot(
                            label="完整对话记录",
                            elem_classes="chat-container",
                            height=500,
                            avatar_images=("👤", "🦉"),  # 添加用户和助手的头像
                            bubble_full_width=False,     # 气泡不占满宽度
                            show_copy_button=True        # 显示复制按钮
                        )
                        
                        # 添加自动滚动到底部的JavaScript
                        gr.HTML("""
                        <script>
                        // 自动滚动聊天记录到底部
                        function scrollChatToBottom() {
                            const chatContainer = document.querySelector('.chat-container .chatbot');
                            if (chatContainer) {
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            }
                        }
                        
                        // 每秒检查并滚动
                        setInterval(scrollChatToBottom, 1000);
                        
                        // 监听标签页切换，当切换到对话历史标签时滚动到底部
                        document.addEventListener('click', function(e) {
                            if (e.target && e.target.closest('[id="chat-history-tab"]')) {
                                setTimeout(scrollChatToBottom, 100);
                            }
                        });
                        </script>
                        """)
                    
                    with gr.TabItem("系统日志"):
                        # 添加日志显示区域
                        log_display = gr.Textbox(
                            label="系统日志",
                            lines=20,
                            max_lines=50,
                            interactive=False,
                            autoscroll=True,
                            show_copy_button=True,
                            elem_classes="log-display"
                        )
                        
                        with gr.Row():
                            refresh_logs_button = gr.Button("刷新日志")
                            auto_refresh_checkbox = gr.Checkbox(
                                label="自动刷新", 
                                value=True,
                                interactive=True
                            )
                            clear_logs_button = gr.Button("清空日志", variant="secondary")
                    
                    with gr.TabItem("环境变量管理", id="env-settings"):
                        gr.Markdown("""
                        ## 环境变量管理
                        
                        在此处设置模型API密钥和其他服务凭证。这些信息将保存在本地的`.env`文件中，确保您的API密钥安全存储且不会上传到网络。
                        """)
                        
                        # 添加API密钥获取指南
                        gr.Markdown("### API密钥获取指南")
                        
                        for key, info in API_HELP_INFO.items():
                            with gr.Accordion(f"{info['name']} ({key})", open=False):
                                gr.Markdown(f"""
                                - **说明**: {info['desc']}
                                - **获取地址**: [{info['url']}]({info['url']})
                                """)
                        
                        gr.Markdown("---")
                        
                        # 环境变量表格
                        env_table = gr.Dataframe(
                            headers=["变量名", "值"],
                            datatype=["str", "str"],
                            row_count=10,
                            col_count=(2, "fixed"),
                            value=update_env_table,
                            label="当前环境变量",
                            interactive=False
                        )
                        
                        with gr.Row():
                            with gr.Column(scale=1):
                                new_env_key = gr.Textbox(label="变量名", placeholder="例如: OPENAI_API_KEY")
                            with gr.Column(scale=2):
                                new_env_value = gr.Textbox(label="值", placeholder="输入API密钥或其他配置值")
                        
                        with gr.Row():
                            add_env_button = gr.Button("添加/更新变量", variant="primary")
                            refresh_button = gr.Button("刷新变量列表")
                            delete_env_button = gr.Button("删除选定变量", variant="stop")
                        
                        env_status = gr.Textbox(label="状态", interactive=False)
                        
                        # 变量选择器（用于删除）
                        env_var_to_delete = gr.Dropdown(
                            choices=[], 
                            label="选择要删除的变量",
                            interactive=True
                        )
                        
                        # 更新变量选择器的选项
                        def update_delete_dropdown():
                            env_vars = load_env_vars()
                            return gr.Dropdown.update(choices=list(env_vars.keys()))
                        
                        # 连接事件处理函数
                        add_env_button.click(
                            fn=lambda k, v: add_env_var(k, v),
                            inputs=[new_env_key, new_env_value],
                            outputs=[env_status]
                        ).then(
                            fn=update_env_table,
                            outputs=[env_table]
                        ).then(
                            fn=update_delete_dropdown,
                            outputs=[env_var_to_delete]
                        ).then(
                            fn=lambda: ("", ""),  # 修改为返回两个空字符串的元组
                            outputs=[new_env_key, new_env_value]
                        )
                        
                        refresh_button.click(
                            fn=update_env_table,
                            outputs=[env_table]
                        ).then(
                            fn=update_delete_dropdown,
                            outputs=[env_var_to_delete]
                        )
                        
                        delete_env_button.click(
                            fn=lambda k: delete_env_var(k),
                            inputs=[env_var_to_delete],
                            outputs=[env_status]
                        ).then(
                            fn=update_env_table,
                            outputs=[env_table]
                        ).then(
                            fn=update_delete_dropdown,
                            outputs=[env_var_to_delete]
                        )
                            
                        
                
           
            
            # 示例问题
            examples = [
                "打开百度搜索，总结一下camel-ai的camel框架的github star、fork数目等，并把数字用plot包写成python文件保存到本地，用本地终端执行python文件显示图出来给我",
                "请分析GitHub上CAMEL-AI项目的最新统计数据。找出该项目的星标数量、贡献者数量和最近的活跃度。",
                "浏览亚马逊并找出一款对程序员有吸引力的产品。请提供产品名称和价格",
                "写一个hello world的python文件，保存到本地",
             
            ]
            
            gr.Examples(
                examples=examples, 
                inputs=question_input
            )
    



            
            gr.HTML("""
                <div class="footer" id="about">
                    <h3>关于 OWL 多智能体协作系统</h3>
                    <p>OWL 是一个基于CAMEL框架开发的先进多智能体协作系统，旨在通过智能体协作解决复杂问题。</p>
                    <p>© 2025 CAMEL-AI.org. 基于Apache License 2.0开源协议</p>
                    <p><a href="https://github.com/camel-ai/owl" target="_blank">GitHub</a></p>
                </div>
            """)
            
            # 设置事件处理
            run_button.click(
                fn=process_with_live_logs,
                inputs=[question_input, module_dropdown], 
                outputs=[answer_output, chat_output, token_count_output, status_output, log_display]
            )
            
            # 添加停止按钮事件处理
            stop_button.click(
                fn=terminate_process,
                outputs=[answer_output, status_output]
            )
            
            # 模块选择更新描述
            module_dropdown.change(
                fn=update_module_description,
                inputs=module_dropdown,
                outputs=module_description
            )
            
            # 日志相关事件处理
            refresh_logs_button.click(
                fn=update_logs,
                outputs=[log_display]
            )
            
            clear_logs_button.click(
                fn=clear_log_file,
                outputs=[log_display]
            )
            
            # 自动刷新控制
            def toggle_auto_refresh(enabled):
                if enabled:
                    return gr.update(every=3)
                else:
                    return gr.update(every=0)
            
            auto_refresh_checkbox.change(
                fn=toggle_auto_refresh,
                inputs=[auto_refresh_checkbox],
                outputs=[log_display]
            )
            
            # 设置自动刷新（默认每3秒刷新一次）
            if auto_refresh_checkbox.value:
                app.load(
                    fn=update_logs,
                    outputs=[log_display],
                    every=2
                )
    
    return app

# 主函数
def main():
    try:
        # 初始化日志系统
        global LOG_FILE
        LOG_FILE = setup_logging()
        logging.info("OWL Web应用程序启动")
        
        # 启动日志读取线程
        log_thread = threading.Thread(target=log_reader_thread, args=(LOG_FILE,), daemon=True)
        log_thread.start()
        logging.info("日志读取线程已启动")
        
        # 初始化.env文件（如果不存在）
        init_env_file()
        app = create_ui()
        
        # 注册应用关闭时的清理函数
        def cleanup():
            global STOP_LOG_THREAD, STOP_REQUESTED
            STOP_LOG_THREAD.set()
            STOP_REQUESTED.set()
            logging.info("应用程序关闭，停止日志线程")
            
        app.launch(share=False,enable_queue=True,server_name="127.0.0.1",server_port=7860)
    except Exception as e:
        logging.error(f"启动应用程序时发生错误: {str(e)}")
        print(f"启动应用程序时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 确保日志线程停止
        STOP_LOG_THREAD.set()
        STOP_REQUESTED.set()
        logging.info("应用程序关闭")

if __name__ == "__main__":
    main()