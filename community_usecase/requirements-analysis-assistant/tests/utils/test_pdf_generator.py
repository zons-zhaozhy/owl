"""
Test PDF generator
"""
import pytest
from pathlib import Path
import json
from src.utils.pdf_generator import PDFGenerator

@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        "executive_summary": "这是一个测试用的执行摘要。",
        "analysis": {
            "core_requirements": [
                "需求1: 实现基本功能",
                "需求2: 确保系统安全"
            ],
            "dependencies": [
                "依赖1: Python 3.8+",
                "依赖2: WeasyPrint"
            ],
            "feasibility": "系统在技术上完全可行。"
        },
        "risks": [
            {
                "title": "技术风险",
                "severity": "中等",
                "probability": "低",
                "description": "可能存在技术实现难度。",
                "mitigation": [
                    "提前进行技术验证",
                    "准备备选方案"
                ]
            }
        ],
        "recommendations": [
            {
                "title": "架构建议",
                "priority": "高",
                "description": "采用模块化架构设计。",
                "steps": [
                    "定义模块边界",
                    "实现接口规范",
                    "编写单元测试"
                ]
            }
        ],
        "diagrams": {
            "system_architecture": "graph TD;\nA-->B;",
            "data_flow": "sequenceDiagram;\nA->>B: Hello;"
        },
        "validation": {
            "is_valid": True,
            "errors": []
        }
    }

@pytest.fixture
def pdf_generator():
    """PDF generator instance"""
    return PDFGenerator()

@pytest.fixture
def output_path(tmp_path):
    """Temporary output path"""
    return tmp_path / "test_output.pdf"

@pytest.mark.asyncio
async def test_generate_pdf(pdf_generator, sample_content, output_path):
    """Test PDF generation"""
    # Generate PDF
    await pdf_generator.generate(sample_content, output_path)
    
    # Check if file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_generate_pdf_minimal_content(pdf_generator, output_path):
    """Test PDF generation with minimal content"""
    minimal_content = {
        "executive_summary": "最小化测试内容。"
    }
    
    # Generate PDF
    await pdf_generator.generate(minimal_content, output_path)
    
    # Check if file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_generate_pdf_empty_content(pdf_generator, output_path):
    """Test PDF generation with empty content"""
    empty_content = {}
    
    # Generate PDF
    await pdf_generator.generate(empty_content, output_path)
    
    # Check if file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_generate_pdf_nested_directory(pdf_generator, sample_content, tmp_path):
    """Test PDF generation in nested directory"""
    nested_path = tmp_path / "nested" / "dir" / "test.pdf"
    
    # Generate PDF
    await pdf_generator.generate(sample_content, nested_path)
    
    # Check if file exists
    assert nested_path.exists()
    assert nested_path.stat().st_size > 0

def test_generate_html_content(pdf_generator, sample_content):
    """Test HTML content generation"""
    html_content = pdf_generator._generate_html_content(sample_content)
    
    # Check basic structure
    assert "<!DOCTYPE html>" in html_content
    assert "<title>需求分析报告</title>" in html_content
    assert "执行摘要" in html_content
    assert "分析详情" in html_content
    assert "风险评估" in html_content
    assert "建议" in html_content
    assert "系统图表" in html_content
    assert "验证结果" in html_content

def test_generate_toc(pdf_generator, sample_content):
    """Test table of contents generation"""
    toc = pdf_generator._generate_toc(sample_content)
    
    # Check TOC structure
    assert any("目录" in item for item in toc)
    assert any("执行摘要" in item for item in toc)
    assert any("分析详情" in item for item in toc)
    assert any("风险评估" in item for item in toc)
    assert any("建议" in item for item in toc)
    assert any("系统图表" in item for item in toc)
    assert any("验证结果" in item for item in toc)

def test_format_analysis(pdf_generator, sample_content):
    """Test analysis section formatting"""
    analysis = pdf_generator._format_analysis(sample_content["analysis"])
    
    # Check analysis structure
    assert any("分析详情" in item for item in analysis)
    assert any("核心需求" in item for item in analysis)
    assert any("依赖和约束" in item for item in analysis)
    assert any("技术可行性" in item for item in analysis)

def test_format_risks(pdf_generator, sample_content):
    """Test risks section formatting"""
    risks = pdf_generator._format_risks(sample_content["risks"])
    
    # Check risks structure
    assert any("风险评估" in item for item in risks)
    assert any("技术风险" in item for item in risks)
    assert any("severity" in item.lower() for item in risks)
    assert any("probability" in item.lower() for item in risks)

def test_format_recommendations(pdf_generator, sample_content):
    """Test recommendations section formatting"""
    recommendations = pdf_generator._format_recommendations(sample_content["recommendations"])
    
    # Check recommendations structure
    assert any("建议" in item for item in recommendations)
    assert any("架构建议" in item for item in recommendations)
    assert any("priority" in item.lower() for item in recommendations)
    assert any("steps" in item.lower() for item in recommendations)

def test_format_diagrams(pdf_generator, sample_content):
    """Test diagrams section formatting"""
    diagrams = pdf_generator._format_diagrams(sample_content["diagrams"])
    
    # Check diagrams structure
    assert any("系统图表" in item for item in diagrams)
    assert any("System Architecture" in item for item in diagrams)
    assert any("Data Flow" in item for item in diagrams)

