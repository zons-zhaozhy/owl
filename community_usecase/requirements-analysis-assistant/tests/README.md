# 需求分析助手测试文档

## 测试概述

本项目包含了完整的测试体系，覆盖了需求分析助手的所有核心功能，确保系统的可靠性和稳定性。

## 测试结构

```
tests/
├── conftest.py              # 测试配置和夹具
├── test_cli.py             # CLI接口测试
├── test_web.py             # Web接口测试
├── test_llm.py             # LLM服务测试
├── test_config.py          # 配置管理测试
├── test_analyzer.py        # 需求分析器测试
├── test_integration.py     # 集成测试
├── test_full_workflow.py   # 完整工作流程测试
└── README.md               # 本文档
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **标记**: `@pytest.mark.unit`
- **目的**: 测试单个模块或函数的功能
- **覆盖范围**: 
  - 配置管理
  - LLM服务
  - 需求分析器核心功能
  - 工具函数

### 2. 集成测试 (Integration Tests)
- **标记**: `@pytest.mark.integration`
- **目的**: 测试模块间的交互和集成
- **覆盖范围**:
  - CLI与后端服务集成
  - Web API与分析器集成
  - LLM服务与配置集成

### 3. 性能测试 (Performance Tests)
- **标记**: `@pytest.mark.performance`
- **目的**: 测试系统性能和响应时间
- **覆盖范围**:
  - 大量需求处理性能
  - 并发请求处理
  - 内存使用优化

### 4. 端到端测试 (End-to-End Tests)
- **文件**: `test_full_workflow.py`
- **目的**: 测试完整的用户工作流程
- **覆盖范围**:
  - 完整需求分析流程
  - 多模式运行测试
  - 错误处理流程

## 快速开始

### 1. 安装测试依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-cov pytest-html pytest-xdist pytest-mock
```

### 2. 运行测试

```bash
# 运行所有快速测试
make test

# 运行所有测试
make test-all

# 运行特定类型的测试
python run_tests.py --unit          # 单元测试
python run_tests.py --integration   # 集成测试
python run_tests.py --performance   # 性能测试

# 运行特定测试文件
python run_tests.py --test tests/test_cli.py

# 生成覆盖率报告
make test-coverage
```

### 3. 并行测试

```bash
# 并行运行测试（4个进程）
python run_tests.py --fast --parallel 4

# 自动检测CPU核心数并行运行
pytest -n auto
```

## 测试配置

### pytest.ini
项目根目录的 `pytest.ini` 文件包含了测试的默认配置：

- 测试发现路径
- 标记定义
- 日志配置
- 警告过滤
- 超时设置

### conftest.py
`tests/conftest.py` 提供了丰富的测试夹具：

- `test_config`: 测试配置
- `mock_llm_service`: 模拟LLM服务
- `temp_dir`: 临时目录
- `sample_requirements_file`: 示例需求文件
- 各种模拟服务和客户端

## 测试覆盖范围

### CLI接口测试 (test_cli.py)
- ✅ 版本命令
- ✅ 分析命令
- ✅ 批量处理
- ✅ 配置管理
- ✅ 交互模式
- ✅ 错误处理
- ✅ 输出格式
- ✅ 文件输入输出

### Web接口测试 (test_web.py)
- ✅ 健康检查端点
- ✅ 需求分析API
- ✅ 批量处理API
- ✅ WebSocket通信
- ✅ 输入验证
- ✅ 速率限制
- ✅ CORS配置
- ✅ 错误处理

### LLM服务测试 (test_llm.py)
- ✅ 服务初始化
- ✅ 多提供商支持 (OpenAI, Anthropic, Azure)
- ✅ 模型选择
- ✅ 参数配置
- ✅ 重试机制
- ✅ 流式响应
- ✅ 超时处理
- ✅ 并发请求

### 配置管理测试 (test_config.py)
- ✅ 配置加载
- ✅ 环境变量支持
- ✅ 配置验证
- ✅ 默认值处理
- ✅ 配置更新
- ✅ 敏感信息处理

