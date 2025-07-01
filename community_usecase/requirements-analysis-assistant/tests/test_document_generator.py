"""
Tests for the document generator agent
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
from owl_requirements.agents.documentation import DocumentGeneratorAgent
from owl_requirements.utils.document_toolkit import DocumentGenerator

@pytest.fixture
def mock_doc_generator():
    """Mock document generator"""
    generator = MagicMock(spec=DocumentGenerator)
    generator.generate = AsyncMock()
    generator.templates = {
        "executive_summary": AsyncMock(),
        "requirements_spec": AsyncMock(),
        "technical_design": AsyncMock(),
        "implementation_plan": AsyncMock(),
        "risk_assessment": AsyncMock(),
        "test_plan": AsyncMock(),
        "traceability_matrix": AsyncMock()
    }
    return generator

@pytest.fixture
def document_generator(mock_doc_generator):
    """Document generator agent fixture"""
    with patch('owl_requirements.agents.documentation.DocumentGenerator', return_value=mock_doc_generator):
        config = {
            "output_dir": "test_output/docs"
        }
        agent = DocumentGeneratorAgent(config)
        yield agent

@pytest.mark.asyncio
async def test_generate_documentation(document_generator, mock_doc_generator):
    """Test generating comprehensive documentation"""
    # Setup
    requirements = [{"id": "REQ-001", "title": "Test Requirement"}]
    validation_results = [{"finding": "Test Finding"}]
    expected_docs = {
        "executive_summary": "Test Summary",
        "requirements_spec": "Test Spec"
    }
    mock_doc_generator.generate.return_value = expected_docs
    
    # Execute
    result = await document_generator.generate_documentation(requirements, validation_results)
    
    # Verify
    assert result == expected_docs
    mock_doc_generator.generate.assert_called_once_with(requirements, validation_results)

@pytest.mark.asyncio
async def test_update_documentation(document_generator, mock_doc_generator):
    """Test updating specific sections of documentation"""
    # Setup
    requirements = [{"id": "REQ-001", "title": "Test Requirement"}]
    validation_results = [{"finding": "Test Finding"}]
    changed_sections = ["executive_summary", "requirements_spec"]
    mock_doc_generator.templates["executive_summary"].return_value = "Updated Summary"
    mock_doc_generator.templates["requirements_spec"].return_value = "Updated Spec"
    
    # Execute
    result = await document_generator.update_documentation(requirements, validation_results, changed_sections)
    
    # Verify
    assert result == {
        "executive_summary": "Updated Summary",
        "requirements_spec": "Updated Spec"
    }
    mock_doc_generator.templates["executive_summary"].assert_called_once_with(requirements, validation_results)
    mock_doc_generator.templates["requirements_spec"].assert_called_once_with(requirements, validation_results)

@pytest.mark.asyncio
async def test_generate_summary(document_generator, mock_doc_generator):
    """Test generating a brief summary"""
    # Setup
    requirements = [{"id": "REQ-001", "title": "Test Requirement"}]
    validation_results = [{"finding": "Test Finding"}]
    mock_doc_generator.templates["executive_summary"].return_value = "Test Summary"
    
    # Execute
    result = await document_generator.generate_summary(requirements, validation_results)
    
    # Verify
    assert result == "Test Summary"
    mock_doc_generator.templates["executive_summary"].assert_called_once_with(requirements, validation_results)

@pytest.mark.asyncio
async def test_generate_report(document_generator, mock_doc_generator):
    """Test generating a specific report"""
    # Setup
    requirements = [{"id": "REQ-001", "title": "Test Requirement"}]
    validation_results = [{"finding": "Test Finding"}]
    report_type = "technical_design"
    mock_doc_generator.templates[report_type].return_value = "Test Report"
    
    # Execute
    result = await document_generator.generate_report(requirements, validation_results, report_type)
    
    # Verify
    assert result == "Test Report"
    mock_doc_generator.templates[report_type].assert_called_once_with(requirements, validation_results)

@pytest.mark.asyncio
async def test_generate_report_invalid_type(document_generator):
    """Test generating a report with invalid type"""
    # Setup
    requirements = [{"id": "REQ-001", "title": "Test Requirement"}]
    validation_results = [{"finding": "Test Finding"}]
    invalid_report_type = "invalid_type"
    
    # Execute and verify
    with pytest.raises(ValueError, match=f"Unknown report type: {invalid_report_type}"):
        await document_generator.generate_report(requirements, validation_results, invalid_report_type)

@pytest.mark.asyncio
async def test_save_documents(document_generator):
    """Test saving documents to files"""
    # Setup
    docs = {
        "executive_summary": "Test Summary",
        "requirements_spec": "Test Spec"
    }
    output_dir = "test_output/docs"
    
    # Execute
    await document_generator._save_documents(docs)
    
    # Verify
    assert os.path.exists(output_dir)
    for doc_type in docs:
        file_path = os.path.join(output_dir, f"{doc_type}.md")
        assert os.path.exists(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == docs[doc_type]
            
    # Cleanup
    import shutil
    shutil.rmtree("test_output") 