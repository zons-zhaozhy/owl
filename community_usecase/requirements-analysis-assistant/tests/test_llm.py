"""
LLM 服务测试模块
"""
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from src.owl_requirements.services.llm import LLMService
from src.owl_requirements.core.config import Config
from src.owl_requirements.core.exceptions import LLMError

class TestLLMService:
    """LLM 服务测试类"""
    
    def test_initialization(self, test_config: Dict[str, Any]):
        """测试服务初始化"""
        service = LLMService(Config(**test_config))
        assert service.provider is not None
        assert service.model is not None
        assert service.temperature is not None
        
    def test_analyze_requirements(self, test_config: Dict[str, Any]):
        """测试需求分析"""
        service = LLMService(Config(**test_config))
        
        result = service.analyze_requirements("创建一个用户登录系统")
        
        assert "requirements" in result
        assert "analysis" in result
        assert isinstance(result["requirements"], list)
        assert isinstance(result["analysis"], dict)
        
    def test_provider_selection(self, test_config: Dict[str, Any]):
        """测试提供商选择"""
        # OpenAI
        config = Config(**test_config)
        config.llm_provider = "openai"
        service = LLMService(config)
        assert service.provider == "openai"
        
        # Anthropic
        config.llm_provider = "anthropic"
        service = LLMService(config)
        assert service.provider == "anthropic"
        
        # Azure
        config.llm_provider = "azure"
        service = LLMService(config)
        assert service.provider == "azure"
        
    def test_model_selection(self, test_config: Dict[str, Any]):
        """测试模型选择"""
        config = Config(**test_config)
        
        # GPT-4
        config.llm_model = "gpt-4"
        service = LLMService(config)
        assert service.model == "gpt-4"
        
        # GPT-3.5
        config.llm_model = "gpt-3.5-turbo"
        service = LLMService(config)
        assert service.model == "gpt-3.5-turbo"
        
        # Claude
        config.llm_provider = "anthropic"
        config.llm_model = "claude-2"
        service = LLMService(config)
        assert service.model == "claude-2"
        
    def test_temperature_setting(self, test_config: Dict[str, Any]):
        """测试温度设置"""
        config = Config(**test_config)
        
        # 默认温度
        service = LLMService(config)
        assert 0 <= service.temperature <= 1
        
        # 自定义温度
        config.llm_temperature = 0.8
        service = LLMService(config)
        assert service.temperature == 0.8
        
    def test_context_length(self, test_config: Dict[str, Any]):
        """测试上下文长度"""
        service = LLMService(Config(**test_config))
        
        # 正常长度
        result = service.analyze_requirements("简单的需求文本")
        assert "requirements" in result
        
        # 超长文本
        long_text = "需求" * 10000
        with pytest.raises(LLMError) as exc:
            service.analyze_requirements(long_text)
        assert "超出最大长度" in str(exc.value)
        
    def test_retry_mechanism(self, test_config: Dict[str, Any]):
        """测试重试机制"""
        service = LLMService(Config(**test_config))
        
        # 模拟临时错误
        with patch.object(
            service,
            "_call_llm",
            side_effect=[
                Exception("临时错误"),
                {"requirements": [], "analysis": {}}
            ]
        ):
            result = service.analyze_requirements("测试需求")
            assert "requirements" in result
            
    def test_streaming_response(self, test_config: Dict[str, Any]):
        """测试流式响应"""
        config = Config(**test_config)
        config.llm_stream = True
        service = LLMService(config)
        
        chunks = []
        for chunk in service.analyze_requirements_stream("测试需求"):
            chunks.append(chunk)
            
        assert len(chunks) > 0
        assert isinstance(chunks[-1], dict)
        assert "requirements" in chunks[-1]
        
    def test_timeout_handling(self, test_config: Dict[str, Any]):
        """测试超时处理"""
        config = Config(**test_config)
        config.llm_timeout = 1
        service = LLMService(config)
        
        # 模拟超时
        with patch.object(
            service,
            "_call_llm",
            side_effect=TimeoutError
        ):
            with pytest.raises(LLMError) as exc:
                service.analyze_requirements("测试需求")
            assert "超时" in str(exc.value)
            
    def test_rate_limiting(self, test_config: Dict[str, Any]):
        """测试速率限制"""
        config = Config(**test_config)
        config.llm_rate_limit = 2
        service = LLMService(config)
        
        # 快速发送多个请求
        for _ in range(3):
            service.analyze_requirements("测试需求")
            
        with pytest.raises(LLMError) as exc:
            service.analyze_requirements("测试需求")
        assert "速率限制" in str(exc.value)
        
    def test_concurrent_requests(self, test_config: Dict[str, Any]):
        """测试并发请求"""
        import asyncio
        
        service = LLMService(Config(**test_config))
        
        async def analyze():
            return await service.analyze_requirements_async("测试需求")
            
        async def test_concurrent():
            tasks = [analyze() for _ in range(3)]
            results = await asyncio.gather(*tasks)
            return results
            
        results = asyncio.run(test_concurrent())
        assert len(results) == 3
        assert all("requirements" in r for r in results)
        
    def test_error_handling(self, test_config: Dict[str, Any]):
        """测试错误处理"""
        service = LLMService(Config(**test_config))
        
        # API 错误
        with patch.object(
            service,
            "_call_llm",
            side_effect=Exception("API错误")
        ):
            with pytest.raises(LLMError) as exc:
                service.analyze_requirements("测试需求")
            assert "API错误" in str(exc.value)
            
        # 无效的响应
        with patch.object(
            service,
            "_call_llm",
            return_value={"invalid": "response"}
        ):
            with pytest.raises(LLMError) as exc:
                service.analyze_requirements("测试需求")
            assert "无效的响应" in str(exc.value)
            
    def test_prompt_templates(self, test_config: Dict[str, Any]):
        """测试提示模板"""
        service = LLMService(Config(**test_config))
        
        # 默认模板
        result = service.analyze_requirements("测试需求")
        assert "requirements" in result
        
        # 自定义模板
        config = Config(**test_config)
        config.llm_prompt_template = "分析以下需求：{input}"
        service = LLMService(config)
        
        result = service.analyze_requirements("测试需求")
        assert "requirements" in result
        
    def test_response_validation(self, test_config: Dict[str, Any]):
        """测试响应验证"""
        service = LLMService(Config(**test_config))
        
        # 有效响应
        valid_response = {
            "requirements": [
                {"id": 1, "description": "需求1"},
                {"id": 2, "description": "需求2"}
            ],
            "analysis": {
                "complexity": "中等",
                "priority": "高"
            }
        }
        
        with patch.object(
            service,
            "_call_llm",
            return_value=valid_response
        ):
            result = service.analyze_requirements("测试需求")
            assert result == valid_response
            
        # 无效响应
        invalid_response = {
            "requirements": "不是列表",
            "analysis": "不是字典"
        }
        
        with patch.object(
            service,
            "_call_llm",
            return_value=invalid_response
        ):
            with pytest.raises(LLMError) as exc:
                service.analyze_requirements("测试需求")
            assert "响应格式无效" in str(exc.value)
            
    def test_cost_tracking(self, test_config: Dict[str, Any]):
        """测试成本跟踪"""
        service = LLMService(Config(**test_config))
        
        # 记录初始成本
        initial_cost = service.total_cost
        
        # 发送请求
        service.analyze_requirements("测试需求")
        
        # 验证成本增加
        assert service.total_cost > initial_cost
        
        # 验证成本计算
        assert service.calculate_cost("测试需求") > 0
        
    def test_model_capabilities(self, test_config: Dict[str, Any]):
        """测试模型能力"""
        service = LLMService(Config(**test_config))
        
        # 测试多语言支持
        result = service.analyze_requirements("Create a login system")
        assert "requirements" in result
        
        result = service.analyze_requirements("创建登录系统")
        assert "requirements" in result
        
        # 测试复杂需求分析
        complex_req = """
        创建一个电子商务平台：
        1. 用户管理
        2. 商品管理
        3. 订单处理
        4. 支付集成
        5. 物流跟踪
        """
        result = service.analyze_requirements(complex_req)
        assert len(result["requirements"]) >= 5
        assert "complexity" in result["analysis"]
        
    def test_response_formatting(self, test_config: Dict[str, Any]):
        """测试响应格式化"""
        service = LLMService(Config(**test_config))
        
        # JSON 格式
        result = service.analyze_requirements(
            "测试需求",
            output_format="json"
        )
        assert isinstance(result, dict)
        
        # Markdown 格式
        result = service.analyze_requirements(
            "测试需求",
            output_format="markdown"
        )
        assert isinstance(result, str)
        assert "# " in result
        
    def test_context_management(self, test_config: Dict[str, Any]):
        """测试上下文管理"""
        service = LLMService(Config(**test_config))
        
        # 设置上下文
        service.set_context({"project": "测试项目"})
        
        # 验证上下文影响
        result1 = service.analyze_requirements("添加用户功能")
        
        # 清除上下文
        service.clear_context()
        result2 = service.analyze_requirements("添加用户功能")
        
        assert result1 != result2
        
    def test_performance_monitoring(self, test_config: Dict[str, Any]):
        """测试性能监控"""
        service = LLMService(Config(**test_config))
        
        # 记录性能指标
        with service.monitor_performance() as stats:
            service.analyze_requirements("测试需求")
            
        assert "response_time" in stats
        assert "token_count" in stats
        assert "cost" in stats 