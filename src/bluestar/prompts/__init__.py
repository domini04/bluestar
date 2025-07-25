"""
BlueStar Prompt Templates

LangChain prompt templates for various LLM operations.
Centralized location for all prompt engineering and template management.
"""

from .commit_analysis import create_commit_analysis_prompt

__all__ = [
    "create_commit_analysis_prompt"
] 