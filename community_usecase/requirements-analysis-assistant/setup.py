"""
Setup configuration for the OWL Requirements Analysis Assistant package.
"""
from setuptools import setup, find_packages

setup(
    name="owl-requirements",
    version="1.0.0",
    description="基于OWL框架的需求分析系统",
    author="OWL Team",
    author_email="owl@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Core dependencies
        "loguru>=0.7.0",
        "pydantic>=2.11.0",
        "aiohttp>=3.8.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "jinja2>=3.0.0",
        "pyyaml>=6.0.0",
        "markdown>=3.4.0",
        "httpx>=0.27.0",
        
        # Web Framework
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "websockets>=10.0",
        "python-multipart>=0.0.5",
        "aiofiles>=0.8.0",
        "pydantic-settings>=2.1.0",
        "tiktoken>=0.6.0",
        "gradio>=4.19.2",
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        
        # CLI
        "click>=8.0.0",
        "prompt_toolkit>=3.0.0",
        
        # Utils
        "python-dotenv>=1.0.1",
        "requests>=2.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.5.14",
            "mkdocstrings>=0.24.1",
            "mkdocstrings-python>=1.9.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "owl-requirements=main:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
) 