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
    
    # 配置CAMEL日志系统（如果可用）
    try:
        from camel.logger import set_log_file, set_log_level, enable_logging
        # 启用CAMEL日志
        enable_logging()
        # 设置CAMEL日志文件为同一个文件
        set_log_file(log_file)
        # 设置日志级别
        set_log_level("INFO")
        logging.info("CAMEL日志系统已配置")
    except ImportError:
        logging.warning("无法导入CAMEL日志模块，将只使用Python标准日志")
    except Exception as e:
        logging.warning(f"配置CAMEL日志时出错: {str(e)}")
    
    # 配置第三方库的日志级别
    for logger_name in ['urllib3', 'requests', 'gradio']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    logging.info("日志系统已初始化，日志文件: %s", log_file)
    return log_file

# 全局变量
LOG_FILE = None
LOG_QUEUE = queue.Queue()
STOP_LOG_THREAD = threading.Event()

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

def run_owl(question: str, example_module: str) -> Tuple[str, List[List[str]], str, str]:
    """运行OWL系统并返回结果
    
    Args:
        question: 用户问题
        example_module: 要导入的示例模块名（如 "run_terminal_zh" 或 "run_deep"）
        
    Returns:
        Tuple[...]: 回答、聊天历史、令牌计数、状态
    """
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
        
    def clear_log_display():
        """清空日志显示"""
        return ""
    
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
       
            
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
                    
                    run_button = gr.Button("运行", variant="primary", elem_classes="primary")
                        
                    status_output = gr.Textbox(label="状态", interactive=False)
                    token_count_output = gr.Textbox(
                        label="令牌计数", 
                        interactive=False,
                        elem_classes="token-count"
                    ) 
                
           
                
                with gr.Tabs(scale=2):
                    with gr.TabItem("回答"):
                        answer_output = gr.Textbox(
                            label="回答", 
                            lines=10,
                            elem_classes="answer-box"
                        )
                    
                    with gr.TabItem("对话历史"):
                        chat_output = gr.Chatbot(
                            label="完整对话记录",
                            elem_classes="chat-container",
                            height=500
                        )
                    
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
                            clear_logs_button = gr.Button("清空显示", variant="secondary")
                    
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
                fn=run_owl,
                inputs=[question_input, module_dropdown], 
                outputs=[answer_output, chat_output, token_count_output, status_output]
            ).then(
                fn=update_logs,  # 任务完成后自动更新日志
                outputs=[log_display]
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
                fn=clear_log_display,
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
                    every=3
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
            STOP_LOG_THREAD.set()
            logging.info("应用程序关闭，停止日志线程")
            
        app.launch(share=False)
    except Exception as e:
        logging.error(f"启动应用程序时发生错误: {str(e)}")
        print(f"启动应用程序时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 确保日志线程停止
        STOP_LOG_THREAD.set()
        logging.info("应用程序关闭")

if __name__ == "__main__":
    main()