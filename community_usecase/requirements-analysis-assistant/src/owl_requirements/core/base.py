"""Base agent implementation for the OWL Requirements Analysis system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime

from .config import AgentConfig, AgentStatus, AgentRole

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the system.
    
    This class provides the core functionality that all agents share:
    - Configuration management
    - Status tracking
    - Basic communication
    - Error handling
    - Resource management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the base agent.
        
        Args:
            config: Configuration for this agent instance
        """
        self.config = config
        self.status = AgentStatus.IDLE
        self.last_error: Optional[Exception] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.logger = logging.getLogger(f"owl.agent.{config['name']}")
        
        # Initialize metrics
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "last_call_timestamp": None
        }
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results.
        
        This is the main entry point for agent-specific logic.
        Must be implemented by each agent subclass.
        
        Args:
            input_data: Data to be processed by this agent
            
        Returns:
            Processed results
        """
        raise NotImplementedError
        
    async def start(self) -> None:
        """Start the agent's processing loop."""
        self.status = AgentStatus.BUSY
        self.start_time = datetime.now()
        self.logger.info(f"Agent {self.config['name']} started")
        
    async def stop(self) -> None:
        """Stop the agent's processing loop."""
        self.status = AgentStatus.TERMINATED
        self.end_time = datetime.now()
        self.logger.info(f"Agent {self.config['name']} stopped")
        
    def get_status(self) -> Dict[str, Any]:
        """Get the current status and metrics of this agent.
        
        Returns:
            Dict containing status information and metrics
        """
        return {
            "name": self.config['name'],
            "role": self.config['role'].value,
            "status": self.status.value,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "metrics": self.metrics,
            "last_error": str(self.last_error) if self.last_error else None,
            "config": self.config
        }
        
    async def handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during processing.
        
        Args:
            error: The exception that was raised
        """
        self.last_error = error
        self.metrics["failed_calls"] += 1
        self.status = AgentStatus.ERROR
        self.logger.error(f"Error in agent {self.config['name']}: {error}", exc_info=True)
        
    def _update_metrics(self, success: bool, processing_time: float):
        """Update agent metrics.
        
        Args:
            success: Whether the call was successful
            processing_time: Processing time in seconds
        """
        self.metrics["total_calls"] += 1
        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1
            
        self.metrics["total_processing_time"] += processing_time
        self.metrics["average_processing_time"] = (
            self.metrics["total_processing_time"] /
            self.metrics["total_calls"]
        )
        self.metrics["last_call_timestamp"] = datetime.now().isoformat()