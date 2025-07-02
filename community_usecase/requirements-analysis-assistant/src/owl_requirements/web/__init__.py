"""
OWL需求分析助手 - Web模块

提供Web界面和WebSocket服务，支持实时需求分析和多轮需求澄清。
"""

from .app import create_app

__all__ = ["create_app"]
