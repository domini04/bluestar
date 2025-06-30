"""
Unit tests for BlueStar Config class.

Tests configuration loading, validation, provider management, and settings.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from src.bluestar.config import Config
from src.bluestar.core.exceptions import ConfigurationError, InvalidProviderError


class TestConfigInitialization:
    """Test Config class initialization and environment loading."""
    
    def test_valid_gemini_initialization(self, valid_gemini_env):
        """Test successful initialization with valid Gemini configuration."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.llm_provider == "gemini"
            assert config.llm_model == "gemini-2.5-pro-preview-06-05"
            assert config.llm_api_key == "test_gemini_key_123"
            assert config.log_level == "INFO"
            assert config.console_output is True
            assert config.output_format == "markdown"
    
    def test_valid_openai_initialization(self, valid_openai_env):
        """Test successful initialization with valid OpenAI configuration."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.llm_provider == "openai"
            assert config.llm_model == "gpt-4.1-2025-04-14"
            assert config.llm_api_key == "test_openai_key_456"
            assert config.log_level == "DEBUG"
            assert config.console_output is False
    
    def test_valid_claude_initialization(self, valid_claude_env):
        """Test successful initialization with valid Claude configuration."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.llm_provider == "claude"
            assert config.llm_model == "claude-opus-4-20250514"
            assert config.llm_api_key == "test_claude_key_789"
            assert config.log_level == "WARNING"
    
    def test_minimal_env_defaults(self, minimal_env):
        """Test initialization with minimal environment (using defaults)."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.llm_provider == "gemini"  # Default provider
            assert config.llm_model == "gemini-2.5-pro-preview-06-05"
            assert config.log_level == "INFO"
            assert config.console_output is True
            assert config.output_format == "markdown"
    
    def test_invalid_provider_error(self, invalid_provider_env):
        """Test that invalid provider raises ValueError."""
        with patch('src.bluestar.config.load_dotenv'):
            with pytest.raises(ValueError) as exc_info:
                Config()
            
            assert "Unsupported LLM provider: 'invalid_provider'" in str(exc_info.value)
            assert "Supported providers: ['openai', 'claude', 'gemini']" in str(exc_info.value)


class TestConfigProviderManagement:
    """Test provider-related functionality."""
    
    def test_get_available_providers(self, valid_gemini_env):
        """Test get_available_providers returns correct list."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            providers = config.get_available_providers()
            
            assert isinstance(providers, list)
            assert set(providers) == {"openai", "claude", "gemini"}
            assert len(providers) == 3
    
    def test_get_provider_info_structure(self, valid_gemini_env):
        """Test get_provider_info returns correct structure."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            info = config.get_provider_info()
            
            assert isinstance(info, dict)
            assert "provider" in info
            assert "model" in info
            assert "api_key_configured" in info
            
            assert info["provider"] == "gemini"
            assert info["model"] == "gemini-2.5-pro-preview-06-05"
            assert info["api_key_configured"] is True
    
    def test_get_provider_info_no_api_key(self, missing_api_key_env):
        """Test get_provider_info with missing API key."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            info = config.get_provider_info()
            
            assert info["api_key_configured"] is False
    
    @pytest.mark.parametrize("provider,expected_model", [
        ("openai", "gpt-4.1-2025-04-14"),
        ("claude", "claude-opus-4-20250514"),
        ("gemini", "gemini-2.5-pro-preview-06-05")
    ])
    def test_provider_model_mapping(self, provider, expected_model, monkeypatch):
        """Test that each provider maps to correct model."""
        monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", provider)
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")  # Provide any API key
        
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            assert config.llm_model == expected_model
    
    def test_display_provider_options(self, valid_gemini_env, capsys):
        """Test display_provider_options output format."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            config.display_provider_options()
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Check that all providers are displayed
            assert "openai: gpt-4.1-2025-04-14" in output
            assert "claude: claude-opus-4-20250514" in output
            assert "gemini: gemini-2.5-pro-preview-06-05" in output
            
            # Check current selection is shown
            assert "Current selection: gemini" in output
            assert "API key configured: ✓" in output


class TestConfigValidation:
    """Test config validation functionality."""
    
    def test_validate_success(self, valid_gemini_env):
        """Test successful validation with valid configuration."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            result = config.validate()
            
            assert result is True
    
    def test_validate_missing_api_key(self, missing_api_key_env, capsys):
        """Test validation failure with missing API key."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            result = config.validate()
            
            assert result is False
            
            # Check error message was printed
            captured = capsys.readouterr()
            assert "Error: API key for gemini is required" in captured.out
    
    def test_validate_invalid_provider(self, monkeypatch, capsys):
        """Test validation failure with invalid provider."""
        monkeypatch.setenv("BLUESTAR_LLM_PROVIDER", "invalid")
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
        
        with patch('src.bluestar.config.load_dotenv'):
            # This should fail during initialization
            with pytest.raises(ValueError):
                Config()


class TestConfigurationValues:
    """Test various configuration values and settings."""
    
    def test_blog_platform_settings(self, valid_gemini_env, monkeypatch):
        """Test blog platform configuration settings."""
        monkeypatch.setenv("BLUESTAR_BLOG_PLATFORM", "wordpress")
        monkeypatch.setenv("BLUESTAR_BLOG_API_URL", "https://myblog.com/api")
        monkeypatch.setenv("BLUESTAR_BLOG_API_KEY", "blog_key_123")
        
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.blog_platform == "wordpress"
            assert config.blog_api_url == "https://myblog.com/api"
            assert config.blog_api_key == "blog_key_123"
    
    def test_repository_settings(self, valid_gemini_env, monkeypatch):
        """Test repository configuration settings."""
        test_repo_path = "/custom/repo/path"
        monkeypatch.setenv("BLUESTAR_DEFAULT_REPO", test_repo_path)
        
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.default_repo_path == test_repo_path
    
    def test_output_format_settings(self, valid_gemini_env, monkeypatch):
        """Test output format configuration settings."""
        monkeypatch.setenv("BLUESTAR_OUTPUT_FORMAT", "html")
        monkeypatch.setenv("BLUESTAR_CONSOLE_OUTPUT", "false")
        
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert config.output_format == "html"
            assert config.console_output is False
    
    def test_project_root_path(self, valid_gemini_env):
        """Test project root path is correctly set."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            
            assert isinstance(config.project_root, Path)
            # Should point to project root (3 levels up from config.py)
            assert config.project_root.name == "bluestar"
    
    def test_console_output_boolean_conversion(self, valid_gemini_env, monkeypatch):
        """Test console_output boolean conversion from string."""
        test_cases = [
            ("true", True),
            ("True", True), 
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("invalid", False)  # Default to False for invalid values
        ]
        
        for env_value, expected in test_cases:
            monkeypatch.setenv("BLUESTAR_CONSOLE_OUTPUT", env_value)
            
            with patch('src.bluestar.config.load_dotenv'):
                config = Config()
                assert config.console_output is expected


class TestConfigRepresentation:
    """Test config string representation."""
    
    def test_repr_format(self, valid_gemini_env):
        """Test __repr__ method output format."""
        with patch('src.bluestar.config.load_dotenv'):
            config = Config()
            repr_str = repr(config)
            
            assert "Config(" in repr_str
            assert "provider=gemini" in repr_str
            assert "model=gemini-2.5-pro-preview-06-05" in repr_str
            assert "platform=ghost" in repr_str  # Default platform
            assert "api_key_configured=True" in repr_str 