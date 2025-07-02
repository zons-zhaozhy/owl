"""
Web API测试模块。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from typing import Dict, Any

from owl_requirements.web.app import app
from owl_requirements.core.config import SystemConfig, LLMProvider
from owl_requirements.services.llm_factory import LLMFactory
from src.owl_requirements.core.config import Config
from src.owl_requirements.web.app import create_app


@pytest.fixture
def test_client():
    """测试客户端fixture。"""
    return TestClient(app)


@pytest.fixture
def mock_llm_service():
    """模拟LLM服务fixture。"""
    service = MagicMock()
    service.generate = MagicMock(return_value="测试响应")
    return service


@pytest.fixture
def mock_llm_factory(mock_llm_service):
    """模拟LLM工厂fixture。"""
    factory = MagicMock()
    factory.create_service = MagicMock(return_value=mock_llm_service)
    return factory


def test_health_check(test_client):
    """测试健康检查端点。"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_analyze_requirements_success(test_client, mock_llm_factory):
    """测试需求分析端点成功场景。"""
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "测试需求"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert data["analysis"] == "测试响应"
        mock_llm_factory.create_service.assert_called_once()


def test_analyze_requirements_empty_text(test_client):
    """测试需求分析端点空文本场景。"""
    response = test_client.post(
        "/api/v1/analyze",
        json={"text": ""}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "需求文本不能为空"


def test_analyze_requirements_missing_text(test_client):
    """测试需求分析端点缺少文本场景。"""
    response = test_client.post(
        "/api/v1/analyze",
        json={}
    )
    
    assert response.status_code == 422


def test_analyze_requirements_llm_error(test_client, mock_llm_factory):
    """测试需求分析端点LLM错误场景。"""
    mock_llm_service = MagicMock()
    mock_llm_service.generate = MagicMock(side_effect=Exception("LLM服务错误"))
    mock_llm_factory.create_service = MagicMock(return_value=mock_llm_service)
    
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "测试需求"}
        )
        
        assert response.status_code == 500
        assert response.json()["detail"] == "需求分析失败：LLM服务错误"


def test_analyze_requirements_invalid_json(test_client):
    """测试需求分析端点无效JSON场景。"""
    response = test_client.post(
        "/api/v1/analyze",
        data="invalid json"
    )
    
    assert response.status_code == 422


