from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import json
import uuid
import logging
from pathlib import Path

from ..core.coordinator import RequirementsCoordinator
from ..core.config import SystemConfig
from ..core.models import RequirementsAnalysisResult, ProcessingStatus, WebSocketMessage


def create_web_app(config: SystemConfig) -> FastAPI:
    """创建Web应用实例"""
    app = FastAPI(title="OWL需求分析助手")

    # 配置静态文件和模板
    base_path = Path(__file__).parent
    static_path = base_path / "static"
    templates_path = base_path / "templates"

    app.mount("/static", StaticFiles(directory=str(static_path)), _name="static")
    templates = Jinja2Templates(directory=str(templates_path))

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        _allow_origins=config.web.cors_origins,
        _allow_credentials=True,
        _allow_methods=["*"],
        _allow_headers=["*"],
    )

    # 会话管理
    sessions: Dict[str, dict] = {}

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """根路径处理"""
        return RedirectResponse(url="/index.html")

    @app.get("/index.html", response_class=HTMLResponse)
    async def index(request):
        """主页"""
        return templates.TemplateResponse("index.html", {"request": request})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket处理"""
        await websocket.accept()
        session_id = str(uuid.uuid4())

        try:
            # 创建会话
            coordinator = RequirementsCoordinator(config)
            sessions[session_id] = {"websocket": websocket, "coordinator": coordinator}

            # 发送会话ID
            await websocket.send_json({"type": "session", "session_id": session_id})

            # 处理消息
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message["type"] == "analyze":
                    # 处理需求分析请求
                    requirements_text = message["text"]
                    result = await coordinator.process(requirements_text)

                    # 发送结果
                    await websocket.send_json({"type": "result", "data": result.dict()})
                elif message["type"] == "status":
                    # 获取处理状态
                    status = coordinator.get_status()
                    await websocket.send_json({"type": "status", "data": status.dict()})

        except WebSocketDisconnect:
            logging.info(f"WebSocket连接断开: {session_id}")
        except Exception as e:
            logging.error(f"WebSocket错误: {str(e)}")
            await websocket.send_json({"type": "error", "message": str(e)})
        finally:
            # 清理会话
            if session_id in sessions:
                del sessions[session_id]

    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "healthy"}

    return app


# 创建默认应用实例
_app = create_web_app(SystemConfig())
