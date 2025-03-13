# Import from the correct module path
from owl.utils import run_society
import os
import gradio as gr
from typing import Tuple, List, Dict, Any
import importlib

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Enhanced CSS with navigation bar and additional styling
custom_css = """
:root {
    --primary-color: #4a89dc;
    --secondary-color: #5d9cec;
    --accent-color: #7baaf7;
    --light-bg: #f8f9fa;
    --border-color: #e4e9f0;
    --text-muted: #8a9aae;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 30px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    color: white;
    border-radius: 10px 10px 0 0;
    margin-bottom: 0;
    box-shadow: 0 2px 10px rgba(74, 137, 220, 0.15);
}

.navbar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.5em;
    font-weight: bold;
}

.navbar-menu {
    display: flex;
    gap: 20px;
}

/* Navbar styles moved to a more specific section below */

.header {
    text-align: center;
    margin-bottom: 20px;
    background: linear-gradient(180deg, var(--secondary-color), var(--accent-color));
    color: white;
    padding: 40px 20px;
    border-radius: 0 0 10px 10px;
    box-shadow: 0 4px 6px rgba(93, 156, 236, 0.12);
}

.module-info {
    background-color: var(--light-bg);
    border-left: 5px solid var(--primary-color);
    padding: 10px 15px;
    margin-top: 10px;
    border-radius: 5px;
    font-size: 0.9em;
}

.answer-box {
    background-color: var(--light-bg);
    border-left: 5px solid var(--secondary-color);
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.token-count {
    background-color: #e9ecef;
    padding: 10px;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
    margin-bottom: 20px;
}

.chat-container {
    border: 1px solid var(--border-color);
    border-radius: 5px;
    max-height: 500px;
    overflow-y: auto;
    margin-bottom: 20px;
}

.footer {
    text-align: center;
    margin-top: 20px;
    color: var(--text-muted);
    font-size: 0.9em;
    padding: 20px;
    border-top: 1px solid var(--border-color);
}

.features-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin: 20px 0;
}

@media (max-width: 1200px) {
    .features-section {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .features-section {
        grid-template-columns: 1fr;
    }
}

.feature-card {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(74, 137, 220, 0.08);
    transition: transform 0.3s, box-shadow 0.3s;
    height: 100%;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(228, 233, 240, 0.6);
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(74, 137, 220, 0.15);
    border-color: rgba(93, 156, 236, 0.3);
}

.feature-icon {
    font-size: 2em;
    color: var(--primary-color);
    margin-bottom: 10px;
    text-shadow: 0 1px 2px rgba(74, 137, 220, 0.1);
}

.feature-card h3 {
    margin-top: 10px;
    margin-bottom: 10px;
}

.feature-card p {
    flex-grow: 1;
    font-size: 0.95em;
    line-height: 1.5;
}

/* Navbar link styles - ensuring consistent colors */
.navbar-menu a {
    color: #ffffff !important;
    text-decoration: none;
    padding: 5px 10px;
    border-radius: 5px;
    transition: background-color 0.3s, color 0.3s;
    font-weight: 500;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.navbar-menu a:hover {
    background-color: rgba(255, 255, 255, 0.15);
    color: #ffffff !important;
}

/* Improved button and input styles */
button.primary {
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    transition: all 0.3s;
}

button.primary:hover {
    background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(74, 137, 220, 0.2);
}
"""

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
        return (
            "请输入有效的问题", 
            [], 
            "0", 
            "❌ 错误: 输入无效"
        )
    
    try:
        # 检查模块是否在MODULE_DESCRIPTIONS中
        if example_module not in MODULE_DESCRIPTIONS:
            return (
                f"所选模块 '{example_module}' 不受支持", 
                [], 
                "0", 
                f"❌ 错误: 不支持的模块"
            )
            
        # 动态导入目标模块
        module_path = f"owl.examples.{example_module}"
        try:
            module = importlib.import_module(module_path)
        except ImportError as ie:
            return (
                f"无法导入模块: {module_path}", 
                [], 
                "0", 
                f"❌ 错误: 模块 {example_module} 不存在或无法加载 - {str(ie)}"
            )
        except Exception as e:
            return (
                f"导入模块时发生错误: {module_path}", 
                [], 
                "0", 
                f"❌ 错误: {str(e)}"
            )
        
        # 检查是否包含construct_society函数
        if not hasattr(module, "construct_society"):
            return (
                f"模块 {module_path} 中未找到 construct_society 函数", 
                [], 
                "0", 
                f"❌ 错误: 模块接口不兼容"
            )
            
        # 构建社会模拟
        try:
            society = module.construct_society(question)
        except Exception as e:
            return (
                f"构建社会模拟时发生错误: {str(e)}", 
                [], 
                "0", 
                f"❌ 错误: 构建失败 - {str(e)}"
            )
        
        # 运行社会模拟
        try:
            answer, chat_history, token_info = run_society(society)
        except Exception as e:
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
            formatted_chat_history = []
        
        # 安全地获取令牌计数
        if not isinstance(token_info, dict):
            token_info = {}
            
        completion_tokens = token_info.get("completion_token_count", 0)
        prompt_tokens = token_info.get("prompt_token_count", 0)
        total_tokens = completion_tokens + prompt_tokens
        
        return (
            answer, 
            formatted_chat_history, 
            f"完成令牌: {completion_tokens:,} | 提示令牌: {prompt_tokens:,} | 总计: {total_tokens:,}", 
            "✅ 成功完成"
        )
        
    except Exception as e:
        return (
            f"发生错误: {str(e)}", 
            [], 
            "0", 
            f"❌ 错误: {str(e)}"
        )

