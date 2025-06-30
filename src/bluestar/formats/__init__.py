"""
BlueStar Output Format Structures

Pydantic models for tool outputs and data exchange in the LangGraph workflow.
These structures ensure consistent, validated data flow between nodes.
"""

from .commit_data import CommitData, DiffData, CommitAnalysis
from .blog_formats import (
    GhostBlogPost, 
    GhostAuthor, 
    GhostTag, 
    BlogSection, 
    GhostPublishingResult
)

__all__ = [
    # Commit data structures
    "CommitData",
    "DiffData", 
    "CommitAnalysis",
    
    # Ghost blog structures
    "GhostBlogPost",
    "GhostAuthor", 
    "GhostTag",
    "BlogSection", 
    "GhostPublishingResult"
] 