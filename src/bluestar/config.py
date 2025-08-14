"""
BlueStar Configuration Management

Handles application configuration, environment variables, and settings.
"""

import os
import re
from urllib.parse import urlsplit
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
        # Allowed LLM providers and default models
        # Users may select any model string for a given provider; we keep defaults as fallback
        self.allowed_llm_providers = {"openai", "claude", "gemini", "grok"}
        self.default_llm_models = {
            "openai": "gpt-5",
            "claude": "claude-opus-4-20250514",
            "gemini": "gemini-2.5-pro",
            "grok": "grok-4-0709",
        }

        # LLM Configuration (provider + optional model override)
        self.llm_provider = os.getenv("BLUESTAR_LLM_PROVIDER", "gemini").lower()

        # Validate provider against allowlist
        if self.llm_provider not in self.allowed_llm_providers:
            available_providers = sorted(list(self.allowed_llm_providers))
            raise ValueError(
                f"Unsupported LLM provider: '{self.llm_provider}'. "
                f"Supported providers: {available_providers}. "
                f"Set BLUESTAR_LLM_PROVIDER in your .env file."
            )

        # Resolve model: CLI/env override via BLUESTAR_LLM_MODEL, else default per provider
        env_model = os.getenv("BLUESTAR_LLM_MODEL", "").strip()
        self.llm_model = env_model if env_model else self.default_llm_models[self.llm_provider]
        
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
        
        # Notion Configuration (loaded opportunistically; validated when used)
        self.notion_api_key: Optional[str] = os.getenv("NOTION_API_KEY")
        self.notion_url: Optional[str] = os.getenv("NOTION_URL")
        self.notion_database_id: Optional[str] = None
        if self.notion_url:
            self.notion_database_id = self._extract_notion_id_from_url(self.notion_url)
        
        # Repository Configuration
        self.default_repo_path = os.getenv("BLUESTAR_DEFAULT_REPO", str(self.project_root))
        
        # Output Configuration
        self.output_format = os.getenv("BLUESTAR_OUTPUT_FORMAT", "markdown")
        self.console_output = os.getenv("BLUESTAR_CONSOLE_OUTPUT", "true").lower() == "true"
        
        # Logging Configuration
        self.log_level = os.getenv("BLUESTAR_LOG_LEVEL", "INFO")

        # Optional preselected publishing target (ghost|notion|local|discard)
        preselect = os.getenv("BLUESTAR_PUBLISH", "").strip().lower()
        self.preselect_publish: Optional[str] = preselect if preselect in {"ghost", "notion", "local", "discard"} else None
    
    def _get_provider_api_key(self) -> Optional[str]:
        """Get API key based on selected provider."""
        api_key_mapping = {
            "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "grok": "GROK_API_KEY",
        }
        
        env_var = api_key_mapping.get(self.llm_provider)
        api_key = os.getenv(env_var)
        
        if not api_key:
            print(f"Warning: {env_var} not configured for {self.llm_provider} provider")
        
        return api_key
    
    def get_available_providers(self) -> list[str]:
        """Get list of supported LLM providers."""
        return sorted(list(self.allowed_llm_providers))
    
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
        for provider in self.get_available_providers():
            default_model = self.default_llm_models.get(provider, "<none>")
            print(f"  • {provider}: (default) {default_model}")
        print(f"\nCurrent selection: {self.llm_provider} → {self.llm_model}")
        print(f"API key configured: {'✓' if self.llm_api_key else '✗'}")

    def apply_overrides(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_api_key: Optional[str] = None,
    ) -> None:
        """Apply runtime overrides for provider/model/api key (e.g., from CLI).

        Provider is validated against the allowlist. Model is free-form; when not
        provided, we fall back to the provider's default model.
        """
        # Provider override
        if llm_provider:
            provider = llm_provider.lower().strip()
            if provider not in self.allowed_llm_providers:
                available_providers = sorted(list(self.allowed_llm_providers))
                raise ValueError(
                    f"Unsupported LLM provider: '{provider}'. "
                    f"Supported providers: {available_providers}."
                )
            self.llm_provider = provider
            # If model not explicitly overridden, reset to provider default
            if not llm_model:
                self.llm_model = self.default_llm_models[self.llm_provider]

        # Model override (free-form)
        if llm_model:
            model = llm_model.strip()
            if not model:
                raise ValueError("BLUESTAR_LLM_MODEL cannot be empty when provided.")
            self.llm_model = model

        # API key override (optional)
        if llm_api_key is not None:
            self.llm_api_key = llm_api_key.strip()
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        is_valid = True
        
        # Validate LLM configuration
        if not self.llm_api_key:
            print(f"Error: API key for {self.llm_provider} is required")
            is_valid = False
        
        # Validate provider
        if self.llm_provider not in self.allowed_llm_providers:
            print(
                f"Error: Invalid LLM provider '{self.llm_provider}'. "
                f"Allowed: {sorted(list(self.allowed_llm_providers))}"
            )
            is_valid = False

        # Validate model (non-empty); actual validity checked at client creation
        if not self.llm_model or not str(self.llm_model).strip():
            print("Error: LLM model must be a non-empty string")
            is_valid = False
            
        return is_valid
    
    def __repr__(self) -> str:
        """String representation of config (hiding sensitive data)."""
        return (f"Config(provider={self.llm_provider}, "
                f"model={self.llm_model}, "
                f"ghost_api_configured={bool(self.ghost_admin_api_key)})")

    @staticmethod
    def _extract_notion_id_from_url(url: str) -> Optional[str]:
        """Extract and normalize a Notion database/page ID from a shared URL.

        Supports URLs like:
          - https://www.notion.so/Workspace/Name-20ee4da2d57c804ca53fd8964074d448
          - https://www.notion.so/20ee4da2d57c804ca53fd8964074d448
          - https://www.notion.so/Workspace/20ee4da2d57c804ca53fd8964074d448?v=<view>

        Returns a hyphenated UUID string (8-4-4-4-12) if found, else None.
        """
        if not url or not isinstance(url, str):
            return None

        # Prefer IDs that appear in the PATH and are preceded by a hyphen (slug-id form)
        parsed = urlsplit(url)
        path = parsed.path or ""

        hyphen_suffixed_ids = re.findall(r"-([0-9a-fA-F]{32})", path)
        if hyphen_suffixed_ids:
            return Config._hyphenate_uuid(hyphen_suffixed_ids[-1])

        # Fallback: any UUID (hyphenated) or 32-hex in the PATH
        path_ids = re.findall(
            r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9a-fA-F]{32})",
            path,
        )
        if path_ids:
            raw = path_ids[0]
            return Config._hyphenate_uuid(re.sub(r"[^0-9a-fA-F]", "", raw))

        # Last resort: search the entire URL (may capture view IDs; less reliable)
        all_ids = re.findall(
            r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9a-fA-F]{32})",
            url,
        )
        if all_ids:
            raw = all_ids[0]
            return Config._hyphenate_uuid(re.sub(r"[^0-9a-fA-F]", "", raw))

        return None

    @staticmethod
    def _hyphenate_uuid(hexish: str) -> Optional[str]:
        """Normalize a 32-hex or hyphenated UUID string to hyphenated UUID.

        Returns None if the input cannot be normalized to 32 hex characters.
        """
        if not hexish:
            return None
        only_hex = re.sub(r"[^0-9a-fA-F]", "", hexish).lower()
        if len(only_hex) != 32:
            return None
        return (
            f"{only_hex[0:8]}-"
            f"{only_hex[8:12]}-"
            f"{only_hex[12:16]}-"
            f"{only_hex[16:20]}-"
            f"{only_hex[20:32]}"
        )


# Global config instance
config = Config() 