def update_module_description(module_name: str) -> str:
    """返回所选模块的描述"""
    return MODULE_DESCRIPTIONS.get(module_name, "无可用描述")

def create_ui():
    """创建增强版Gradio界面"""
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft(primary_hue="blue")) as app:
        with gr.Column(elem_classes="container"):
            gr.HTML("""
                <div class="navbar">
                    <div class="navbar-logo">
                        🦉 OWL 多智能体协作系统
                    </div>
                    <div class="navbar-menu">
                        <a href="#home">首页</a>
                        <a href="https://github.com/camel-ai/owl/blob/main/README.md#-community">加入交流群</a>
                        <a href="https://github.com/camel-ai/owl/blob/main/README.md">OWL文档</a>
                        <a href="https://github.com/camel-ai/camel">CAMEL框架</a>
                        <a href="https://camel-ai.org">CAMEL-AI官网</a>
                    </div>
                </div>
                <div class="header" id="home">
                    
                    <p>我们的愿景是彻底改变AI代理协作解决现实世界任务的方式。通过利用动态代理交互，OWL能够在多个领域实现更自然、高效和稳健的任务自动化。</p>
                </div>
            """)
            
            with gr.Row(elem_id="features"):
                gr.HTML("""
                <div class="features-section">
                    <div class="feature-card">
                        <div class="feature-icon">🔍</div>
                        <h3>实时信息检索</h3>
                        <p>利用维基百科、谷歌搜索和其他在线资源获取最新信息。</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📹</div>
                        <h3>多模态处理</h3>
                        <p>支持处理互联网或本地的视频、图像和音频数据。</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🌐</div>
                        <h3>浏览器自动化</h3>
                        <p>使用Playwright框架模拟浏览器交互，实现网页操作自动化。</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📄</div>
                        <h3>文档解析</h3>
                        <p>从各种文档格式中提取内容，并转换为易于处理的格式。</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">💻</div>
                        <h3>代码执行</h3>
                        <p>使用解释器编写和运行Python代码，实现自动化数据处理。</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🧰</div>
                        <h3>内置工具包</h3>
                        <p>提供丰富的工具包，支持搜索、数据分析、代码执行等多种功能。</p>
                    </div>
                </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
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
                
                with gr.Column(scale=1):
                    gr.Markdown("""
                    ### 使用指南
                    
                    1. **选择适合的模块**：根据您的任务需求选择合适的功能模块
                    2. **详细描述您的需求**：在输入框中清晰描述您的问题或任务
                    3. **启动智能处理**：点击"运行"按钮开始多智能体协作处理
                    4. **查看结果**：在下方标签页查看回答和完整对话历史
                    
                    > **高级提示**: 对于复杂任务，可以尝试指定具体步骤和预期结果
                    """)
            
            status_output = gr.Textbox(label="状态", interactive=False)
            
            with gr.Tabs():
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
                    
                
            
            token_count_output = gr.Textbox(
                label="令牌计数", 
                interactive=False,
                elem_classes="token-count"
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
            )
            
            # 模块选择更新描述
            module_dropdown.change(
                fn=update_module_description,
                inputs=module_dropdown,
                outputs=module_description
            )
    
    return app

# 主函数
def main():
    try:
        app = create_ui()
        app.launch(share=False)
    except Exception as e:
        print(f"启动应用程序时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()