"""Test documentation generator."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from owl_requirements.agents.documentation_generator import DocumentationGenerator
from owl_requirements.core.exceptions import (
    DocumentationGenerationError,
    InvalidInputError,
    TemplateError
)
from owl_requirements.utils.exceptions import DocumentationError

# Test data
SAMPLE_REQUIREMENTS = {
    "project_name": "在线教育平台",
    "description": "开发一个现代化的在线教育平台",
    "functional_requirements": [
        {
            "category": "教师功能",
            "items": [
                "上传教学视频",
                "创建在线测验",
                "管理学生作业"
            ]
        }
    ],
    "non_functional_requirements": [
        {
            "category": "性能",
            "items": [
                "支持1000并发用户",
                "页面加载时间<2秒"
            ]
        }
    ]
}

SAMPLE_ANALYSIS = {
    "feasibility_score": 0.85,
    "complexity_score": 0.7,
    "risk_assessment": {
        "technical_risks": ["需要优化视频存储", "并发性能挑战"],
        "business_risks": ["市场竞争激烈"]
    },
    "resource_requirements": {
        "development_team": ["前端开发", "后端开发", "DevOps"],
        "infrastructure": ["云服务器", "CDN", "数据库"]
    }
}

SAMPLE_QUALITY_CHECK = {
    "completeness_score": 90,
    "clarity_score": 85,
    "consistency_score": 95,
    "recommendations": [
        "建议细化性能指标",
        "需要补充安全需求"
    ]
}

VALID_DOCUMENTATION = {
    "sections": [
        {
            "title": "项目概述",
            "content": "本文档描述了在线教育平台项目的需求规格说明。",
            "subsections": [
                {
                    "title": "项目目标",
                    "content": "开发一个高性能、易用的在线教育平台。"
                }
            ]
        }
    ],
    "metadata": {
        "title": "在线教育平台需求规格说明书",
        "version": "1.0.0",
        "date": "2024-03-20",
        "status": "初稿"
    }
}

# 测试数据路径
TEST_DATA_DIR = Path(__file__).parent / "test_data"

@pytest.fixture
def test_config():
    """测试配置。"""
    return {
        "name": "DocumentationGenerator",
        "description": "测试文档生成器",
        "version": "1.0.0",
        "llm_service": {
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 4000
        },
        "templates": {
            "template_dir": str(TEST_DATA_DIR / "templates")
        },
        "max_retries": 2
    }

@pytest.fixture
def test_requirements():
    """测试需求数据。"""
    with open(TEST_DATA_DIR / "test_requirements.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_analysis():
    """测试分析数据。"""
    with open(TEST_DATA_DIR / "test_analysis.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def test_quality_check():
    """测试质量检查数据。"""
    return {
        "质量评分": 88,
        "维度得分": {
            "完整性": 0.9,
            "清晰度": 0.85,
            "可测试性": 0.89,
            "一致性": 0.87,
            "可行性": 0.86,
            "依赖关系": 0.88
        },
        "问题列表": [
            {
                "类型": "清晰度问题",
                "需求编号": "FR-001",
                "描述": "需求描述不够具体"
            },
            {
                "类型": "可测试性问题",
                "需求编号": "NFR-001",
                "描述": "性能需求缺少具体的度量指标"
            }
        ],
        "改进建议": [
            "建议添加更详细的性能指标",
            "建议明确用户角色和权限"
        ],
        "检查类型": "规则检查 + LLM检查",
        "规则检查": {
            "使用规则": {
                "最低描述长度": 30,
                "最大依赖层级": 3,
                "高优先级需求比例": 0.4,
                "最低可行性分数": 0.6,
                "最大冲突数": 2
            }
        },
        "LLM检查": {
            "quality_score": 85,
            "issues": [
                {
                    "category": "清晰度",
                    "description": "需求描述不够具体",
                    "severity": "中"
                }
            ],
            "recommendations": [
                {
                    "category": "改进建议",
                    "description": "添加具体的性能指标",
                    "priority": "高"
                }
            ]
        }
    }

@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.generate = AsyncMock(return_value={
        "documentation": {
            "overview": "图书管理系统概述",
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "title": "用户登录",
                    "description": "系统应支持用户通过用户名和密码登录",
                    "acceptance_criteria": [
                        "用户可以输入用户名和密码",
                        "系统验证用户凭据",
                        "登录成功后跳转到主页"
                    ]
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "category": "性能",
                    "description": "系统响应时间应在2秒内",
                    "metrics": [
                        "95%的请求响应时间<2秒",
                        "99%的请求响应时间<5秒"
                    ]
                }
            ],
            "architecture": {
                "overview": "系统采用三层架构",
                "components": [
                    "前端界面层",
                    "业务逻辑层",
                    "数据访问层"
                ]
            }
        }
    })
    return mock

@pytest.fixture
def mock_config():
    """Create mock config."""
    return {
        "name": "documentation_generator",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }

@pytest.fixture
def generator(test_config, mock_llm_service):
    """文档生成器实例。"""
    return DocumentationGenerator(test_config)

@pytest.fixture
def test_template():
    """测试模板数据。"""
    with open(TEST_DATA_DIR / "test_template.json", "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def temp_template(tmp_path: Path) -> Path:
    """创建临时模板文件。"""
    template = {
        "version": "1.0.0",
        "sections": ["project", "requirements", "analysis", "quality"]
    }
    template_path = tmp_path / "template.json"
    with template_path.open('w', encoding='utf-8') as f:
        json.dump(template, f)
    return template_path

@pytest.fixture
def documentation_generator(test_template):
    """创建文档生成器实例。"""
    return DocumentationGenerator({
        "name": "documentation_generator",
        "template": test_template
    }, "test_output/docs")

@pytest.mark.asyncio
async def test_generate_documentation_success(mock_llm_service, mock_config):
    """Test successful documentation generation."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    requirements = {
        "functional_requirements": [
            {
                "id": "FR-001",
                "description": "系统应支持用户登录功能",
                "priority": "high"
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-001",
                "category": "性能",
                "description": "系统响应时间应在2秒内"
            }
        ]
    }
    
    result = await generator.process(requirements)
    
    assert isinstance(result, dict)
    assert "documentation" in result
    assert "overview" in result["documentation"]
    assert "functional_requirements" in result["documentation"]
    assert "non_functional_requirements" in result["documentation"]
    assert "architecture" in result["documentation"]

