"""
Unit tests for BlueStar LLMClient class.

Tests LLM client factory functionality, provider management, and integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from src.bluestar.core.llm import LLMClient
from src.bluestar.core.exceptions import (
    ConfigurationError, 
    InvalidProviderError,
    LLMError
)


class TestLLMClientInitialization:
    """Test LLMClient initialization and configuration validation."""
    
    def test_valid_initialization_gemini(self, valid_gemini_env):
        """Test successful initialization with valid Gemini configuration."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_gemini_key_123"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client = LLMClient()
            
            assert client.provider == "gemini"
            assert client.model == "gemini-2.5-pro-preview-06-05"
            assert client.api_key == "test_gemini_key_123"
    
    def test_valid_initialization_openai(self, valid_openai_env):
        """Test successful initialization with valid OpenAI configuration."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "openai"
            mock_config.llm_model = "gpt-4.1-2025-04-14"
            mock_config.llm_api_key = "test_openai_key_456"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client = LLMClient()
            
            assert client.provider == "openai"
            assert client.model == "gpt-4.1-2025-04-14"
            assert client.api_key == "test_openai_key_456"
    
    def test_missing_api_key_error(self, missing_api_key_env):
        """Test that missing API key raises ConfigurationError."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_api_key = None
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            with pytest.raises(ConfigurationError) as exc_info:
                LLMClient()
            
            assert "API key not configured for provider: gemini" in str(exc_info.value)
    
    def test_invalid_provider_error(self, invalid_provider_env):
        """Test that invalid provider raises InvalidProviderError."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "invalid_provider"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
    
            with pytest.raises(InvalidProviderError) as exc_info:
                LLMClient()
    
            assert "Unsupported LLM provider: 'invalid_provider'" in str(exc_info.value)


class TestLLMClientFactory:
    """Test LLM client factory methods."""
    
    def test_get_default_client(self, valid_gemini_env, mock_all_langchain_clients):
        """Test get_default_client creates client with default parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_default_client()
            
            # Verify it returns a BaseChatModel (or Mock pretending to be one)
            assert client is not None
            # Verify the mock was called with correct parameters
            mock_all_langchain_clients['gemini'].assert_called_once_with(
                model="gemini-2.5-pro-preview-06-05",
                google_api_key="test_key",
                temperature=0.7,
                max_output_tokens=10000
            )
    
    def test_get_conservative_client(self, valid_gemini_env, mock_all_langchain_clients):
        """Test get_conservative_client creates client with conservative parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_conservative_client()
            
            mock_all_langchain_clients['gemini'].assert_called_once_with(
                model="gemini-2.5-pro-preview-06-05",
                google_api_key="test_key",
                temperature=0.2,  # Conservative temperature
                max_output_tokens=3000  # Conservative token limit
            )
    
    def test_get_creative_client(self, valid_gemini_env, mock_all_langchain_clients):
        """Test get_creative_client creates client with creative parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_creative_client()
            
            mock_all_langchain_clients['gemini'].assert_called_once_with(
                model="gemini-2.5-pro-preview-06-05",
                google_api_key="test_key",
                temperature=0.9,  # Creative temperature
                max_output_tokens=4096  # Higher token limit
            )
    
    def test_get_client_with_custom_parameters(self, valid_gemini_env, mock_all_langchain_clients):
        """Test get_client with custom parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_client(
                temperature=0.5,
                max_tokens=8000,
                timeout=30
            )
            
            mock_all_langchain_clients['gemini'].assert_called_once_with(
                model="gemini-2.5-pro-preview-06-05",
                google_api_key="test_key",
                temperature=0.5,
                max_output_tokens=8000,
                timeout=30
            )


class TestProviderSpecificClients:
    """Test provider-specific client creation."""
    
    @pytest.mark.parametrize("provider,expected_calls", [
        ("openai", {
            'class': 'openai',
            'params': {
                'model': "gpt-4.1-2025-04-14",
                'api_key': "test_key",
                'temperature': 0.7,
                'max_tokens': 10000,
                'request_timeout': 60
            }
        }),
        ("claude", {
            'class': 'claude',
            'params': {
                'model': "claude-opus-4-20250514",
                'api_key': "test_key",
                'temperature': 0.7,
                'max_tokens': 10000,
                'timeout': 60
            }
        }),
        ("gemini", {
            'class': 'gemini',
            'params': {
                'model': "gemini-2.5-pro-preview-06-05",
                'google_api_key': "test_key",
                'temperature': 0.7,
                'max_output_tokens': 10000
            }
        })
    ])
    def test_provider_specific_client_creation(self, provider, expected_calls, provider_test_data, mock_all_langchain_clients):
        """Test that each provider creates the correct client type with correct parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            provider_data = provider_test_data[provider]
            mock_config.llm_provider = provider
            mock_config.llm_model = provider_data["model"]
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_default_client()
            
            # Verify the correct provider's mock was called
            mock_class = mock_all_langchain_clients[expected_calls['class']]
            mock_class.assert_called_once_with(**expected_calls['params'])
    
    def test_openai_specific_parameters(self, mock_all_langchain_clients):
        """Test OpenAI-specific parameter handling."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "openai"
            mock_config.llm_model = "gpt-4.1-2025-04-14"
            mock_config.llm_api_key = "test_openai_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_client(temperature=0.8, max_tokens=5000, timeout=90)
            
            mock_all_langchain_clients['openai'].assert_called_once_with(
                model="gpt-4.1-2025-04-14",
                api_key="test_openai_key",
                temperature=0.8,
                max_tokens=5000,
                request_timeout=90
            )
    
    def test_gemini_uses_different_param_names(self, mock_all_langchain_clients):
        """Test that Gemini uses different parameter names (max_output_tokens vs max_tokens)."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_gemini_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            client = client_factory.get_client(max_tokens=6000)
            
            # Verify Gemini gets max_output_tokens instead of max_tokens
            mock_all_langchain_clients['gemini'].assert_called_once_with(
                model="gemini-2.5-pro-preview-06-05",
                google_api_key="test_gemini_key",
                temperature=0.7,
                max_output_tokens=6000  # Note: max_output_tokens, not max_tokens
            )


