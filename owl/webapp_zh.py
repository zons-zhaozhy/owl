# Import from the correct module path
from owl.utils import run_society
import os
import gradio as gr
import time
import json
from typing import Tuple, List, Dict, Any
import importlib

# Enhanced CSS with navigation bar and additional styling
custom_css = """
:root {
    --primary-color: #1e3c72;
    --secondary-color: #2a5298;
    --accent-color: #4776E6;
    --light-bg: #f8f9fa;
    --border-color: #dee2e6;
    --text-muted: #6c757d;
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

.navbar-menu a {
    color: white;
    text-decoration: none;
    padding: 5px 10px;
    border-radius: 5px;
    transition: background-color 0.3s;
}

.navbar-menu a:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.header {
    text-align: center;
    margin-bottom: 20px;
    background: linear-gradient(180deg, var(--secondary-color), var(--accent-color));
    color: white;
    padding: 40px 20px;
    border-radius: 0 0 10px 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.feature-card {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: transform 0.3s, box-shadow 0.3s;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.feature-icon {
    font-size: 2em;
    color: var(--primary-color);
    margin-bottom: 10px;
}

/* Improved button and input styles */
button.primary {
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    transition: all 0.3s;
}

button.primary:hover {
    background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}
"""

# Dictionary containing module descriptions
MODULE_DESCRIPTIONS = {
    "run": "默认模式：使用默认的智能体协作模式，适合大多数任务。",
    "run_mini":"使用最小化配置处理任务",
    "run_deepseek_zh":"使用deepseek模型处理中文任务",
    "run_terminal_zh": "终端模式：可执行命令行操作，支持网络搜索、文件处理等功能。适合需要系统交互的任务。",
    "run_mini": "精简模式：轻量级智能体协作，适合快速回答和简单任务处理，响应速度更快。",
    "run_gaia_roleplaying":"GAIA基准测试实现，用于评估模型能力",
    "run_openai_compatiable_model":"使用openai兼容模型处理任务",
    "run_ollama":"使用本地ollama模型处理任务",
    "run_qwen_mini_zh":"使用qwen模型处理中文任务",
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

def run_owl(question: str, example_module: str) -> Tuple[str, List[List[str]], str, str]:
    """运行OWL系统并返回结果
    
    Args:
        question: 用户问题
        example_module: 要导入的示例模块名（如 "run_terminal_zh" 或 "run_deep"）
        
    Returns:
        Tuple[...]: 回答、聊天历史、令牌计数、状态
    """
    try:
        # 动态导入目标模块
        module_path = f"owl.examples.{example_module}"
        module = importlib.import_module(module_path)
        
        # 检查是否包含construct_society函数
        if not hasattr(module, "construct_society"):
            raise AttributeError(f"模块 {module_path} 中未找到 construct_society 函数")
            
        # 构建社会模拟
        society = module.construct_society(question)
        
        # 运行社会模拟（假设run_society兼容不同模块）
        answer, chat_history, token_info = run_society(society)
        
        # 格式化和令牌计数（与原逻辑一致）
        formatted_chat_history = format_chat_history(chat_history)
        total_tokens = token_info["completion_token_count"] + token_info["prompt_token_count"]
        
        return (
            answer, 
            formatted_chat_history, 
            f"完成令牌: {token_info['completion_token_count']:,} | 提示令牌: {token_info['prompt_token_count']:,} | 总计: {total_tokens:,}", 
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
                        🦉 OWL 智能助手
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
                    <h1>多智能体协作系统</h1>
                    <p>基于CAMEL框架的先进多智能体协作平台，解决复杂问题的智能解决方案</p>
                </div>
            """)
            
            with gr.Row(elem_id="features"):
                gr.HTML("""
                    <div class="features-section">
                        <div class="feature-card">
                            <div class="feature-icon">🔍</div>
                            <h3>智能信息获取</h3>
                            <p>自动化网络搜索和数据收集，提供精准信息</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🤖</div>
                            <h3>多智能体协作</h3>
                            <p>多个专家智能体协同工作，解决复杂问题</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📊</div>
                            <h3>数据分析与可视化</h3>
                            <p>强大的数据分析能力，生成直观的可视化结果</p>
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
                    module_dropdown = gr.Dropdown(
                        choices=["run", "run_mini","run_terminal_zh","run_gaia_roleplaying",
                                 "run_openai_compatiable_model","run_ollama","run_qwen_zh","run_qwen_mini_zh","run_deepseek_zh","run_terminal"],
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
                    <h3>关于 OWL 智能助手</h3>
                    <p>OWL 是一个基于CAMEL框架开发的先进多智能体协作系统，旨在通过智能体协作解决复杂问题。</p>
                    <p>© 2024 CAMEL-AI.org. 基于Apache License 2.0开源协议</p>
                    <p><a href="https://github.com/camel-ai/camel" target="_blank">GitHub</a> | 
                       <a href="#docs">文档</a> | 
                       <a href="#contact" id="contact">联系我们</a></p>
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
    app = create_ui()
    app.launch(share=False)

if __name__ == "__main__":
    main()