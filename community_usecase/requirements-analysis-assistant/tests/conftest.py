"""
测试配置和 fixtures
"""
import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.owl_requirements.core.config import Config
from src.owl_requirements.services.llm_factory import LLMFactory
from src.owl_requirements.web.app import create_app

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """测试配置"""
    return {
        "llm_provider": "openai",
        "llm_model": "gpt-3.5-turbo",
        "llm_temperature": 0.1,
        "llm_max_tokens": 2048,
        "llm_timeout": 30,
        "llm_retry_count": 3,
        "llm_retry_delay": 1.0,
        "api_key": "test-api-key",
        "base_url": "https://api.openai.com/v1",
        "log_level": "INFO",
        "output_format": "json",
        "web_host": "127.0.0.1",
        "web_port": 8000,
        "enable_cors": True,
        "enable_rate_limit": False,
        "max_concurrent_requests": 10,
        "request_timeout": 30,
        "enable_caching": False,
        "cache_ttl": 3600,
        "enable_metrics": False,
        "metrics_port": 9090
    }

@pytest.fixture
def test_input_text() -> str:
    """提供测试输入文本"""
    return """
    需求描述：
    开发一个在线教育平台，支持以下功能：
    1. 用户注册和登录
    2. 课程浏览和搜索
    3. 在线支付
    4. 视频播放
    5. 作业提交
    6. 师生互动
    """

@pytest.fixture
def mock_llm_response() -> str:
    """提供模拟的 LLM 响应"""
    return {
        "requirements": [
            {
                "id": "REQ-001",
                "title": "用户认证系统",
                "description": "实现用户注册和登录功能",
                "priority": "高",
                "category": "核心功能"
            },
            {
                "id": "REQ-002",
                "title": "课程管理",
                "description": "支持课程浏览和搜索",
                "priority": "高",
                "category": "核心功能"
            }
        ],
        "analysis": {
            "complexity": "中等",
            "estimated_time": "3-4个月",
            "key_challenges": [
                "用户数据安全",
                "视频流处理",
                "并发性能"
            ]
        }
    }

@pytest.fixture
def mock_llm_service():
    """模拟LLM服务"""
    with patch('src.owl_requirements.services.llm.LLMService') as mock:
        mock_instance = MagicMock()
        mock_instance.analyze_requirements.return_value = {
            "requirements": [
                {
                    "description": "用户可以登录系统",
                    "category": "功能需求",
                    "priority": "高",
                    "complexity": "中"
                }
            ],
            "analysis": {
                "total_requirements": 1,
                "complexity_distribution": {"高": 0, "中": 1, "低": 0},
                "priority_distribution": {"高": 1, "中": 0, "低": 0}
            }
        }
        mock_instance.extract_requirements.return_value = [
            {
                "description": "用户可以登录系统",
                "type": "功能需求"
            }
        ]
        mock_instance.classify_requirements.return_value = [
            {
                "description": "用户可以登录系统",
                "category": "功能需求",
                "confidence": 0.95
            }
        ]
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_llm_factory(mock_llm_service):
    """提供模拟的 LLM 工厂"""
    mock_factory = MagicMock(spec=LLMFactory)
    mock_factory.create_service.return_value = mock_llm_service
    return mock_factory

@pytest.fixture
def test_client(test_config: Dict[str, Any], mock_llm_factory) -> TestClient:
    """提供测试客户端"""
    config = Config()
    config.load_from_dict(test_config)
    
    with patch("src.owl_requirements.web.app.llm_factory", mock_llm_factory):
        app = create_app()
        return TestClient(app)

@pytest.fixture
def temp_dir():
    """临时目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_requirements_file(temp_dir):
    """示例需求文件"""
    content = """
    需求文档
    
    1. 用户管理
    - 用户注册
    - 用户登录
    - 密码重置
    
    2. 系统管理
    - 数据备份
    - 日志记录
    - 监控告警
    """
    
    file_path = temp_dir / "requirements.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path

@pytest.fixture
def mock_config_file(temp_dir):
    """模拟配置文件"""
    config_content = """
    [llm]
    provider = openai
    model = gpt-3.5-turbo
    temperature = 0.1
    max_tokens = 2048
    
    [api]
    key = test-api-key
    base_url = https://api.openai.com/v1
    timeout = 30
    
    [web]
    host = 127.0.0.1
    port = 8000
    enable_cors = true
    """
    
    config_file = temp_dir / "config.ini"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    return config_file

@pytest.fixture
def mock_database():
    """模拟数据库"""
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn

@pytest.fixture
def mock_openai_client():
    """模拟OpenAI客户端"""
    with patch('openai.OpenAI') as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"requirements": [{"description": "用户登录", "priority": "高"}]}'))
        ]
        mock_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_anthropic_client():
    """模拟Anthropic客户端"""
    with patch('anthropic.Anthropic') as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"requirements": [{"description": "用户登录", "priority": "高"}]}')
        ]
        mock_instance.messages.create.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_web_client():
    """模拟Web客户端"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"requirements": []}
        }
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_file_system(temp_dir):
    """模拟文件系统"""
    # 创建测试目录结构
    (temp_dir / "input").mkdir()
    (temp_dir / "output").mkdir()
    (temp_dir / "logs").mkdir()
    (temp_dir / "cache").mkdir()
    
    # 创建测试文件
    test_files = {
        "input/requirements.txt": "用户登录需求",
        "input/requirements.md": "# 需求\n- 用户管理",
        "input/requirements.json": '{"requirements": ["用户登录"]}',
        "config/settings.yaml": "llm:\n  provider: openai"
    }
    
    for file_path, content in test_files.items():
        full_path = temp_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return temp_dir

