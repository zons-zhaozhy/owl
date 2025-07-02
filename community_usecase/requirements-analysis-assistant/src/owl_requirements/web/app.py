"""Web application for the requirements analysis assistant."""

import typer
import json
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
import logging
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.coordinator import AgentCoordinator
from ..core.config import SystemConfig
from ..services.llm.factory import create_llm_service
from ..services.llm import LLMConfig, LLMProvider
from ..utils.enums import AgentRole
from ..agents.requirements_extractor import RequirementsExtractor
from ..agents.requirements_analyzer import RequirementsAnalyzer
from ..agents.documentation_generator import DocumentationGenerator
from ..agents.quality_checker import QualityChecker
from ..utils.exceptions import (
    RequirementsError,
    AnalysisError,
    QualityCheckError,
    DocumentationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("owl.web")

class RequirementsRequest(BaseModel):
    """Requirements analysis request."""
    text: str
    config: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    """Response model for requirements analysis."""
    requirements: Dict[str, Any]
    analysis: Dict[str, Any]
    quality_check: Dict[str, Any]
    documentation: Dict[str, Any]
    metrics: Dict[str, Any]

def create_web_app(coordinator: AgentCoordinator, system_config: SystemConfig) -> FastAPI:
    """Create FastAPI application.
    
    Args:
        coordinator: Agent coordinator instance
        system_config: System configuration
        
    Returns:
        FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="需求分析助手",
        description="基于OWL框架的需求分析系统",
        version="0.1.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    try:
        # Create LLM service
        llm_config = LLMConfig(
            provider=LLMProvider(system_config.llm_provider),
            model=system_config.llm_model,
            api_key=system_config.llm_api_key,
            temperature=system_config.llm_temperature,
            max_tokens=system_config.llm_max_tokens
        )
        llm_service = create_llm_service(llm_config)
        
        @app.post("/analyze")
        async def analyze_requirements(request: RequirementsRequest) -> Dict[str, Any]:
            """Analyze requirements.
            
            Args:
                request: Requirements analysis request
                
            Returns:
                Analysis results
            """
            try:
                # Process requirements
                result = await coordinator.analyze(request.text)
                return result
                
            except Exception as e:
                logger.error(f"需求分析失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
                
        @app.get("/health")
        async def health_check() -> Dict[str, str]:
            """Health check endpoint.
            
            Returns:
                Health status
            """
            return {"status": "healthy"}
            
        return app
        
    except Exception as e:
        logger.error(f"应用创建失败: {e}", exc_info=True)
        raise 