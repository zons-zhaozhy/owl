import pytest
from unittest.mock import AsyncMock, MagicMock
from src.agents.quality_checker import QualityCheckerAgent
from src.llm.llm_service import LLMService
from datetime import datetime
import json

@pytest.fixture
def llm_service():
    service = MagicMock(spec=LLMService)
    service.get_completion = AsyncMock()
    return service

@pytest.fixture
def quality_checker(llm_service):
    config = {
        "name": "TestQualityChecker",
        "description": "Test quality checker",
        "check_model": "test-model",
        "quality_threshold": 0.8
    }
    return QualityCheckerAgent(
        name=config["name"],
        description=config["description"],
        config=config,
        llm_service=llm_service
    )

@pytest.mark.asyncio
async def test_process_quality_check(quality_checker, llm_service):
    # Prepare test data
    test_requirements = [
        {"id": "REQ-001", "description": "Clear and testable requirement"}
    ]
    test_analysis_results = {"overall_analysis": "Good"}
    test_documents = {"requirements_spec": "Doc content"}

    # Set LLM service mock return values
    llm_service.get_completion.side_effect = [
        ('{"score": 0.9, "issues": []}', None),  # completeness
        ('{"score": 0.9, "issues": []}', None),  # clarity
        ('{"score": 0.9, "issues": []}', None),  # testability
        ('{"consistency_status": "consistent"}', None), # consistency
        ('{"identified_issues": []}', None), # identify_issues
        ('{"improvement_suggestions": []}', None) # generate_improvements
    ]

    # Execute the process
    result = await quality_checker.process(
        test_requirements,
        test_analysis_results,
        test_documents
    )

    # Assertions
    assert "quality_score" in result
    assert "consistency_check" in result
    assert "identified_issues" in result
    assert "improvement_suggestions" in result
    assert "checked_at" in result
    assert quality_checker.get_state() == 'ready'
    assert quality_checker.check_results == result

@pytest.mark.asyncio
async def test_check_requirements_quality(quality_checker, llm_service):
    test_requirements = [{"id": "REQ-001", "description": "Test"}]
    llm_service.get_completion.side_effect = [
        ('{"score": 0.9}', None), # completeness
        ('{"score": 0.8}', None), # clarity
        ('{"score": 0.7}', None)  # testability
    ]

    result = await quality_checker._check_requirements_quality(test_requirements)
    assert "completeness" in result
    assert "clarity" in result
    assert "testability" in result
    assert "overall_score" in result
    assert "passed_threshold" in result

@pytest.mark.asyncio
async def test_check_consistency(quality_checker, llm_service):
    test_requirements = [{"id": "REQ-001", "description": "Test"}]
    test_analysis = {"analysis": "ok"}
    test_documents = {"doc": "content"}
    llm_service.get_completion.return_value = ('{"consistency_status": "consistent"}', None)

    result = await quality_checker._check_consistency(test_requirements, test_analysis, test_documents)
    assert "consistency_status" in result

@pytest.mark.asyncio
async def test_identify_issues(quality_checker, llm_service):
    test_requirements = [{"id": "REQ-001", "description": "Test"}]
    test_analysis = {"analysis": "ok"}
    test_documents = {"doc": "content"}
    llm_service.get_completion.return_value = ('{"identified_issues": ["Issue 1"]}', None)

    result = await quality_checker._identify_issues(test_requirements, test_analysis, test_documents)
    assert "identified_issues" in result
    assert "Issue 1" in result["identified_issues"]

@pytest.mark.asyncio
async def test_generate_improvements(quality_checker, llm_service):
    test_requirements = [{"id": "REQ-001", "description": "Test"}]
    test_analysis = {"analysis": "ok"}
    test_documents = {"doc": "content"}
    test_issues = [{"description": "Issue 1"}]
    llm_service.get_completion.return_value = ('{"improvement_suggestions": ["Suggestion 1"]}', None)

    result = await quality_checker._generate_improvements(test_requirements, test_analysis, test_documents, test_issues)
    assert "improvement_suggestions" in result
    assert "Suggestion 1" in result["improvement_suggestions"]

@pytest.mark.asyncio
async def test_quality_check_error_handling(quality_checker, llm_service):
    llm_service.get_completion.side_effect = Exception("LLM error")
    result = await quality_checker.process([], {}, {})
    assert result == {}
    assert quality_checker.get_state() == 'error' 