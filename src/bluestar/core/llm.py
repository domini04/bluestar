"""
BlueStar LLM Integration

LLM client factory for creating configured LangChain clients.
Integrates with BlueStar configuration and error handling.
"""

from typing import Optional, Dict, Any
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel

from ..config import config
from .exceptions import (
    LLMError, 
    ConfigurationError, 
    InvalidProviderError
)


logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client factory for creating configured LangChain clients."""
    
    def __init__(self):
        """Initialize the LLM client factory with configuration."""
        self.provider = config.llm_provider
        self.model = config.llm_model
        self.api_key = config.llm_api_key
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"LLM client factory initialized: {self.provider} -> {self.model}")
    
    def _validate_configuration(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ConfigurationError(
                f"API key not configured for provider: {self.provider}"
            )
        
        if self.provider not in config.get_available_providers():
            available = config.get_available_providers()
            raise InvalidProviderError(self.provider, available)
    
    def get_client(
        self, 
        temperature: float = 0.7, 
        max_tokens: int = 10000,
        timeout: int = 60,
        **kwargs
    ) -> BaseChatModel:
        """
        Create a configured LangChain client with custom parameters.
        
        Args:
            temperature: Model temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured LangChain client
            
        Raises:
            LLMError: On client creation failure
        """
        try:
            if self.provider == "openai":
                return ChatOpenAI(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    request_timeout=timeout,
                    **kwargs
                )
            
            elif self.provider == "claude":
                return ChatAnthropic(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    **kwargs
                )
            
            elif self.provider == "gemini":
                # Gemini uses different parameter names and may not support timeout
                gemini_params = {
                    "model": self.model,
                    "google_api_key": self.api_key,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                # Add timeout parameter for Gemini
                if timeout != 60:  # Only add if not default
                    gemini_params["timeout"] = timeout
                
                return ChatGoogleGenerativeAI(**gemini_params, **kwargs)
            
            else:
                available = config.get_available_providers()
                raise InvalidProviderError(self.provider, available)
                
        except Exception as e:
            if isinstance(e, (ConfigurationError, InvalidProviderError)):
                raise
            raise LLMError.from_langchain_error(e, "client creation")
    
    def get_default_client(self) -> BaseChatModel:
        """
        Create a LangChain client with default parameters.
        
        Returns:
            Configured LangChain client with default settings
        """
        return self.get_client()
    
    def get_conservative_client(self) -> BaseChatModel:
        """
        Create a client optimized for consistent, factual content.
        
        Returns:
            LangChain client with conservative settings
        """
        return self.get_client(temperature=0.2, max_tokens=3000)
    
    def get_creative_client(self) -> BaseChatModel:
        """
        Create a client optimized for creative content generation.
        
        Returns:
            LangChain client with creative settings
        """
        return self.get_client(temperature=0.9, max_tokens=4096)
    
    def test_connection(self) -> bool:
        """
        Test LLM connection with a simple query.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_client = self.get_client(max_tokens=20)
            response = test_client.invoke([
                HumanMessage(content="Say 'Hello from BlueStar' in exactly those words.")
            ])
            return "Hello from BlueStar" in response.content
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the current LLM client configuration."""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key_configured": bool(self.api_key),
            "available_providers": config.get_available_providers()
        }
    
    def __repr__(self) -> str:
        """String representation of LLM client factory."""
        return f"LLMClient(provider={self.provider}, model={self.model})"


# Global LLM client factory instance
llm_client = LLMClient() 