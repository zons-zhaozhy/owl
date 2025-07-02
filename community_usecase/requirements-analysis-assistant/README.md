# OWL Requirements Analysis Assistant

基于OWL框架的需求分析助手，用于自动化需求提取、分析、文档生成和质量检查。

## 功能特点

- 🔍 智能需求提取：从自然语言输入中提取结构化需求
- 📊 深度需求分析：评估可行性、复杂度和依赖关系
- 📝 自动文档生成：生成标准格式的需求文档
- ✅ 质量检查：确保需求的完整性、一致性和可测试性
- 🤖 多智能体协作：基于OWL框架的智能体系统

## 项目结构

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

## 安装

1. 克隆仓库：
```bash
git clone <repository_url>
cd requirements-analysis-assistant
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置：
```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml 设置必要的配置项
```

## 使用方法

### Web界面模式（默认）
```bash
python main.py
```

### CLI模式
```bash
python main.py --mode cli
```

### 单次执行模式
```bash
python main.py --mode once "需求描述"
```

### Web模式自定义配置
```bash
python main.py --mode web --port 8080 --host 127.0.0.1
```

## 开发指南

### 环境设置
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit hooks
pre-commit install
```

### 运行测试
```bash
pytest tests/
```

### 代码规范
- 遵循PEP 8规范
- 使用类型注解
- 编写完整的文档字符串
- 确保测试覆盖率

## 智能体系统

### 1. 需求提取智能体
- 负责从用户输入中提取结构化需求
- 支持多种输入格式
- 使用LLM进行智能识别

### 2. 需求分析智能体
- 评估需求可行性
- 分析依赖关系
- 识别潜在风险
- 提供实现建议

### 3. 文档生成智能体
- 生成标准格式文档
- 支持多种输出格式
- 维护需求追踪性

### 4. 质量检查智能体
- 验证需求质量
- 检查一致性
- 提供改进建议

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

[License Name] - 查看 LICENSE 文件了解更多信息。