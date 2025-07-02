"""
Web 接口测试模块
"""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.owl_requirements.web.app import app
from src.owl_requirements.core.config import Config
from src.owl_requirements.core.exceptions import WebAPIError

client = TestClient(app)

class TestWebAPI:
    """Web API 测试类"""
    
    def test_root_endpoint(self):
        """测试根路径端点"""
        response = client.get("/")
        assert response.status_code == 200
        assert "OWL Requirements Analysis" in response.json()["title"]
        
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
    def test_analyze_requirements(self, test_input_text: str):
        """测试需求分析端点"""
        response = client.post(
            "/api/v1/analyze",
            json={"text": test_input_text}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "requirements" in data
        assert "analysis" in data
        
    def test_batch_analyze(self, test_input_text: str):
        """测试批量分析端点"""
        requests = [
            {"text": f"{test_input_text} {i}"}
            for i in range(3)
        ]
        
        response = client.post(
            "/api/v1/analyze/batch",
            json={"requests": requests}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        
    def test_async_analyze(self, test_input_text: str):
        """测试异步分析端点"""
        # 提交分析请求
        response = client.post(
            "/api/v1/analyze/async",
            json={"text": test_input_text}
        )
        
        assert response.status_code == 202
        task_id = response.json()["task_id"]
        
        # 检查任务状态
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] in ["pending", "processing", "completed"]
        
    def test_websocket_updates(self, test_input_text: str):
        """测试 WebSocket 更新"""
        with client.websocket_connect("/ws") as websocket:
            # 发送分析请求
            websocket.send_json({
                "type": "analyze",
                "data": {"text": test_input_text}
            })
            
            # 接收进度更新
            data = websocket.receive_json()
            assert data["type"] == "progress"
            
            # 接收最终结果
            data = websocket.receive_json()
            assert data["type"] == "result"
            assert "requirements" in data["data"]
            
    def test_input_validation(self):
        """测试输入验证"""
        # 空文本
        response = client.post(
            "/api/v1/analyze",
            json={"text": ""}
        )
        assert response.status_code == 422
        
        # 缺少必需字段
        response = client.post(
            "/api/v1/analyze",
            json={}
        )
        assert response.status_code == 422
        
        # 文本过长
        response = client.post(
            "/api/v1/analyze",
            json={"text": "a" * 10001}
        )
        assert response.status_code == 422
        
    def test_error_handling(self):
        """测试错误处理"""
        # 模拟内部错误
        with patch(
            "src.owl_requirements.services.analyzer.RequirementsAnalyzer.analyze",
            side_effect=Exception("分析错误")
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "测试文本"}
            )
            assert response.status_code == 500
            assert "error" in response.json()
            
    def test_rate_limiting(self):
        """测试速率限制"""
        # 快速发送多个请求
        for _ in range(10):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "测试文本"}
            )
            
        response = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本"}
        )
        assert response.status_code == 429
        
    def test_cors_headers(self):
        """测试 CORS 头部"""
        response = client.options("/api/v1/analyze")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        
    def test_api_versioning(self):
        """测试 API 版本控制"""
        # v1 版本
        response = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本"}
        )
        assert response.status_code == 200
        
        # 不存在的版本
        response = client.post(
            "/api/v2/analyze",
            json={"text": "测试文本"}
        )
        assert response.status_code == 404
        
    def test_metrics_endpoint(self):
        """测试指标端点"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "requests_total" in response.text
        assert "response_time_seconds" in response.text
        
    def test_api_documentation(self):
        """测试 API 文档"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/v1/analyze" in schema["paths"]
        
    def test_request_validation(self):
        """测试请求验证"""
        # 无效的 JSON
        response = client.post(
            "/api/v1/analyze",
            data="invalid json"
        )
        assert response.status_code == 422
        
        # 无效的内容类型
        response = client.post(
            "/api/v1/analyze",
            data="test",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 415
        
    def test_response_headers(self):
        """测试响应头部"""
        response = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本"}
        )
        
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers
        
    def test_security_headers(self):
        """测试安全头部"""
        response = client.get("/")
        
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        
    def test_compression(self):
        """测试响应压缩"""
        response = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本" * 100},
            headers={"Accept-Encoding": "gzip"}
        )
        
        assert response.status_code == 200
        assert response.headers["Content-Encoding"] == "gzip"
        
    def test_caching(self):
        """测试缓存控制"""
        # 首次请求
        response1 = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本"}
        )
        etag1 = response1.headers["ETag"]
        
        # 带条件的请求
        response2 = client.post(
            "/api/v1/analyze",
            json={"text": "测试文本"},
            headers={"If-None-Match": etag1}
        )
        assert response2.status_code == 304
        
    def test_large_payload(self):
        """测试大型负载处理"""
        large_text = "测试文本\n" * 1000
        
        response = client.post(
            "/api/v1/analyze",
            json={"text": large_text}
        )
        
        assert response.status_code == 200
        assert "requirements" in response.json()
        
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import asyncio
        import httpx
        
        async def make_request():
            async with httpx.AsyncClient(app=app) as ac:
                response = await ac.post(
                    "/api/v1/analyze",
                    json={"text": "测试文本"}
                )
                return response.status_code
                
        async def test_concurrent():
            tasks = [make_request() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            return results
            
        results = asyncio.run(test_concurrent())
        assert all(status == 200 for status in results)
        
    def test_graceful_shutdown(self):
        """测试优雅关闭"""
        # 模拟长时间运行的请求
        with patch(
            "src.owl_requirements.services.analyzer.RequirementsAnalyzer.analyze",
            side_effect=lambda *args, **kwargs: time.sleep(2)
        ):
            # 发送请求
            response = client.post(
                "/api/v1/analyze",
                json={"text": "测试文本"}
            )
            
            # 模拟关闭信号
            app.shutdown()
            
            assert response.status_code in [200, 503]
            
    def test_request_timeout(self):
        """测试请求超时"""
        # 模拟超时
        with patch(
            "src.owl_requirements.services.analyzer.RequirementsAnalyzer.analyze",
            side_effect=asyncio.TimeoutError
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "测试文本"}
            )
            
            assert response.status_code == 504
            assert "timeout" in response.json()["error"].lower() 