# OWL需求分析助手

基于OWL框架的智能需求分析系统，支持自动化需求提取、分析、文档生成和质量检查。

## 功能特点

- 🤖 智能需求提取和分析
- 📝 自动生成结构化需求文档
- ✅ 需求质量检查和建议
- 🌐 支持Web界面和CLI操作
- 🔄 实时分析反馈
- 📊 可视化分析结果

## 系统要求

- Python 3.8+
- Node.js 14+ (用于前端开发)

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/your-username/owl-requirements.git
cd owl-requirements
```

2. 创建虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 配置环境变量：

创建 `.env` 文件并添加以下配置：

```env
# 选择一个LLM提供商
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Web服务配置
HOST=127.0.0.1
PORT=8080
```

## 使用方法

### Web界面模式（默认）

```bash
python main.py
# 或
python main.py --mode web --host 127.0.0.1 --port 8080
```

访问 http://localhost:8080 使用Web界面。

### 命令行交互模式

```bash
python main.py --mode cli
```

### 单次执行模式

```bash
python main.py --mode once --text "您的需求描述"
```

## 配置

系统配置文件位于 `config/system.yaml`：

```yaml
# 运行模式配置
mode: web  # web, cli, once
input_text: null  # 单次执行模式的输入文本

# Web服务配置
host: 127.0.0.1
port: 8080

# LLM配置
llm_provider: deepseek  # openai, deepseek, ollama

# 日志配置
log_level: INFO
log_file: logs/owl.log
```

LLM配置文件位于 `config/llm.yaml`：

```yaml
llm:
  default_provider: deepseek
  providers:
    openai:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4-turbo-preview
      temperature: 0.7
      max_tokens: 2000
    
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      temperature: 0.7
      max_tokens: 2000
    
    ollama:
      host: http://localhost:11434
      model: llama2
      temperature: 0.7
      max_tokens: 2000
```

## 开发

### 项目结构

```
requirements-analysis-assistant/
├── src/
│   ├── owl_requirements/      # 核心功能模块
│   │   ├── agents/           # 智能体实现
│   │   ├── core/             # 核心功能
│   │   ├── services/         # 服务层
│   │   └── utils/            # 通用工具
│   ├── web/                  # Web界面
│   ├── cli/                  # CLI接口
│   └── config/               # 配置
├── tests/                    # 测试用例
└── docs/                     # 文档
```

### 运行测试

```bash
pytest tests/
```

### 代码风格

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行代码检查
flake8 src/
mypy src/
```

## 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目维护者：Your Name
- 邮箱：your.email@example.com
- 项目链接：https://github.com/your-username/owl-requirements