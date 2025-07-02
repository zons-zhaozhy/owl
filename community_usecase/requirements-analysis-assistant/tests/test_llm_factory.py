"""
LLM 工厂测试模块
"""
import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from src.owl_requirements.core.config import Config, LLMConfig
from src.owl_requirements.services.llm_factory import LLMFactory
from src.owl_requirements.core.exceptions import ConfigurationError, LLMError

class TestLLMFactory:
    """LLM 工厂测试类"""
    
    async def test_create_openai_service(self, test_config: Dict[str, Any], mock_openai):
        """测试创建 OpenAI 服务"""
        config = Config()
        config.load_from_dict(test_config)
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("openai")
        
        assert service is not None
        assert service.provider == "openai"
        
        # 测试文本生成
        response = await service.generate_text("测试提示")
        assert isinstance(response, str)
        assert len(response) > 0
        
        # 测试流式生成
        chunks = []
        async for chunk in service.generate_stream("测试提示"):
            chunks.append(chunk)
        assert len(chunks) > 0
        
    async def test_create_anthropic_service(self, test_config: Dict[str, Any], mock_anthropic):
        """测试创建 Anthropic 服务"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.provider = "anthropic"
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("anthropic")
        
        assert service is not None
        assert service.provider == "anthropic"
        
        # 测试文本生成
        response = await service.generate_text("测试提示")
        assert isinstance(response, str)
        assert len(response) > 0
        
    async def test_create_azure_service(self, test_config: Dict[str, Any], mock_azure):
        """测试创建 Azure OpenAI 服务"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.provider = "azure"
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("azure")
        
        assert service is not None
        assert service.provider == "azure"
        
        # 测试文本生成
        response = await service.generate_text("测试提示")
        assert isinstance(response, str)
        assert len(response) > 0
        
    async def test_invalid_provider(self, test_config: Dict[str, Any]):
        """测试无效的提供商"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.provider = "invalid"
        
        factory = LLMFactory(config.llm)
        with pytest.raises(ConfigurationError):
            await factory.create_service("invalid")
            
    async def test_missing_api_key(self, test_config: Dict[str, Any]):
        """测试缺少 API 密钥"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.api_key = None
        
        factory = LLMFactory(config.llm)
        with pytest.raises(ConfigurationError):
            await factory.create_service("openai")
            
    async def test_rate_limiting(self, test_config: Dict[str, Any], mock_openai):
        """测试速率限制"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.rate_limit = 2  # 每秒 2 个请求
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("openai")
        
        # 发送多个请求
        import asyncio
        tasks = [service.generate_text("测试提示") for _ in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证部分请求被限制
        success = sum(1 for r in responses if isinstance(r, str))
        limited = sum(1 for r in responses if isinstance(r, LLMError))
        
        assert success > 0
        assert limited > 0
        assert success + limited == 5
        
    async def test_context_length(self, test_config: Dict[str, Any], mock_openai):
        """测试上下文长度限制"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.max_tokens = 100
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("openai")
        
        # 生成长文本
        long_text = "测试" * 1000
        
        # 验证长文本被截断
        response = await service.generate_text(long_text)
        assert len(response) < len(long_text)
        
    async def test_retry_mechanism(self, test_config: Dict[str, Any]):
        """测试重试机制"""
        config = Config()
        config.load_from_dict(test_config)
        
        # 模拟间歇性失败
        mock_service = MagicMock()
        mock_service.generate_text.side_effect = [
            LLMError("API Error"),
            LLMError("Rate Limit"),
            "成功响应"
        ]
        
        with patch("src.owl_requirements.services.llm_factory.OpenAIService", return_value=mock_service):
            factory = LLMFactory(config.llm)
            service = await factory.create_service("openai")
            
            # 应该在第三次尝试时成功
            response = await service.generate_text("测试提示")
            assert response == "成功响应"
            assert mock_service.generate_text.call_count == 3
            
    async def test_streaming_timeout(self, test_config: Dict[str, Any], mock_openai):
        """测试流式传输超时"""
        config = Config()
        config.load_from_dict(test_config)
        config.llm.stream_timeout = 1  # 1 秒超时
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("openai")
        
        # 模拟慢速流
        async def slow_stream():
            import asyncio
            yield "第一部分"
            await asyncio.sleep(2)  # 超过超时时间
            yield "第二部分"
            
        with patch.object(service, "generate_stream", return_value=slow_stream()):
            chunks = []
            with pytest.raises(asyncio.TimeoutError):
                async for chunk in service.generate_stream("测试提示"):
                    chunks.append(chunk)
                    
            assert len(chunks) == 1
            assert chunks[0] == "第一部分"
            
    async def test_concurrent_requests(self, test_config: Dict[str, Any], mock_openai):
        """测试并发请求"""
        config = Config()
        config.load_from_dict(test_config)
        
        factory = LLMFactory(config.llm)
        service = await factory.create_service("openai")
        
        # 并发发送多个请求
        import asyncio
        tasks = [service.generate_text(f"测试提示 {i}") for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 10
        assert all(isinstance(r, str) for r in responses)
        
    async def test_error_handling(self, test_config: Dict[str, Any]):
        """测试错误处理"""
        config = Config()
        config.load_from_dict(test_config)
        
        factory = LLMFactory(config.llm)
        
        # 测试网络错误
        with patch("openai.ChatCompletion.create", side_effect=ConnectionError):
            with pytest.raises(LLMError) as exc_info:
                service = await factory.create_service("openai")
                await service.generate_text("测试提示")
            assert "网络错误" in str(exc_info.value)
            
        # 测试认证错误
        with patch("openai.ChatCompletion.create", side_effect=ValueError("Invalid API key")):
            with pytest.raises(LLMError) as exc_info:
                service = await factory.create_service("openai")
                await service.generate_text("测试提示")
            assert "认证错误" in str(exc_info.value)
            
        # 测试速率限制错误
        with patch("openai.ChatCompletion.create", side_effect=Exception("Rate limit exceeded")):
            with pytest.raises(LLMError) as exc_info:
                service = await factory.create_service("openai")
                await service.generate_text("测试提示")
            assert "速率限制" in str(exc_info.value)
            
    async def test_configuration_validation(self, test_config: Dict[str, Any]):
        """测试配置验证"""
        config = Config()
        config.load_from_dict(test_config)
        
        # 测试无效的模型名称
        config.llm.model = "invalid-model"
        with pytest.raises(ConfigurationError) as exc_info:
            factory = LLMFactory(config.llm)
            await factory.create_service("openai")
        assert "无效的模型" in str(exc_info.value)
        
        # 测试无效的温度值
        config.llm.temperature = 2.0
        with pytest.raises(ConfigurationError) as exc_info:
            factory = LLMFactory(config.llm)
            await factory.create_service("openai")
        assert "温度值必须在 0-1 之间" in str(exc_info.value)
        
        # 测试无效的最大令牌数
        config.llm.max_tokens = -1
        with pytest.raises(ConfigurationError) as exc_info:
            factory = LLMFactory(config.llm)
            await factory.create_service("openai")
        assert "最大令牌数必须为正数" in str(exc_info.value) 