def test_analyze_requirements_cors(test_client):
    """测试需求分析端点CORS支持。"""
    response = test_client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_root_redirect(test_client):
    """测试根路径重定向。"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_files(test_client):
    """测试静态文件服务。"""
    response = test_client.get("/static/css/main.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    
    response = test_client.get("/static/js/main.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]


def test_analyze_requirements_rate_limit(test_client, mock_llm_factory):
    """测试需求分析端点速率限制。"""
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        # 发送多个请求测试速率限制
        for _ in range(5):
            response = test_client.post(
                "/api/v1/analyze",
                json={"text": "测试需求"}
            )
        
        # 第6个请求应该被限制
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "测试需求"}
        )
        
        assert response.status_code == 429
        assert "请求过于频繁" in response.json()["detail"]


def test_analyze_requirements_concurrent(test_client, mock_llm_factory):
    """测试需求分析端点并发处理。"""
    import asyncio
    import threading
    
    async def make_request():
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "测试需求"}
        )
        return response.status_code
    
    # 创建多个并发请求
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        loop = asyncio.new_event_loop()
        tasks = [make_request() for _ in range(3)]
        results = loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
        
        # 验证所有请求都成功
        assert all(status == 200 for status in results)


def test_analyze_requirements_large_input(test_client, mock_llm_factory):
    """测试需求分析端点大输入场景。"""
    large_text = "测试" * 10000  # 20KB的文本
    
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": large_text}
        )
        
        assert response.status_code == 400
        assert "需求文本过长" in response.json()["detail"]


def test_analyze_requirements_special_chars(test_client, mock_llm_factory):
    """测试需求分析端点特殊字符场景。"""
    special_chars = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/\\"
    
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": f"测试需求 {special_chars}"}
        )
        
        assert response.status_code == 200
        assert "analysis" in response.json()


def test_analyze_requirements_unicode(test_client, mock_llm_factory):
    """测试需求分析端点Unicode字符场景。"""
    unicode_text = "测试需求 🚀 👨‍💻 你好世界"
    
    with patch("owl_requirements.web.app.llm_factory", mock_llm_factory):
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": unicode_text}
        )
        
        assert response.status_code == 200
        assert "analysis" in response.json()


class TestWebAPI:
    """Web API 测试类"""
    
    def test_root_endpoint(self, test_client: TestClient):
        """测试根端点"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "OWL Requirements Analysis API" in response.text
        
    def test_health_check(self, test_client: TestClient):
        """测试健康检查"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        
    def test_analyze_requirements(self, test_client: TestClient, test_input_text: str):
        """测试需求分析"""
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": test_input_text}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "requirements" in data
        assert "analysis" in data
        assert len(data["requirements"]) > 0
        assert isinstance(data["analysis"], dict)
        
    def test_analyze_with_options(self, test_client: TestClient, test_input_text: str):
        """测试带选项的需求分析"""
        response = test_client.post(
            "/api/v1/analyze",
            json={
                "text": test_input_text,
                "format": "markdown",
                "include_metadata": True
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown"
        
        content = response.text
        assert "# 需求分析报告" in content
        assert "## 元数据" in content
        
    def test_batch_analyze(self, test_client: TestClient, test_input_text: str):
        """测试批量分析"""
        response = test_client.post(
            "/api/v1/analyze/batch",
            json={
                "items": [
                    {"text": test_input_text},
                    {"text": "另一个需求文本"}
                ]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert all("requirements" in item for item in data)
        
    def test_invalid_input(self, test_client: TestClient):
        """测试无效输入"""
        # 空文本
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": ""}
        )
        assert response.status_code == 400
        
        # 缺少文本字段
        response = test_client.post(
            "/api/v1/analyze",
            json={}
        )
        assert response.status_code == 422
        
        # 无效的格式
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "测试", "format": "invalid"}
        )
        assert response.status_code == 400
        
    def test_cors_headers(self, test_client: TestClient):
        """测试 CORS 头部"""
        response = test_client.options("/api/v1/analyze")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
        
    def test_rate_limiting(self, test_client: TestClient, test_input_text: str):
        """测试速率限制"""
        # 发送多个请求
        responses = []
        for _ in range(10):
            response = test_client.post(
                "/api/v1/analyze",
                json={"text": test_input_text}
            )
            responses.append(response)
            
        # 验证部分请求被限制
        success = sum(1 for r in responses if r.status_code == 200)
        limited = sum(1 for r in responses if r.status_code == 429)
        
        assert success > 0
        assert limited > 0
        assert success + limited == 10
        
    def test_error_handling(self, test_client: TestClient):
        """测试错误处理"""
        # 模拟内部错误
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "trigger_error"}
        )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "message" in data
        
        # 模拟验证错误
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": "a" * 10000}  # 超过最大长度
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data
        
    def test_async_analysis(self, test_client: TestClient, test_input_text: str):
        """测试异步分析"""
        # 启动异步任务
        response = test_client.post(
            "/api/v1/analyze/async",
            json={"text": test_input_text}
        )
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        
        # 检查任务状态
        task_id = data["task_id"]
        response = test_client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
        # 等待任务完成
        import time
        for _ in range(10):
            response = test_client.get(f"/api/v1/tasks/{task_id}")
            if response.json()["status"] == "completed":
                break
            time.sleep(0.5)
            
        # 获取结果
        response = test_client.get(f"/api/v1/tasks/{task_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert "requirements" in data
        assert "analysis" in data
        
    def test_websocket_updates(self, test_client: TestClient):
        """测试 WebSocket 更新"""
        import websockets
        import asyncio
        
        async def test_ws():
            uri = "ws://localhost:8000/ws/analysis"
            async with websockets.connect(uri) as websocket:
                # 发送分析请求
                await websocket.send(json.dumps({
                    "text": "测试需求文本"
                }))
                
                # 接收更新
                updates = []
                while True:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5
                        )
                        data = json.loads(message)
                        updates.append(data)
                        if data.get("status") == "completed":
                            break
                    except asyncio.TimeoutError:
                        break
                        
                assert len(updates) > 0
                assert updates[-1]["status"] == "completed"
                assert "requirements" in updates[-1]
                
        asyncio.run(test_ws())
        
    def test_documentation(self, test_client: TestClient):
        """测试 API 文档"""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/api/v1/analyze" in data["paths"]
        
    def test_metrics(self, test_client: TestClient):
        """测试指标端点"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        
        data = response.text
        assert "http_requests_total" in data
        assert "http_request_duration_seconds" in data
        assert "analysis_requests_total" in data
        
    def test_api_versioning(self, test_client: TestClient, test_input_text: str):
        """测试 API 版本控制"""
        # v1 版本
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": test_input_text}
        )
        assert response.status_code == 200
        
        # v2 版本（如果存在）
        response = test_client.post(
            "/api/v2/analyze",
            json={"text": test_input_text}
        )
        assert response.status_code in (200, 404)  # 取决于是否实现了 v2
        
    def test_request_validation(self, test_client: TestClient):
        """测试请求验证"""
        # 无效的 JSON
        response = test_client.post(
            "/api/v1/analyze",
            data="invalid json"
        )
        assert response.status_code == 422
        
        # 缺少必需字段
        response = test_client.post(
            "/api/v1/analyze",
            json={"invalid_field": "value"}
        )
        assert response.status_code == 422
        
        # 字段类型错误
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": 123}  # 应该是字符串
        )
        assert response.status_code == 422
        
    def test_response_headers(self, test_client: TestClient, test_input_text: str):
        """测试响应头部"""
        response = test_client.post(
            "/api/v1/analyze",
            json={"text": test_input_text}
        )
        assert response.status_code == 200
        
        # 验证标准头部
        assert "content-type" in response.headers
        assert "x-request-id" in response.headers
        assert "x-response-time" in response.headers
        
        # 验证缓存控制
        assert "cache-control" in response.headers
        assert "no-store" in response.headers["cache-control"]
        
    def test_security_headers(self, test_client: TestClient):
        """测试安全头部"""
        response = test_client.get("/")
        assert response.status_code == 200
        
        # 验证安全头部
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert "strict-transport-security" in response.headers 