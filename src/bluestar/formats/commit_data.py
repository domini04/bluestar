"""
BlueStar Commit Data Structures

Pydantic models for Git commit data and analysis results.
These models ensure consistent structure for data flowing through the LangGraph workflow.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class DiffData(BaseModel):
    """Represents file diff information from a commit."""
    
    file_path: str = Field(description="Path to the file that was changed")
    change_type: Literal["added", "modified", "deleted", "renamed"] = Field(
        description="Type of change made to the file"
    )
    additions: int = Field(description="Number of lines added", ge=0)
    deletions: int = Field(description="Number of lines deleted", ge=0)
    diff_content: str = Field(description="The actual diff content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "src/components/Button.tsx",
                "change_type": "modified",
                "additions": 5,
                "deletions": 2,
                "diff_content": "+  const [isLoading, setIsLoading] = useState(false);\n-  const [loading, setLoading] = useState(false);"
            }
        }


class CommitData(BaseModel):
    """Structured commit data returned by CommitFetcher tool."""
    
    sha: str = Field(description="Git commit SHA hash")
    message: str = Field(description="Commit message")
    author: str = Field(description="Commit author name")
    author_email: str = Field(description="Commit author email")
    date: datetime = Field(description="Commit timestamp")
    branch: Optional[str] = Field(default=None, description="Branch name if available")
    
    # File changes
    files_changed: List[str] = Field(description="List of files modified in this commit")
    total_additions: int = Field(description="Total lines added across all files", ge=0)
    total_deletions: int = Field(description="Total lines deleted across all files", ge=0)
    
    # Detailed diff information
    diffs: List[DiffData] = Field(description="Detailed diff data for each changed file")
    
    # Metadata
    repository_path: str = Field(description="Path to the repository")
    tags: List[str] = Field(default_factory=list, description="Git tags at this commit")
    
    # Optional directory context
    project_structure: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Project directory structure (optional, filtered to relevant paths)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sha": "a1b2c3d4e5f6",
                "message": "Add user authentication feature",
                "author": "John Doe",
                "author_email": "john@example.com",
                "date": "2025-01-20T10:30:00Z",
                "branch": "feature/auth",
                "files_changed": ["src/auth.py", "tests/test_auth.py"],
                "total_additions": 15,
                "total_deletions": 3,
                "diffs": [],
                "repository_path": "/path/to/repo",
                "tags": ["v1.2.0"],
                "project_structure": {
                    "src/": {
                        "auth/": ["login.py", "register.py", "middleware.py"],
                        "components/": ["Button.tsx"],
                        "utils/": ["helpers.py"]
                    },
                    "tests/": {
                        "auth/": ["test_login.py"]
                    }
                }
            }
        }


class CommitAnalysis(BaseModel):
    """
    AI-powered analysis of a Git commit for blog generation.
    
    This model structures the output from LLM analysis to provide
    consistent, reliable data for blog post generation.
    """
    
    # Core categorization
    change_type: Literal["feature", "bugfix", "refactor", "performance", "security", "documentation", "other"] = Field(
        description="Primary type of change. Must be exactly one of: feature, bugfix, refactor, performance, security, documentation, or other"
    )
    
    # Content for blog generation
    technical_summary: str = Field(
        description="Technical explanation of what was changed, aimed at developers. Focus on implementation details, code structure, and technical decisions."
    )
    
    business_impact: str = Field(
        description="Explanation of why this change matters to users, stakeholders, or the business. Focus on user value, problem solved, or improvement gained."
    )
    
    # Structured insights (from original model)
    key_changes: List[str] = Field(
        description="List of the main changes made in this commit. Each item should be a concise, specific change (e.g., 'Added JWT authentication middleware', 'Updated user database schema')."
    )
    
    technical_details: List[str] = Field(
        description="Technical implementation details that developers would find valuable. Include specific technologies, patterns, or approaches used (e.g., 'Used bcrypt for password hashing', 'Implemented OAuth2 flow')."
    )
    
    affected_components: List[str] = Field(
        description="Components, modules, or areas of the codebase that were affected by this change (e.g., 'authentication module', 'user routes', 'database models')."
    )
    
    # Blog narrative structure
    narrative_angle: str = Field(
        description="Suggested narrative structure for the blog post. Explain how to tell this change as a compelling story (e.g., 'Problem-solution approach', 'Before-after comparison', 'Technical deep dive')."
    )
    
    # Context assessment for progressive enhancement
    context_assessment: Literal["sufficient", "needs_enhancement", "insufficient"] = Field(
        description="Assessment of context completeness. Must be exactly one of: 'sufficient', 'needs_enhancement', or 'insufficient'"
    )
    
    context_assessment_details: Optional[str] = Field(
        default=None,
        description="Detailed explanation of what additional context would improve the analysis. Be specific about what information is missing (e.g., 'Missing component hierarchy for React changes', 'Database schema context needed for model changes'). Only provide if context_assessment is 'needs_enhancement' or 'insufficient'."
    )
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"CommitAnalysis(type={self.change_type}, "
                f"context={self.context_assessment}, "
                f"changes={len(self.key_changes)})")
    
    def needs_enhanced_context(self) -> bool:
        """Check if this analysis indicates enhanced context would be helpful."""
        return self.context_assessment in ["needs_enhancement", "insufficient"]
    
    def is_sufficient_for_blog_generation(self) -> bool:
        """Check if analysis has sufficient context for quality blog generation."""
        return self.context_assessment == "sufficient" 