### 需求分析器测试 (test_analyzer.py)
- ✅ 需求提取
- ✅ 需求分类
- ✅ 优先级排序
- ✅ 依赖关系分析
- ✅ 风险评估
- ✅ 质量检查
- ✅ 冲突检测
- ✅ 版本控制

### 集成测试 (test_integration.py)
- ✅ 系统级集成
- ✅ 数据流测试
- ✅ 配置集成
- ✅ 错误传播
- ✅ 性能集成

### 完整工作流程测试 (test_full_workflow.py)
- ✅ 端到端分析流程
- ✅ 多模式运行测试
- ✅ 并发处理测试
- ✅ 错误恢复测试
- ✅ 数据持久化测试

## 测试数据

### 示例需求
测试中使用的示例需求涵盖：
- 功能需求
- 性能需求
- 安全需求
- 界面需求
- 约束条件

### 测试配置
- 模拟API密钥
- 测试环境配置
- 临时文件路径
- 数据库连接

## 测试报告

### 覆盖率报告
```bash
# 生成HTML覆盖率报告
python run_tests.py --all --coverage

# 查看覆盖率报告
open htmlcov/index.html
```

### HTML测试报告
```bash
# 生成HTML测试报告
python run_tests.py --report

# 查看测试报告
open test_reports/report.html
```

### 性能报告
```bash
# 运行性能测试
python run_tests.py --performance

# 查看性能数据
cat performance_report.json
```

## 持续集成

### GitHub Actions
项目配置了GitHub Actions工作流程：
- 多Python版本测试
- 多操作系统测试
- 覆盖率报告上传
- 测试结果通知

### 预提交钩子
```bash
# 安装预提交钩子
pre-commit install

# 手动运行预提交检查
pre-commit run --all-files
```

## 调试测试

### 运行单个测试
```bash
# 运行单个测试方法
pytest tests/test_cli.py::TestCLI::test_version_command -v

# 运行单个测试类
pytest tests/test_cli.py::TestCLI -v
```

### 调试模式
```bash
# 启用详细输出
pytest -v -s

# 进入调试模式
pytest --pdb

# 在失败时进入调试模式
pytest --pdb-trace
```

### 日志调试
```bash
# 启用日志输出
pytest --log-cli-level=DEBUG

# 查看测试日志文件
tail -f tests.log
```

## 测试最佳实践

### 1. 测试命名
- 使用描述性的测试名称
- 遵循 `test_<功能>_<场景>_<期望结果>` 格式
- 使用中文注释说明测试目的

### 2. 测试隔离
- 每个测试独立运行
- 使用夹具管理测试数据
- 避免测试间的依赖关系

### 3. 模拟外部依赖
- 使用mock模拟外部API调用
- 模拟数据库操作
- 模拟文件系统操作

### 4. 断言质量
- 使用具体的断言
- 验证错误消息
- 检查副作用

### 5. 测试数据管理
- 使用夹具提供测试数据
- 清理测试产生的文件
- 避免硬编码测试数据

## 故障排除

### 常见问题

1. **测试超时**
   - 检查网络连接
   - 增加超时时间
   - 使用mock替代真实API调用

2. **依赖缺失**
   - 运行 `python run_tests.py --check-deps`
   - 安装缺失的测试依赖

3. **权限问题**
   - 检查文件权限
   - 使用临时目录进行测试

4. **环境变量**
   - 确保测试环境变量正确设置
   - 使用 `.env` 文件管理配置

### 获取帮助

如果遇到测试问题：
1. 查看测试日志文件
2. 运行单个测试进行调试
3. 检查测试配置
4. 查看项目文档
5. 提交Issue报告问题

## 贡献指南

### 添加新测试
1. 选择合适的测试文件
2. 编写测试函数
3. 添加适当的标记
4. 更新文档

### 测试代码风格
- 遵循项目代码风格
- 使用中文注释
- 保持测试简洁明了
- 添加必要的文档字符串

### 提交测试
1. 运行完整测试套件
2. 确保所有测试通过
3. 检查测试覆盖率
4. 提交代码审查 