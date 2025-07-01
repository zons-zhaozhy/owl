"""Tests for utility classes."""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from owl_requirements.utils.cache import CacheManager
from owl_requirements.utils.task_manager import TaskManager
from owl_requirements.utils.resource_monitor import ResourceMonitor

@pytest.fixture
def cache_dir():
    """Temporary cache directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def cache_manager(cache_dir):
    """Cache manager instance."""
    return CacheManager(
        cache_dir=cache_dir,
        max_size_mb=10,
        expiration_days=1,
        cleanup_interval=1
    )

@pytest.fixture
def task_manager():
    """Task manager instance."""
    return TaskManager(
        default_timeout=1.0,
        cleanup_interval=1.0,
        max_concurrent_tasks=10
    )

@pytest.fixture
def resource_monitor():
    """Resource monitor instance."""
    return ResourceMonitor(
        interval=0.1,
        history_size=10,
        cpu_threshold=90.0,
        memory_threshold=90.0,
        disk_threshold=90.0
    )

def test_cache_operations(cache_manager):
    """Test basic cache operations."""
    # Test set and get
    cache_manager.set("test_key", {"data": "test"})
    result = cache_manager.get("test_key")
    assert result == {"data": "test"}
    
    # Test delete
    cache_manager.delete("test_key")
    result = cache_manager.get("test_key")
    assert result is None
    
    # Test clear
    cache_manager.set("test_key", {"data": "test"})
    cache_manager.clear()
    result = cache_manager.get("test_key")
    assert result is None

@pytest.mark.asyncio
async def test_task_manager(task_manager):
    """Test task manager operations."""
    # Test task creation and execution
    async def test_task():
        await asyncio.sleep(0.1)
        return "success"
        
    task_id = await task_manager.create_task(test_task())
    
    # Wait for task completion
    while True:
        status = await task_manager.get_task_status(task_id)
        if status["status"] == "completed":
            break
        await asyncio.sleep(0.1)
        
    # Check result
    task = task_manager.tasks[task_id]
    assert task.result == "success"
    
    # Test task cancellation
    async def long_task():
        await asyncio.sleep(10)
        
    task_id = await task_manager.create_task(long_task())
    await task_manager.cancel_task(task_id)
    
    status = await task_manager.get_task_status(task_id)
    assert status["status"] == "cancelled"
    
    # Cleanup
    await task_manager.shutdown()

@pytest.mark.asyncio
async def test_resource_monitor(resource_monitor):
    """Test resource monitor operations."""
    # Start monitoring
    await resource_monitor.start()
    
    # Wait for some metrics to be collected
    await asyncio.sleep(0.5)
    
    # Check current metrics
    metrics = resource_monitor.get_current_metrics()
    assert metrics is not None
    assert metrics.cpu_percent >= 0
    assert metrics.memory_percent >= 0
    
    # Check metrics history
    history = resource_monitor.get_metrics_history()
    assert len(history) > 0
    
    # Check average metrics
    avg_metrics = resource_monitor.get_average_metrics(window=5)
    assert avg_metrics is not None
    
    # Stop monitoring
    await resource_monitor.stop()

def test_cache_size_limit(cache_manager):
    """Test cache size limit enforcement."""
    # Create data larger than cache limit
    large_data = "x" * (11 * 1024 * 1024)  # 11MB
    
    # This should raise an error as it exceeds the 10MB limit
    with pytest.raises(Exception):
        cache_manager.set("large_key", large_data)

@pytest.mark.asyncio
async def test_task_limit(task_manager):
    """Test task limit enforcement."""
    async def dummy_task():
        await asyncio.sleep(1)
        
    # Create maximum number of tasks
    for _ in range(10):
        await task_manager.create_task(dummy_task())
        
    # This should raise an error
    with pytest.raises(Exception):
        await task_manager.create_task(dummy_task())
        
    # Cleanup
    await task_manager.shutdown()

@pytest.mark.asyncio
async def test_resource_monitor_thresholds(resource_monitor):
    """Test resource monitor threshold warnings."""
    # Lower thresholds to ensure warnings
    resource_monitor.cpu_threshold = 0.1
    resource_monitor.memory_threshold = 0.1
    resource_monitor.disk_threshold = 0.1
    
    # Start monitoring
    await resource_monitor.start()
    
    # Wait for metrics collection
    await asyncio.sleep(0.5)
    
    # Stop monitoring
    await resource_monitor.stop()
    
    # Check that metrics were collected
    assert len(resource_monitor.metrics_history) > 0 