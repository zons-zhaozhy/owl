.PHONY: install install-dev format lint test coverage clean docs serve-docs

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Code formatting and linting
format:
	black src tests
	isort src tests

lint:
	flake8 src tests
	mypy src tests
	bandit -c pyproject.toml -r src

# Testing
test:
	pytest

coverage:
	pytest --cov=src --cov-report=html

# Documentation
docs:
	mkdocs build

serve-docs:
	mkdocs serve

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf site/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Development workflow
dev: install-dev format lint test

# Run the application
run-web:
	python -m owl_requirements.run --mode web

run-cli:
	python -m owl_requirements.run --mode cli

# Help
help:
	@echo "Available commands:"
	@echo "  make install      - Install the package"
	@echo "  make install-dev  - Install the package with development dependencies"
	@echo "  make format      - Format code with black and isort"
	@echo "  make lint        - Run linting tools"
	@echo "  make test        - Run tests"
	@echo "  make coverage    - Generate test coverage report"
	@echo "  make docs        - Build documentation"
	@echo "  make serve-docs  - Serve documentation locally"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make dev         - Run full development workflow"
	@echo "  make run-web     - Run the web interface"
	@echo "  make run-cli     - Run the CLI interface" 