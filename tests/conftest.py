"""
Shared pytest fixtures for BlueStar testing.

Provides common test setup, mocked dependencies, and test data.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path


# Environment Variable Fixtures
@pytest.fixture
def valid_gemini_env(monkeypatch):
    """Mock environment variables for valid Gemini configuration."""
    monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "test_gemini_key_123")
    monkeypatch.setenv("BLUESTAR_LOG_LEVEL", "INFO")
    monkeypatch.setenv("BLUESTAR_CONSOLE_OUTPUT", "true")
    monkeypatch.setenv("BLUESTAR_OUTPUT_FORMAT", "markdown")
    


@pytest.fixture
def valid_openai_env(monkeypatch):
    """Mock environment variables for valid OpenAI configuration."""
    monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_456")
    monkeypatch.setenv("BLUESTAR_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("BLUESTAR_CONSOLE_OUTPUT", "false")


@pytest.fixture
def valid_claude_env(monkeypatch):
    """Mock environment variables for valid Claude configuration."""
    monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_claude_key_789")
    monkeypatch.setenv("BLUESTAR_LOG_LEVEL", "WARNING")


@pytest.fixture
def missing_api_key_env(monkeypatch):
    """Mock environment variables with missing API key."""
    monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "gemini")
    # Explicitly remove any existing API key
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("BLUESTAR_LOG_LEVEL", "INFO")


@pytest.fixture
def invalid_provider_env(monkeypatch):
    """Mock environment variables with invalid provider."""
    monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "invalid_provider")
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")


@pytest.fixture
def minimal_env(monkeypatch):
    """Mock minimal environment variables (defaults only)."""
    # Clear all BlueStar environment variables
    env_vars = [
        "BLUESTAR_LLM_PROVIDER", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
        "BLUESTAR_LOG_LEVEL", "BLUESTAR_CONSOLE_OUTPUT", "BLUESTAR_OUTPUT_FORMAT"
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


# LangChain Client Mocks
@pytest.fixture
def mock_openai_client():
    """Mock ChatOpenAI client."""
    mock = Mock()
    mock.invoke.return_value.content = "Hello from BlueStar"
    return mock


@pytest.fixture
def mock_claude_client():
    """Mock ChatAnthropic client."""
    mock = Mock()
    mock.invoke.return_value.content = "Hello from BlueStar"
    return mock


@pytest.fixture
def mock_gemini_client():
    """Mock ChatGoogleGenerativeAI client."""
    mock = Mock()
    mock.invoke.return_value.content = "Hello from BlueStar"
    return mock


@pytest.fixture
def mock_all_langchain_clients(mock_openai_client, mock_claude_client, mock_gemini_client):
    """Mock all LangChain client classes."""
    with patch('src.bluestar.core.llm.ChatOpenAI', return_value=mock_openai_client) as mock_openai, \
         patch('src.bluestar.core.llm.ChatAnthropic', return_value=mock_claude_client) as mock_claude, \
         patch('src.bluestar.core.llm.ChatGoogleGenerativeAI', return_value=mock_gemini_client) as mock_gemini:
        
        yield {
            'openai': mock_openai,
            'claude': mock_claude, 
            'gemini': mock_gemini,
            'clients': {
                'openai': mock_openai_client,
                'claude': mock_claude_client,
                'gemini': mock_gemini_client
            }
        }


# Test Data Fixtures
@pytest.fixture
def provider_test_data():
    """Test data for different providers."""
    return {
        "openai": {
            "provider": "openai",
            "model": "gpt-4.1-2025-04-14",
            "api_key_env": "OPENAI_API_KEY",
            "client_class": "ChatOpenAI"
        },
        "claude": {
            "provider": "claude", 
            "model": "claude-opus-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
            "client_class": "ChatAnthropic"
        },
        "gemini": {
            "provider": "gemini",
            "model": "gemini-2.5-pro-preview-06-05", 
            "api_key_env": "GOOGLE_API_KEY",
            "client_class": "ChatGoogleGenerativeAI"
        }
    }


@pytest.fixture
def sample_client_parameters():
    """Sample parameters for client creation testing."""
    return {
        "default": {"temperature": 0.7, "max_tokens": 10000, "timeout": 60},
        "conservative": {"temperature": 0.2, "max_tokens": 3000, "timeout": 60},
        "creative": {"temperature": 0.9, "max_tokens": 4096, "timeout": 60},
        "custom": {"temperature": 0.5, "max_tokens": 8000, "timeout": 30}
    }


# Error Response Fixtures
@pytest.fixture
def mock_api_error():
    """Mock API error response."""
    error = Exception("API Error: Rate limit exceeded")
    return error


@pytest.fixture
def mock_connection_failure():
    """Mock connection failure."""
    error = Exception("Connection timeout")
    return error


# Configuration Reset Fixture
@pytest.fixture
def clean_config():
    """Ensure clean configuration state for each test."""
    # This will be used to reset any global config state
    yield
    # Cleanup after test if needed 