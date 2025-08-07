"""
BlueStar Configuration Management

Handles application configuration, environment variables, and settings.
"""

import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)  # Automatically loads .env file if it exists, overriding existing values


class Config:
    """Configuration class for BlueStar application."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        # Project root directory
        self.project_root = Path(__file__).parent.parent.parent
        7963
        # LLM Provider-Model Mapping
        # User chooses provider: 'openai', 'claude', or 'gemini'
        # Model is automatically selected based on provider
        # 여기 있는 모델명을 필요에 따라 변경
        self.llm_models = {
            "openai": "gpt-4.1-2025-04-14",
            "claude": "claude-opus-4-20250514", 
            "gemini": "gemini-2.5-pro-preview-06-05"
        }
        
        # LLM Configuration
        self.llm_provider = os.getenv("BLUESTAR_LLM_PROVIDER", "gemini").lower()
        
        # Validate provider and get corresponding model
        if self.llm_provider not in self.llm_models:
            available_providers = list(self.llm_models.keys())
            raise ValueError(
                f"Unsupported LLM provider: '{self.llm_provider}'. "
                f"Supported providers: {available_providers}. "
                f"Set BLUESTAR_LLM_PROVIDER in your .env file."
            )
        
        # Auto-select model based on provider
        self.llm_model = self.llm_models[self.llm_provider]
        
        # Get API key based on provider
        self.llm_api_key = self._get_provider_api_key()
        
        # Ghost CMS Configuration (loaded if platform is 'ghost')
        self.ghost_api_url: Optional[str] = None
        self.ghost_admin_api_key: Optional[str] = None
        
        # Check for blog platform and load specific configs
        blog_platform = os.getenv("BLUESTAR_BLOG_PLATFORM", "ghost").lower()
        if blog_platform == "ghost":
            self.ghost_api_url = os.getenv("GHOST_API_URL")
            self.ghost_admin_api_key = os.getenv("GHOST_ADMIN_API_KEY")
        
        # Repository Configuration
        self.default_repo_path = os.getenv("BLUESTAR_DEFAULT_REPO", str(self.project_root))
        
        # Output Configuration
        self.output_format = os.getenv("BLUESTAR_OUTPUT_FORMAT", "markdown")
        self.console_output = os.getenv("BLUESTAR_CONSOLE_OUTPUT", "true").lower() == "true"
        
        # Logging Configuration
        self.log_level = os.getenv("BLUESTAR_LOG_LEVEL", "INFO")
    
    def _get_provider_api_key(self) -> Optional[str]:
        """Get API key based on selected provider."""
        api_key_mapping = {
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY"
        }
        
        env_var = api_key_mapping[self.llm_provider]
        api_key = os.getenv(env_var)
        
        if not api_key:
            print(f"Warning: {env_var} not configured for {self.llm_provider} provider")
        
        return api_key
    
    def get_available_providers(self) -> list[str]:
        """Get list of supported LLM providers."""
        return list(self.llm_models.keys())
    
    def get_provider_info(self) -> dict:
        """Get current provider configuration info."""
        return {
            "provider": self.llm_provider,
            "model": self.llm_model,
            "api_key_configured": bool(self.llm_api_key)
        }
    
    def display_provider_options(self) -> None:
        """Display available provider options for user reference."""
        print("Available LLM Providers:")
        for provider, model in self.llm_models.items():
            print(f"  • {provider}: {model}")
        print(f"\nCurrent selection: {self.llm_provider} → {self.llm_model}")
        print(f"API key configured: {'✓' if self.llm_api_key else '✗'}")
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        is_valid = True
        
        # Validate LLM configuration
        if not self.llm_api_key:
            print(f"Error: API key for {self.llm_provider} is required")
            is_valid = False
        
        # Validate provider
        if self.llm_provider not in self.llm_models:
            print(f"Error: Invalid LLM provider '{self.llm_provider}'")
            is_valid = False
            
        return is_valid
    
    def __repr__(self) -> str:
        """String representation of config (hiding sensitive data)."""
        return (f"Config(provider={self.llm_provider}, "
                f"model={self.llm_model}, "
                f"ghost_api_configured={bool(self.ghost_admin_api_key)})")


# Global config instance
config = Config() 