"""Web application entry point."""

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from owl_requirements.agents import (
    RequirementsAnalysisAgent,
    RequirementsExtractionAgent,
    DocumentationGeneratorAgent,
    QualityCheckAgent
)
from owl_requirements.core.config import SystemConfig
from owl_requirements.core.types import (
    AnalysisResult,
    DocumentationResult,
    QualityCheckResult,
    RequirementsResult
)

# 创建FastAPI应用
app = FastAPI(
    title="需求分析助手",
    description="基于OWL框架的智能需求分析系统",
    version="1.0.0"
)

# 获取当前文件所在目录
current_dir = Path(__file__).parent

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")

# 设置模板目录
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# 请求模型
class AnalyzeRequest(BaseModel):
    text: str

# 响应模型
class AnalyzeResponse(BaseModel):
    requirements: RequirementsResult
    analysis: AnalysisResult
    quality_check: QualityCheckResult
    documentation: DocumentationResult

# 系统配置
system_config = SystemConfig()

# 创建智能体实例
requirements_extractor = RequirementsExtractionAgent(system_config)
requirements_analyzer = RequirementsAnalysisAgent(system_config)
documentation_generator = DocumentationGeneratorAgent(system_config)
quality_checker = QualityCheckAgent(system_config)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    渲染主页
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_requirements(request: AnalyzeRequest) -> Dict:
    """
    分析需求并返回结果
    """
    try:
        # 提取需求
        requirements = await requirements_extractor.extract(request.text)
        
        # 分析需求
        analysis = await requirements_analyzer.analyze(requirements)
        
        # 生成文档
        documentation = await documentation_generator.generate(
            requirements=requirements,
            analysis=analysis
        )
        
        # 质量检查
        quality_check = await quality_checker.check(
            requirements=requirements,
            analysis=analysis,
            documentation=documentation
        )
        
        return {
            "requirements": requirements,
            "analysis": analysis,
            "quality_check": quality_check,
            "documentation": documentation
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"需求分析失败: {str(e)}"
        )

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    健康检查端点
    """
    return {"status": "healthy"}

@app.get("/api-docs")
async def api_documentation(request: Request) -> HTMLResponse:
    """
    API文档页面
    """
    return templates.TemplateResponse(
        "api-docs.html",
        {"request": request}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 