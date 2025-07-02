"""
Web应用模块。
"""

import logging
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..core.config import SystemConfig
from ..services.llm_manager import LLMManager


# 创建日志记录器
logger = logging.getLogger(__name__)


class RequirementsRequest(BaseModel):
    """需求请求模型。"""
    text: str
    template: Optional[str] = "requirements_analysis"


class RequirementsResponse(BaseModel):
    """需求响应模型。"""
    analysis: Dict[str, str]


def create_app(
    config: SystemConfig,
    llm_manager: LLMManager
) -> FastAPI:
    """
    创建Web应用。

    Args:
        config: 系统配置
        llm_manager: LLM管理器

    Returns:
        FastAPI应用
    """
    # 创建应用
    app = FastAPI(
        title="OWL需求分析助手",
        description="基于OWL框架的需求分析系统",
        version="0.1.0"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # 挂载静态文件
    app.mount(
        "/static",
        StaticFiles(directory="static"),
        name="static"
    )
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """根路径处理。"""
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    
    @app.get("/health")
    async def health_check():
        """健康检查。"""
        return {"status": "ok"}
    
    @app.post("/api/analyze", response_model=RequirementsResponse)
    async def analyze_requirements(request: RequirementsRequest):
        """
        分析需求。

        Args:
            request: 需求请求

        Returns:
            需求分析结果
        """
        try:
            # 生成响应
            response = await llm_manager.generate(
                prompt=request.text,
                template_name=request.template
            )
            
            # 解析响应
            analysis = {}
            current_section = None
            current_content = []
            
            for line in response.content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
                    # 保存上一个部分
                    if current_section and current_content:
                        analysis[current_section] = "\n".join(current_content)
                        current_content = []
                    
                    # 开始新部分
                    current_section = line.split(".", 1)[1].strip()
                else:
                    current_content.append(line)
            
            # 保存最后一个部分
            if current_section and current_content:
                analysis[current_section] = "\n".join(current_content)
            
            return RequirementsResponse(analysis=analysis)
        except Exception as e:
            logger.error(f"需求分析失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"需求分析失败: {str(e)}"
            )
    
    return app 