"""
BlueStar LangSmith Tracing Integration

Simple LangSmith tracing setup following the standard approach.
Sets environment variables and lets LangSmith automatically trace LangChain calls.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)


def is_tracing_enabled() -> bool:
    """
    Check if LangSmith tracing is enabled and properly configured.
    
    Returns:
        bool: True if tracing is enabled with valid API key
    """
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1", "yes", "on")
    api_key_exists = bool(os.getenv("LANGSMITH_API_KEY"))
    
    return tracing_enabled and api_key_exists


def setup_langsmith_tracing(project_name: str = "bluestar-default") -> bool:
    """
    Set up LangSmith tracing using standard environment variables.
    
    Args:
        project_name: Project name for organizing traces
        
    Returns:
        bool: True if tracing is available and configured
    """
    if not is_tracing_enabled():
        logger.info("LangSmith tracing is disabled or LANGSMITH_API_KEY not set")
        return False
    
    try:
        # Set project name (other env vars should already be set)
        if not os.getenv("LANGSMITH_PROJECT"):
            os.environ["LANGSMITH_PROJECT"] = project_name
        
        # Verify LangSmith is available
        from langsmith import Client
        client = Client()
        
        current_project = os.getenv("LANGSMITH_PROJECT", project_name)
        logger.info(f"LangSmith tracing enabled (project: {current_project})")
        return True
        
    except ImportError:
        logger.warning("LangSmith not installed - tracing disabled")
        return False
    except Exception as e:
        logger.warning(f"LangSmith setup failed: {e}")
        return False


def get_tracing_info() -> Dict[str, Any]:
    """Get current LangSmith tracing configuration info."""
    return {
        "enabled": is_tracing_enabled(),
        "project": os.getenv("LANGSMITH_PROJECT", "not-set"),
        "endpoint": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "api_key_configured": bool(os.getenv("LANGSMITH_API_KEY"))
    }


# Auto-initialize tracing for main application (but not during tests)
if not os.getenv("PYTEST_CURRENT_TEST"):
    setup_langsmith_tracing() 