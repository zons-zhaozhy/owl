# OWL Requirements Analysis Assistant

基于 OWL 框架的需求分析助手，用于自动化软件需求分析过程。

## 功能特点

- 🤖 多智能体协作系统
- 📝 自动需求提取和分析
- 📊 需求质量评估
- 📄 自动文档生成
- 🔄 实时反馈和建议
- 🌐 支持多种交互模式

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/your-org/owl-requirements.git
cd owl-requirements
```

2. 创建虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -e .
```

## 使用方法

### 命令行模式

```bash
# 启动交互式命令行界面
python -m owl_requirements --mode cli

# 单次分析模式
python -m owl_requirements --mode once "您的需求描述"
```

### Web 界面模式

```bash
# 启动 Web 界面（默认）
python -m owl_requirements

# 自定义端口和主机
python -m owl_requirements --mode web --port 8080 --host 127.0.0.1
```

## 项目结构

```
owl-requirements/
├── src/
│   └── owl_requirements/
│       ├── agents/             # 智能体实现
│       ├── core/              # 核心功能
│       ├── utils/             # 工具函数
│       ├── web/               # Web 界面
│       └── cli/               # 命令行界面
├── tests/                     # 测试用例
├── docs/                      # 文档
├── templates/                 # 模板文件
├── setup.py                  # 包配置
├── pyproject.toml            # 项目配置
└── README.md                 # 项目说明
```

## 开发指南

1. 安装开发依赖：

```bash
pip install -e ".[dev]"
```

2. 安装 pre-commit hooks：

```bash
pre-commit install
```

3. 运行测试：

```bash
pytest
```

4. 代码格式化：

```bash
black src tests
isort src tests
```

5. 类型检查：

```bash
mypy src
```

## 配置

1. 创建 `.env` 文件：

```bash
cp .env.example .env
```

2. 编辑配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# Web 界面配置
WEB_HOST=127.0.0.1
WEB_PORT=8000
```

## 智能体系统

系统由以下智能体组成：

1. 需求提取智能体
   - 从用户输入中提取需求
   - 识别需求类型和优先级
   - 标准化需求描述

2. 需求分析智能体
   - 分析需求完整性
   - 识别依赖关系
   - 评估可行性
   - 提供优化建议

3. 文档生成智能体
   - 生成标准格式文档
   - 维护需求追踪
   - 支持多种输出格式

4. 质量检查智能体
   - 评估需求质量
   - 检查一致性
   - 提供改进建议

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：[GitHub](https://github.com/your-org/owl-requirements)
- 问题反馈：[Issues](https://github.com/your-org/owl-requirements/issues)
- 邮件：owl@example.com