class TestErrorHandling:
    """Test error handling in LLM client creation."""
    
    def test_langchain_error_wrapped_in_llm_error(self, valid_gemini_env):
        """Test that LangChain exceptions are wrapped in LLMError."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            with patch('src.bluestar.core.llm.ChatGoogleGenerativeAI') as mock_gemini:
                # Make the mock raise an exception when called
                mock_gemini.side_effect = Exception("LangChain initialization error")
                
                client_factory = LLMClient()
                
                with pytest.raises(LLMError) as exc_info:
                    client_factory.get_default_client()
                
                assert "client creation" in str(exc_info.value)
                assert "LangChain initialization error" in str(exc_info.value)
    
    def test_configuration_error_not_wrapped(self, valid_gemini_env):
        """Test that ConfigurationError is not wrapped in LLMError."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"  
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            with patch('src.bluestar.core.llm.ChatGoogleGenerativeAI') as mock_gemini:
                mock_gemini.side_effect = ConfigurationError("Config error")
                
                client_factory = LLMClient()
                
                # Should raise ConfigurationError directly, not wrapped in LLMError
                with pytest.raises(ConfigurationError):
                    client_factory.get_default_client()
    
    def test_invalid_provider_in_get_client(self, valid_gemini_env):
        """Test invalid provider handling during initialization."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "invalid_provider"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            # Should fail during initialization, not during get_client()
            with pytest.raises(InvalidProviderError) as exc_info:
                LLMClient()
            
            assert "invalid_provider" in str(exc_info.value)


class TestUtilityMethods:
    """Test utility methods of LLMClient."""
    
    def test_get_client_info_structure(self, valid_gemini_env):
        """Test get_client_info returns correct structure."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            info = client_factory.get_client_info()
            
            assert isinstance(info, dict)
            assert "provider" in info
            assert "model" in info
            assert "api_key_configured" in info
            assert "available_providers" in info
            
            assert info["provider"] == "gemini"
            assert info["model"] == "gemini-2.5-pro-preview-06-05"
            assert info["api_key_configured"] is True
            assert info["available_providers"] == ["openai", "claude", "gemini"]
    
    def test_test_connection_success(self, valid_gemini_env, mock_gemini_client):
        """Test successful connection test."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            with patch('src.bluestar.core.llm.ChatGoogleGenerativeAI', return_value=mock_gemini_client):
                client_factory = LLMClient()
                result = client_factory.test_connection()
                
                assert result is True
                mock_gemini_client.invoke.assert_called_once()
    
    def test_test_connection_failure(self, valid_gemini_env):
        """Test connection test failure."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            with patch('src.bluestar.core.llm.ChatGoogleGenerativeAI') as mock_gemini:
                mock_gemini.side_effect = Exception("Connection failed")
                
                client_factory = LLMClient()
                result = client_factory.test_connection()
                
                assert result is False
    
    def test_repr_format(self, valid_gemini_env):
        """Test __repr__ method output format."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            repr_str = repr(client_factory)
            
            assert "LLMClient(" in repr_str
            assert "provider=gemini" in repr_str
            assert "model=gemini-2.5-pro-preview-06-05" in repr_str


class TestIntegration:
    """Integration tests for LLMClient with configuration."""
    
    def test_config_integration(self, valid_gemini_env, mock_all_langchain_clients):
        """Test integration between Config and LLMClient."""
        # This test uses the real config import to test integration
        from src.bluestar.core.llm import LLMClient
        
        with patch('src.bluestar.config.load_dotenv'):
            client_factory = LLMClient() 
            client = client_factory.get_default_client()
            
            # Verify that configuration flows through correctly
            assert client is not None
    
    def test_multiple_client_creation(self, valid_gemini_env, mock_all_langchain_clients):
        """Test creating multiple clients with different parameters."""
        with patch('src.bluestar.core.llm.config') as mock_config:
            mock_config.llm_provider = "gemini"
            mock_config.llm_model = "gemini-2.5-pro-preview-06-05"
            mock_config.llm_api_key = "test_key"
            mock_config.get_available_providers.return_value = ["openai", "claude", "gemini"]
            
            client_factory = LLMClient()
            
            # Create multiple clients
            client1 = client_factory.get_conservative_client()
            client2 = client_factory.get_creative_client()
            client3 = client_factory.get_client(temperature=0.5)
            
            # Verify all were created
            assert client1 is not None
            assert client2 is not None  
            assert client3 is not None
            
            # Verify the mock was called multiple times
            assert mock_all_langchain_clients['gemini'].call_count == 3 