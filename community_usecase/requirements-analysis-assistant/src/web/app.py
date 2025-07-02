"""Web application entry point."""

from pathlib import Path
from typing import Dict
import uuid
import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from owl_requirements.agents import (
    RequirementsAnalysisAgent,
    RequirementsExtractionAgent,
    DocumentationGeneratorAgent,
    QualityCheckAgent,
)
from owl_requirements.core.config import SystemConfig
from owl_requirements.core.types import (
    AnalysisResult,
    DocumentationResult,
    QualityCheckResult,
    RequirementsResult,
)
from owl_requirements.core.coordinator import RequirementsCoordinator
from owl_requirements.core.models import (
    RequirementsAnalysisResult,
    ProcessingStatus,
    WebSocketMessage,
)

# 创建FastAPI应用
app = FastAPI(
    _title="需求分析助手",
    description="基于OWL框架的智能需求分析系统",
    _version="1.0.0",
)

# 获取当前文件所在目录
current_dir = Path(__file__).parent

# 挂载静态文件
app.mount(
    "/static",
    StaticFiles(directory=str(current_dir / "static")),
    name="static",
)

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

# WebSocket连接管理


class ConnectionManager:

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = str(uuid.uuid4())
        self.active_connections[session_id] = websocket
        self.sessions[session_id] = {
            "coordinator": RequirementsCoordinator(SystemConfig()),
            "status": {
                "extraction": "pending",
                "analysis": "pending",
                "quality": "pending",
                "documentation": "pending",
            },
        }
        return session_id

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    渲染主页
    """
    return templates.TemplateResponse("index.html", {"request": request})


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
            requirements=requirements, analysis=analysis
        )

        # 质量检查
        quality_check = await quality_checker.check(
            requirements=requirements,
            analysis=analysis,
            documentation=documentation,
        )

        return {
            "requirements": requirements,
            "analysis": analysis,
            "quality_check": quality_check,
            "documentation": documentation,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")


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
    return templates.TemplateResponse("api-docs.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)

    # 发送会话创建消息
    await manager.send_message(
        session_id, {"type": "session_created", "session_id": session_id}
    )

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "user_input":
                # 获取会话信息
                session = manager.sessions[session_id]
                coordinator = session["coordinator"]

                # 更新处理状态
                session["status"]["extraction"] = "processing"
                await manager.send_message(
                    session_id,
                    {"type": "processing_update", "status": session["status"]},
                )

                try:
                    # 处理需求
                    result = await coordinator.process_requirements(data["content"])

                    # 更新需求列表
                    await manager.send_message(
                        session_id,
                        {
                            "type": "requirements_update",
                            "requirements": [
                                {
                                    "id": f"REQ{i+1}",
                                    "description": req.description,
                                    "priority": req.priority,
                                }
                                for i, req in enumerate(result.requirements)
                            ],
                        },
                    )

                    # 更新分析结果
                    await manager.send_message(
                        session_id,
                        {
                            "type": "analysis_update",
                            "analysis": {
                                "completeness": result.completeness_score * 100,
                                "clarity": result.clarity_score * 100,
                            },
                        },
                    )

                    # 更新处理状态
                    session["status"] = {
                        "extraction": "complete",
                        "analysis": "complete",
                        "quality": "complete",
                        "documentation": "complete",
                    }
                    await manager.send_message(
                        session_id,
                        {
                            "type": "processing_update",
                            "status": session["status"],
                        },
                    )

                    # 发送分析完成消息
                    await manager.send_message(
                        session_id,
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": f"需求分析完成！\n\n共识别出 {len(result.requirements)} 个需求。\n\n"
                            + f"需求完整性评分：{result.completeness_score:.2%}\n"
                            + f"需求清晰度评分：{result.clarity_score:.2%}",
                        },
                    )

                except Exception as e:
                    logging.error(f"处理需求时出错: {str(e)}")
                    session["status"] = {
                        "extraction": "error",
                        "analysis": "error",
                        "quality": "error",
                        "documentation": "error",
                    }
                    await manager.send_message(
                        session_id,
                        {
                            "type": "processing_update",
                            "status": session["status"],
                        },
                    )
                    await manager.send_message(
                        session_id,
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": f"处理需求时出错: {str(e)}",
                        },
                    )

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logging.error(f"WebSocket处理时出错: {str(e)}")
        manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