@pytest.fixture
def mock_environment():
    """模拟环境变量"""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "OWL_LOG_LEVEL": "DEBUG",
        "OWL_CONFIG_PATH": "/tmp/test-config.yaml"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

@pytest.fixture
def mock_metrics():
    """模拟指标收集"""
    with patch('prometheus_client.Counter') as mock_counter, \
         patch('prometheus_client.Histogram') as mock_histogram, \
         patch('prometheus_client.Gauge') as mock_gauge:
        
        yield {
            "counter": mock_counter,
            "histogram": mock_histogram,
            "gauge": mock_gauge
        }

@pytest.fixture
def mock_cache():
    """模拟缓存"""
    cache_data = {}
    
    def get(key):
        return cache_data.get(key)
    
    def set(key, value, ttl=None):
        cache_data[key] = value
    
    def delete(key):
        cache_data.pop(key, None)
    
    def clear():
        cache_data.clear()
    
    with patch('src.owl_requirements.utils.cache.Cache') as mock_cache_class:
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.side_effect = get
        mock_cache_instance.set.side_effect = set
        mock_cache_instance.delete.side_effect = delete
        mock_cache_instance.clear.side_effect = clear
        mock_cache_class.return_value = mock_cache_instance
        yield mock_cache_instance

@pytest.fixture
def mock_rate_limiter():
    """模拟速率限制器"""
    with patch('src.owl_requirements.utils.rate_limiter.RateLimiter') as mock_limiter:
        mock_instance = MagicMock()
        mock_instance.is_allowed.return_value = True
        mock_instance.get_remaining.return_value = 100
        mock_limiter.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_security():
    """模拟安全组件"""
    with patch('src.owl_requirements.utils.security.SecurityManager') as mock_security:
        mock_instance = MagicMock()
        mock_instance.validate_input.return_value = True
        mock_instance.sanitize_output.side_effect = lambda x: x
        mock_instance.encrypt.side_effect = lambda x: f"encrypted_{x}"
        mock_instance.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
        mock_security.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    with patch('websockets.connect') as mock_connect:
        mock_websocket = MagicMock()
        mock_websocket.send = MagicMock()
        mock_websocket.recv = MagicMock()
        mock_websocket.close = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket
        yield mock_websocket

@pytest.fixture
def mock_async_client():
    """模拟异步HTTP客户端"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_instance.post.return_value = mock_response
        mock_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_analysis_result():
    """示例分析结果"""
    return {
        "requirements": [
            {
                "id": "REQ-001",
                "description": "用户可以通过用户名和密码登录系统",
                "category": "功能需求",
                "priority": "高",
                "complexity": "中",
                "effort_estimate": "2-3天",
                "dependencies": [],
                "risks": [
                    {
                        "description": "密码安全风险",
                        "probability": "中",
                        "impact": "高",
                        "mitigation": "实施强密码策略"
                    }
                ]
            },
            {
                "id": "REQ-002",
                "description": "用户可以重置忘记的密码",
                "category": "功能需求",
                "priority": "中",
                "complexity": "中",
                "effort_estimate": "1-2天",
                "dependencies": ["REQ-001"],
                "risks": []
            }
        ],
        "analysis": {
            "total_requirements": 2,
            "complexity_distribution": {
                "高": 0,
                "中": 2,
                "低": 0
            },
            "priority_distribution": {
                "高": 1,
                "中": 1,
                "低": 0
            },
            "category_distribution": {
                "功能需求": 2,
                "性能需求": 0,
                "安全需求": 0,
                "界面需求": 0
            },
            "total_effort_estimate": "3-5天",
            "risk_summary": {
                "high_risk_count": 1,
                "medium_risk_count": 0,
                "low_risk_count": 0
            }
        },
        "metadata": {
            "analysis_timestamp": "2025-01-XX",
            "analyzer_version": "1.0.0",
            "llm_model": "gpt-3.5-turbo",
            "processing_time": 2.5
        }
    }

@pytest.fixture
def performance_test_data():
    """性能测试数据"""
    return {
        "small_dataset": ["简单需求"] * 10,
        "medium_dataset": ["中等复杂度需求"] * 100,
        "large_dataset": ["复杂需求描述"] * 1000,
        "expected_response_times": {
            "small": 5.0,  # 5秒
            "medium": 30.0,  # 30秒
            "large": 120.0  # 2分钟
        }
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 设置测试环境变量
    os.environ["OWL_ENV"] = "test"
    os.environ["OWL_LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # 清理测试环境
    test_vars = ["OWL_ENV", "OWL_LOG_LEVEL"]
    for var in test_vars:
        os.environ.pop(var, None)

@pytest.fixture
def integration_test_config():
    """集成测试配置"""
    return {
        "test_timeout": 60,
        "max_retries": 3,
        "retry_delay": 1.0,
        "parallel_workers": 4,
        "test_data_size": 100,
        "mock_external_services": True,
        "enable_performance_monitoring": True,
        "cleanup_after_test": True
    }

# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
    config.addinivalue_line(
        "markers", "external: 需要外部服务的测试标记"
    )

# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为慢速测试添加标记
        if "test_performance" in item.name or "test_large" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # 为集成测试添加标记
        if "test_integration" in item.name or "test_full_workflow" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # 为需要外部服务的测试添加标记
        if "test_llm" in item.name or "test_api" in item.name:
            item.add_marker(pytest.mark.external) 