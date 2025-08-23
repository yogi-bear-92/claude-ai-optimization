"""
Test configuration and fixtures for Azure Issue Automation
"""
import asyncio
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Generator
import tempfile
import json
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    "github": {
        "token": "test_token_12345",
        "webhook_secret": "test_webhook_secret",
        "api_base_url": "https://api.github.com"
    },
    "azure": {
        "resource_group": "test-rg",
        "subscription_id": "test-subscription",
        "location": "eastus"
    },
    "intelligence": {
        "model_path": "tests/fixtures/test_model.pkl",
        "confidence_threshold": 0.8,
        "learning_enabled": True
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG.copy()

@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": TEST_CONFIG["github"]["token"]}):
        yield TEST_CONFIG["github"]["token"]

@pytest.fixture
def mock_webhook_secret():
    """Mock webhook secret for testing."""
    with patch.dict(os.environ, {"WEBHOOK_SECRET": TEST_CONFIG["github"]["webhook_secret"]}):
        yield TEST_CONFIG["github"]["webhook_secret"]

@pytest.fixture
def sample_github_issue():
    """Sample GitHub issue for testing."""
    return {
        "number": 123,
        "title": "Bug: Application crashes on startup",
        "body": "The application fails to start and shows error message 'Module not found'",
        "labels": [{"name": "bug"}, {"name": "high-priority"}],
        "user": {"login": "testuser"},
        "html_url": "https://github.com/test/repo/issues/123",
        "state": "open",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_github_webhook_payload():
    """Sample GitHub webhook payload for testing."""
    return {
        "action": "opened",
        "number": 123,
        "issue": {
            "number": 123,
            "title": "Bug: Application crashes on startup",
            "body": "The application fails to start and shows error message 'Module not found'",
            "labels": [{"name": "bug"}, {"name": "high-priority"}],
            "user": {"login": "testuser"},
            "html_url": "https://github.com/test/repo/issues/123",
            "state": "open"
        },
        "repository": {
            "name": "test-repo",
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo"
        },
        "sender": {
            "login": "testuser"
        }
    }

@pytest.fixture
def mock_intelligence_engine():
    """Mock intelligence engine for testing."""
    engine = Mock()
    engine.analyze_issue_pattern.return_value = {
        "issue_type": "bug",
        "priority": "high",
        "complexity_score": 0.7,
        "confidence_score": 0.85
    }
    engine.get_agent_recommendations.return_value = [
        {
            "agent_name": "debugger",
            "recommended_model": "sonnet",
            "confidence": 0.85
        }
    ]
    engine.record_execution_outcome = Mock()
    return engine

@pytest.fixture
def mock_self_improving_automation():
    """Mock self-improving automation for testing."""
    automation = Mock()
    automation.submit_feedback = AsyncMock()
    automation.get_adaptive_threshold.return_value = 0.75
    automation.get_agent_performance.return_value = {
        "debugger": {"success_rate": 0.85, "avg_time": 120}
    }
    automation.should_escalate.return_value = False
    return automation

@pytest.fixture
def mock_cross_repo_intelligence():
    """Mock cross-repository intelligence for testing."""
    cross_repo = Mock()
    cross_repo.find_similar_issues.return_value = [
        {
            "repository": "other/repo",
            "issue_number": 456,
            "similarity_score": 0.92,
            "resolution_summary": "Fixed by updating dependencies"
        }
    ]
    cross_repo.get_repository_health.return_value = {
        "health_score": 8.5,
        "technical_debt_score": 3.2,
        "issue_resolution_rate": 0.87
    }
    return cross_repo

@pytest.fixture
def temp_model_file():
    """Create a temporary model file for testing."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False) as f:
        # Create a minimal mock model file
        import pickle
        mock_model = {"type": "test_model", "version": "1.0"}
        pickle.dump(mock_model, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def mock_database():
    """Mock database for testing."""
    db = {}
    
    def get_item(key):
        return db.get(key)
    
    def set_item(key, value):
        db[key] = value
    
    def delete_item(key):
        db.pop(key, None)
    
    def list_items():
        return list(db.items())
    
    mock_db = Mock()
    mock_db.get = Mock(side_effect=get_item)
    mock_db.set = Mock(side_effect=set_item) 
    mock_db.delete = Mock(side_effect=delete_item)
    mock_db.list = Mock(side_effect=list_items)
    
    return mock_db

@pytest.fixture
async def mock_http_client():
    """Mock HTTP client for testing."""
    import httpx
    
    with patch('httpx.AsyncClient') as mock_client:
        client_instance = Mock()
        
        # Default successful responses
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"status": "success"}
        success_response.text = '{"status": "success"}'
        
        client_instance.get = AsyncMock(return_value=success_response)
        client_instance.post = AsyncMock(return_value=success_response)
        client_instance.patch = AsyncMock(return_value=success_response)
        client_instance.put = AsyncMock(return_value=success_response)
        client_instance.delete = AsyncMock(return_value=success_response)
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=None)
        
        mock_client.return_value = client_instance
        yield client_instance

@pytest.fixture
def mock_azure_client():
    """Mock Azure client for testing."""
    client = Mock()
    
    # Container instance operations
    client.container_instances.create = AsyncMock()
    client.container_instances.get = AsyncMock(return_value={
        "properties": {
            "provisioningState": "Succeeded",
            "instanceView": {
                "state": "Running"
            }
        }
    })
    client.container_instances.delete = AsyncMock()
    
    # Resource group operations
    client.resource_groups.check_existence = AsyncMock(return_value=True)
    
    return client

@pytest.fixture
def performance_test_data():
    """Generate performance test data."""
    return {
        "issues": [
            {
                "number": i,
                "title": f"Test issue {i}",
                "body": f"This is test issue {i} for performance testing",
                "labels": [{"name": "test"}]
            }
            for i in range(1, 101)  # 100 test issues
        ],
        "expected_processing_time": 5.0,  # seconds
        "max_memory_usage": 512,  # MB
        "concurrent_requests": 10
    }

@pytest.fixture
def integration_test_repository():
    """Test repository configuration for integration tests."""
    return {
        "owner": "test-owner",
        "repo": "test-repo", 
        "full_name": "test-owner/test-repo",
        "webhook_url": "https://api.github.com/repos/test-owner/test-repo/hooks"
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15"  # Use test database
    }
    
    with patch.dict(os.environ, test_env):
        yield

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.critical = Mock()
    return logger

@pytest.fixture
def sample_execution_outcome():
    """Sample execution outcome for testing."""
    return {
        "issue_id": "123",
        "repository": "test/repo",
        "issue_type": "bug",
        "predicted_confidence": 0.85,
        "agent_used": "debugger",
        "model_used": "sonnet",
        "complexity_score": 0.7,
        "actual_success": True,
        "execution_time": 125.5,
        "error_message": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:05:00Z"
    }

@pytest.fixture
def sample_analytics_data():
    """Sample analytics data for testing."""
    return {
        "resolution_metrics": {
            "total_issues": 150,
            "resolved_issues": 128,
            "success_rate": 0.853,
            "avg_resolution_time": 4.2
        },
        "agent_performance": {
            "debugger": {"success_rate": 0.87, "avg_time": 3.8},
            "security-auditor": {"success_rate": 0.92, "avg_time": 5.1},
            "backend-architect": {"success_rate": 0.78, "avg_time": 6.3}
        },
        "model_effectiveness": {
            "sonnet": {"cost_per_request": 0.0045, "success_rate": 0.84},
            "opus": {"cost_per_request": 0.0180, "success_rate": 0.91},
            "haiku": {"cost_per_request": 0.0015, "success_rate": 0.76}
        }
    }

# Test utilities
class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def generate_issues(count: int, issue_type: str = "bug") -> list:
        """Generate multiple test issues."""
        return [
            {
                "number": i,
                "title": f"Test {issue_type} #{i}",
                "body": f"This is a test {issue_type} issue for automated testing",
                "labels": [{"name": issue_type}, {"name": "automated-test"}]
            }
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def generate_webhook_payloads(issues: list) -> list:
        """Generate webhook payloads for issues."""
        return [
            {
                "action": "opened",
                "issue": issue,
                "repository": {
                    "name": "test-repo",
                    "full_name": "test/repo"
                }
            }
            for issue in issues
        ]

# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

# Async test utilities
class AsyncTestCase:
    """Base class for async test utilities."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true."""
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if condition_func():
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            await asyncio.sleep(interval)
    
    @staticmethod
    async def simulate_delay(min_delay=0.1, max_delay=0.3):
        """Simulate realistic processing delay."""
        import asyncio
        import random
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)