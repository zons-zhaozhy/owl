"""
Setup configuration for the OWL Requirements Analysis Assistant package.
"""
from setuptools import setup, find_namespace_packages

setup(
    name="owl-requirements",
    version="0.1.0",
    description="Requirements analysis assistant based on the OWL framework",
    author="OWL Team",
    author_email="owl@example.com",
    packages=find_namespace_packages(where="src", include=["owl_requirements.*"]),
    package_dir={"": "src"},
    install_requires=[
        "loguru>=0.7.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "jinja2>=3.0.0",
        "pyyaml>=6.0.0",
        "markdown>=3.4.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "pre-commit>=3.0.0"
        ]
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "owl-requirements=owl_requirements.main:main"
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
) 