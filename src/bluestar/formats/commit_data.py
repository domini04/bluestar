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
    """Structured analysis results from CommitAnalyzer node."""
    
    commit_data: CommitData = Field(description="Original commit data")
    
    # Analysis results
    commit_types: List[Literal["feature", "bugfix", "refactor", "docs", "test", "chore", "breaking"]] = Field(
        default_factory=list,
        description="Categories this commit falls into (can be multiple)"
    )
    summary: str = Field(description="Human-readable summary of changes")
    impact_level: Literal["low", "medium", "high"] = Field(
        description="Assessed impact level of the changes"
    )
    
    # Extracted insights
    key_changes: List[str] = Field(description="List of key changes made")
    technical_details: List[str] = Field(description="Technical implementation details")
    affected_components: List[str] = Field(description="Components/modules affected")
    
    # Context for blog generation
    narrative_angle: str = Field(description="Suggested narrative approach for blog post")
    

    class Config:
        json_schema_extra = {
            "example": {
                "commit_data": {},  # Would contain CommitData example
                "commit_types": ["feature", "refactor"],
                "summary": "Added user authentication with JWT tokens",
                "impact_level": "high",
                "key_changes": ["JWT authentication", "User login/logout", "Protected routes"],
                "technical_details": ["bcrypt password hashing", "JWT token generation", "Middleware protection"],
                "affected_components": ["auth module", "user routes", "middleware"],
                "narrative_angle": "Security enhancement for user management",
            }
        } 