@pytest.mark.asyncio
async def test_generate_documentation_empty_requirements(mock_llm_service, mock_config):
    """Test documentation generation with empty requirements."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({})

@pytest.mark.asyncio
async def test_generate_documentation_invalid_requirements(mock_llm_service, mock_config):
    """Test documentation generation with invalid requirements."""
    generator = DocumentationGenerator(llm_service=mock_llm_service, config=mock_config)
    
    with pytest.raises(DocumentationError):
        await generator.process({"invalid": "data"})

@pytest.mark.asyncio
async def test_generate_documentation_invalid_input(generator):
    """测试无效输入。"""
    with pytest.raises(InvalidInputError):
        await generator.generate_documentation({}, {}, {})

@pytest.mark.asyncio
async def test_generate_documentation_missing_template(generator):
    """测试模板缺失。"""
    with patch("src.owl_requirements.utils.template_manager.TemplateManager") as mock:
        mock.return_value.get_template.return_value = None
        with pytest.raises(TemplateError):
            await generator.generate_documentation(
                {"project_info": {}},
                {"feasibility_score": 0.8},
                {"overall_quality_score": 0.9}
            )

@pytest.mark.asyncio
async def test_generate_documentation_llm_error(
    generator,
    test_requirements,
    test_analysis,
    test_quality_check
):
    """测试LLM服务错误。"""
    with patch("src.owl_requirements.services.llm_service.LLMService") as mock:
        mock.return_value.generate.side_effect = Exception("LLM服务错误")
        with pytest.raises(DocumentationGenerationError):
            await generator.generate_documentation(
                test_requirements,
                test_analysis,
                test_quality_check
            )

@pytest.mark.asyncio
async def test_save_documentation(generator, tmp_path):
    """测试保存文档。"""
    doc = {
        "project_overview": {
            "title": "测试项目",
            "description": "测试描述"
        }
    }
    output_path = tmp_path / "test_doc.json"
    await generator.save_documentation(doc, str(output_path))

    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as f:
        saved_doc = json.load(f)
    assert saved_doc == doc

@pytest.mark.asyncio
async def test_save_documentation_error(generator):
    """测试保存文档错误。"""
    with pytest.raises(DocumentationGenerationError):
        await generator.save_documentation({}, "/invalid/path/doc.json")

def test_validate_documentation_success(generator):
    """测试文档验证成功。"""
    doc = {
        "project_overview": {},
        "requirements_specification": {},
        "analysis_results": {},
        "quality_assessment": {},
        "recommendations": []
    }
    generator._validate_documentation(doc)  # 不应抛出异常

def test_validate_documentation_missing_sections(generator):
    """测试文档缺少必要部分。"""
    doc = {"project_overview": {}}
    with pytest.raises(DocumentationGenerationError):
        generator._validate_documentation(doc)

def test_validate_documentation_invalid_structure(generator):
    """测试文档结构无效。"""
    doc = {
        "project_overview": {},
        "requirements_specification": [],  # 应该是字典
        "analysis_results": {},
        "quality_assessment": {},
        "recommendations": []
    }
    with pytest.raises(DocumentationGenerationError):
        generator._validate_documentation(doc)

def test_prepare_input_data(generator):
    """测试输入数据准备。"""
    requirements = {
        "project_info": {"name": "测试项目"},
        "functional_requirements": [],
        "non_functional_requirements": []
    }
    analysis = {
        "feasibility_score": 0.8,
        "complexity_score": 0.7,
        "risk_assessment": {}
    }
    quality_check = {
        "overall_quality_score": 0.9,
        "quality_metrics": {},
        "improvement_suggestions": []
    }

    data = generator._prepare_input_data(
        requirements,
        analysis,
        quality_check
    )

    assert "project_info" in data
    assert "requirements" in data
    assert "analysis" in data
    assert "quality" in data

def test_extract_json_valid_json(generator):
    """Test _extract_json with valid JSON."""
    json_str = '```json\n{"test": "value"}\n```'
    result = generator._extract_json(json_str)
    assert result == {"test": "value"}

def test_extract_json_chinese_punctuation(generator):
    """Test _extract_json with Chinese punctuation."""
    json_str = '```json\n{"测试"："值"，"状态"："完成"}\n```'
    result = generator._extract_json(json_str)
    assert result == {"测试": "值", "状态": "完成"}

def test_extract_json_empty_response(generator):
    """Test _extract_json with empty response."""
    with pytest.raises(ValueError, match="Empty response from LLM"):
        generator._extract_json("")

def test_validate_result_valid_structure(generator):
    """Test _validate_result with valid structure."""
    assert generator._validate_result(VALID_DOCUMENTATION) is True

def test_validate_result_missing_required_fields(generator):
    """Test _validate_result with missing required fields."""
    invalid_doc = {
        "sections": []
        # Missing metadata
    }
    assert generator._validate_result(invalid_doc) is False

def test_validate_result_invalid_sections(generator):
    """Test _validate_result with invalid sections."""
    invalid_doc = {
        "sections": [
            {
                "title": "Test"
                # Missing content
            }
        ],
        "metadata": VALID_DOCUMENTATION["metadata"]
    }
    assert generator._validate_result(invalid_doc) is False

def test_validate_result_invalid_subsections(generator):
    """Test _validate_result with invalid subsections."""
    invalid_doc = {
        "sections": [
            {
                "title": "Test",
                "content": "Content",
                "subsections": [
                    {
                        "title": "Subsection"
                        # Missing content
                    }
                ]
            }
        ],
        "metadata": VALID_DOCUMENTATION["metadata"]
    }
    assert generator._validate_result(invalid_doc) is False

def test_validate_result_invalid_metadata(generator):
    """Test _validate_result with invalid metadata."""
    invalid_doc = {
        "sections": VALID_DOCUMENTATION["sections"],
        "metadata": {
            "title": "Test"
            # Missing other required fields
        }
    }
    assert generator._validate_result(invalid_doc) is False

async def test_generate_documentation(
    documentation_generator,
    test_requirements,
    test_analysis,
    test_quality_check
):
    """测试生成文档。"""
    result = await documentation_generator.process({
        "requirements": test_requirements,
        "analysis": test_analysis,
        "quality_check": test_quality_check
    })
    
    assert result is not None
    assert "documents" in result
    assert len(result["documents"]) > 0
    
    # 验证生成的文档
    for doc in result["documents"]:
        assert isinstance(doc, str)
        assert doc.endswith(".md")
        assert Path(doc).exists()

async def test_generate_documentation_with_invalid_input(documentation_generator):
    """测试使用无效输入生成文档。"""
    with pytest.raises(ValueError):
        await documentation_generator.process({})

async def test_generate_documentation_with_missing_fields(
    documentation_generator,
    test_requirements,
    test_analysis
):
    """测试缺少字段时生成文档。"""
    with pytest.raises(ValueError):
        await documentation_generator.process({
            "requirements": test_requirements,
            "analysis": test_analysis
        })

async def test_generate_documentation_with_custom_template(
    documentation_generator,
    test_requirements,
    test_analysis,
    test_quality_check,
    temp_template
):
    """测试使用自定义模板生成文档。"""
    documentation_generator.config["template"] = temp_template
    
    result = await documentation_generator.process({
        "requirements": test_requirements,
        "analysis": test_analysis,
        "quality_check": test_quality_check
    })
    
    assert result is not None
    assert "documents" in result
    assert len(result["documents"]) > 0 