def test_format_validation(pdf_generator, sample_content):
    """Test validation section formatting"""
    validation = pdf_generator._format_validation(sample_content["validation"])
    
    # Check validation structure
    assert any("验证结果" in item for item in validation)
    assert any("✅" in item for item in validation)  # Success case

def test_format_validation_with_errors(pdf_generator):
    """Test validation section formatting with errors"""
    validation_data = {
        "is_valid": False,
        "errors": ["错误1", "错误2"]
    }
    
    validation = pdf_generator._format_validation(validation_data)
    
    # Check validation structure
    assert any("验证结果" in item for item in validation)
    assert any("❌" in item for item in validation)  # Error case
    assert any("错误1" in item for item in validation)
    assert any("错误2" in item for item in validation)

def test_format_list(pdf_generator):
    """Test list formatting"""
    items = ["项目1", "项目2", "项目3"]
    formatted_list = pdf_generator._format_list(items)
    
    # Check list structure
    assert formatted_list.startswith("<ul>")
    assert formatted_list.endswith("</ul>")
    assert all(f"<li>{item}</li>" in formatted_list for item in items)

# Error Handling Tests

@pytest.mark.asyncio
async def test_generate_pdf_invalid_path(pdf_generator, sample_content):
    """Test PDF generation with invalid output path"""
    # Try to generate PDF in a non-existent root directory
    invalid_path = Path("/nonexistent/directory/test.pdf")
    
    with pytest.raises(PermissionError):
        await pdf_generator.generate(sample_content, invalid_path)

@pytest.mark.asyncio
async def test_generate_pdf_invalid_content(pdf_generator, output_path):
    """Test PDF generation with invalid content"""
    invalid_content = {
        "executive_summary": 123,  # Should be string
        "analysis": "not a dict",  # Should be dict
        "risks": "not a list",  # Should be list
        "validation": None  # Should be dict
    }
    
    with pytest.raises(TypeError):
        await pdf_generator.generate(invalid_content, output_path)

@pytest.mark.asyncio
async def test_generate_pdf_missing_template(monkeypatch, pdf_generator, sample_content, output_path):
    """Test PDF generation with missing template"""
    # Simulate missing template by setting it to None
    monkeypatch.setattr(pdf_generator, "template", None)
    
    with pytest.raises(ValueError, match="Template not initialized"):
        await pdf_generator.generate(sample_content, output_path)

@pytest.mark.asyncio
async def test_generate_pdf_weasyprint_error(monkeypatch, pdf_generator, sample_content, output_path):
    """Test PDF generation with WeasyPrint error"""
    def mock_write_pdf(*args, **kwargs):
        raise Exception("WeasyPrint error")
    
    # Patch HTML.write_pdf method
    monkeypatch.setattr("weasyprint.HTML.write_pdf", mock_write_pdf)
    
    with pytest.raises(Exception, match="WeasyPrint error"):
        await pdf_generator.generate(sample_content, output_path)

@pytest.mark.asyncio
async def test_generate_pdf_directory_creation_error(monkeypatch, pdf_generator, sample_content, tmp_path):
    """Test PDF generation with directory creation error"""
    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Cannot create directory")
    
    # Create a path in a directory that will fail to be created
    output_path = tmp_path / "nested" / "dir" / "test.pdf"
    
    # Patch Path.mkdir method
    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    
    with pytest.raises(PermissionError, match="Cannot create directory"):
        await pdf_generator.generate(sample_content, output_path)

def test_format_list_invalid_items(pdf_generator):
    """Test list formatting with invalid items"""
    invalid_items = [123, None, {"key": "value"}]  # Should be strings
    
    with pytest.raises(TypeError):
        pdf_generator._format_list(invalid_items)

def test_format_validation_invalid_data(pdf_generator):
    """Test validation formatting with invalid data"""
    invalid_data = {
        "is_valid": "not a boolean",  # Should be boolean
        "errors": "not a list"  # Should be list
    }
    
    with pytest.raises(TypeError):
        pdf_generator._format_validation(invalid_data)

def test_format_risks_invalid_data(pdf_generator):
    """Test risks formatting with invalid data"""
    invalid_risks = [
        {
            "title": 123,  # Should be string
            "severity": None,  # Should be string
            "probability": ["not", "a", "string"],  # Should be string
            "description": {"not": "a string"},  # Should be string
            "mitigation": "not a list"  # Should be list
        }
    ]
    
    with pytest.raises(TypeError):
        pdf_generator._format_risks(invalid_risks)

def test_format_recommendations_invalid_data(pdf_generator):
    """Test recommendations formatting with invalid data"""
    invalid_recommendations = [
        {
            "title": 123,  # Should be string
            "priority": None,  # Should be string
            "description": ["not", "a", "string"],  # Should be string
            "steps": "not a list"  # Should be list
        }
    ]
    
    with pytest.raises(TypeError):
        pdf_generator._format_recommendations(invalid_recommendations)

def test_format_diagrams_invalid_data(pdf_generator):
    """Test diagrams formatting with invalid data"""
    invalid_diagrams = {
        "diagram1": 123,  # Should be string
        "diagram2": None,  # Should be string
        "diagram3": ["not", "a", "string"]  # Should be string
    }
    
    with pytest.raises(TypeError):
        pdf_generator._format_diagrams(invalid_diagrams) 