# 需求分析助手 Makefile
# 提供便捷的测试和开发命令

.PHONY: help test test-all clean setup install

# 默认目标
help:
	@echo "需求分析助手开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make test           - 运行快速测试"
	@echo "  make test-all       - 运行所有测试"
	@echo "  make test-coverage  - 运行测试并生成覆盖率报告"
	@echo "  make clean          - 清理测试产物"
	@echo "  make setup          - 设置开发环境"
	@echo "  make install        - 安装依赖"

# 测试命令
test:
	@echo "🚀 运行快速测试..."
	python run_tests.py --fast

test-all:
	@echo "🚀 运行所有测试..."
	python run_tests.py --all --verbose

test-coverage:
	@echo "📊 运行测试并生成覆盖率报告..."
	python run_tests.py --all --coverage

# 清理命令
clean:
	@echo "🧹 清理测试产物..."
	python run_tests.py --clean

# 环境设置
setup:
	@echo "⚙️ 设置开发环境..."
	python run_tests.py --setup

# 依赖安装
install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt

# 运行应用
run-cli:
	@echo "🖥️ 启动CLI模式..."
	python main.py --mode cli

run-web:
	@echo "🌐 启动Web模式..."
	python main.py --mode web

run-once:
	@echo "⚡ 运行单次分析..."
	@read -p "请输入需求描述: " req && python main.py --mode once "$$req"

# 文档生成
docs:
	@echo "📚 生成文档..."
	sphinx-build -b html docs/ docs/_build/html/

docs-serve:
	@echo "🌐 启动文档服务器..."
	cd docs/_build/html && python -m http.server 8080

# 构建和发布
build:
	@echo "🏗️ 构建项目..."
	python setup.py sdist bdist_wheel

publish:
	@echo "📤 发布项目..."
	twine upload dist/*

# Docker 命令
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t requirements-analysis-assistant .

docker-run:
	@echo "🐳 运行Docker容器..."
	docker run -p 8000:8000 requirements-analysis-assistant

docker-test:
	@echo "🐳 在Docker中运行测试..."
	docker run --rm requirements-analysis-assistant make test

# 监控和调试
monitor:
	@echo "📊 启动监控..."
	python -m prometheus_client.exposition 8090 &
	echo "监控端点: http://localhost:8090"

debug:
	@echo "🐛 调试模式..."
	python -m pdb main.py

# 数据库操作
db-init:
	@echo "🗄️ 初始化数据库..."
	python -c "from src.owl_requirements.utils.database import init_db; init_db()"

db-migrate:
	@echo "🗄️ 数据库迁移..."
	python -c "from src.owl_requirements.utils.database import migrate_db; migrate_db()"

db-reset:
	@echo "🗄️ 重置数据库..."
	python -c "from src.owl_requirements.utils.database import reset_db; reset_db()"

# 性能分析
profile:
	@echo "⚡ 性能分析..."
	python -m cProfile -o profile.stats main.py --mode once "测试需求"
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

benchmark:
	@echo "📊 基准测试..."
	python -m pytest tests/test_performance.py --benchmark-only

# 安全检查
security:
	@echo "🔒 安全检查..."
	bandit -r src/ -f json -o security-report.json
	safety check --json --output security-deps.json

# 依赖分析
deps-check:
	@echo "📋 检查依赖..."
	pip-audit --format=json --output=deps-audit.json

deps-update:
	@echo "📋 更新依赖..."
	pip-review --auto

# 代码统计
stats:
	@echo "📊 代码统计..."
	cloc src/ tests/ --json --out=code-stats.json
	@echo "代码统计报告已保存到 code-stats.json"

# 持续集成
ci: clean setup dev-install check test-coverage
	@echo "✅ CI检查完成"

# 预提交检查
pre-commit: format lint test-fast
	@echo "✅ 预提交检查完成"

# 发布准备
release-prep: clean ci docs build
	@echo "✅ 发布准备完成"

# 快速开发循环
dev: format lint test-fast
	@echo "✅ 开发循环完成"

# 显示项目状态
status:
	@echo "📊 项目状态:"
	@echo "  Git状态:"
	@git status --porcelain | head -10
	@echo "  最近提交:"
	@git log --oneline -5
	@echo "  测试覆盖率:"
	@coverage report --show-missing 2>/dev/null || echo "  运行 'make test-coverage' 生成覆盖率报告"
	@echo "  依赖状态:"
	@pip list --outdated | head -5 2>/dev/null || echo "  所有依赖都是最新的" 