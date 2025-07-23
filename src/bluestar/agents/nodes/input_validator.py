"""
Input Validator Node for BlueStar LangGraph Workflow

Validates structured input data in AgentState.
Handles repository identifier validation, commit SHA validation, and error reporting.
"""

import re
from typing import Tuple, Optional

from ..state import AgentState
from ...tools.github_client import GitHubClient
from ...core.exceptions import RepositoryError


def validate_repository(repo_identifier: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate repository identifier using existing GitHubClient logic.
    
    Args:
        repo_identifier: Repository identifier (various formats supported)
        
    Returns:
        Tuple of (is_valid, normalized_repo, error_message)
        
    Examples:
        "microsoft/vscode" → (True, "microsoft/vscode", None)
        "https://github.com/user/repo" → (True, "user/repo", None)
        "invalid" → (False, "", "Invalid repository identifier...")
    """
    if not repo_identifier or not repo_identifier.strip():
        return False, "", "Repository identifier is required"
    
    try:
        # Use existing GitHubClient validation logic
        owner, repo = GitHubClient.parse_repo_identifier(repo_identifier)
        normalized_repo = f"{owner}/{repo}"
        return True, normalized_repo, None
        
    except RepositoryError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", f"Unexpected error parsing repository: {e}"


def validate_commit_sha(commit_sha: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate commit SHA format and structure.
    
    Args:
        commit_sha: Commit SHA string
        
    Returns:
        Tuple of (is_valid, cleaned_sha, error_message)
        
    Examples:
        "abc123def456..." → (True, "abc123def456...", None)
        "invalid" → (False, "", "Commit SHA must be exactly 40 characters")
        "xyz123" → (False, "", "Invalid characters in commit SHA")
    """
    if not commit_sha or not commit_sha.strip():
        return False, "", "Commit SHA is required"
    
    # Clean whitespace
    cleaned_sha = commit_sha.strip()
    
    # Check length
    if len(cleaned_sha) != 40:
        return False, "", f"Commit SHA must be exactly 40 characters (got {len(cleaned_sha)})"
    
    # Check character set (hexadecimal)
    if not re.match(r"^[0-9a-fA-F]{40}$", cleaned_sha):
        return False, "", "Commit SHA must contain only hexadecimal characters (0-9, a-f, A-F)"
    
    return True, cleaned_sha.lower(), None


def input_validator_node(state: AgentState) -> AgentState:
    """
    Input Validator Node - Validate structured input data.
    
    Validates the structured input fields in the AgentState:
    - state.repo_identifier (repository validation)
    - state.commit_sha (commit SHA validation)
    - state.user_instructions (optional, no validation needed)
    
    Updates state with validation results and any errors.
    
    Args:
        state: Current workflow state with structured input data
        
    Returns:
        Updated state with validation results
    """
    print(f"🔄 InputValidator: Validating structured inputs")
    
    # Track validation results
    all_valid = True
    
    # Validate repository identifier
    repo_valid, normalized_repo, repo_error = validate_repository(state.repo_identifier)
    
    if repo_valid:
        state.repo_identifier = normalized_repo  # Use normalized version
        print(f"   ✅ Repository: {normalized_repo}")
    else:
        state.add_error(f"Repository validation failed: {repo_error}")
        print(f"   ❌ Repository: {repo_error}")
        all_valid = False
    
    # Validate commit SHA
    sha_valid, cleaned_sha, sha_error = validate_commit_sha(state.commit_sha)
    
    if sha_valid:
        state.commit_sha = cleaned_sha  # Use cleaned version
        print(f"   ✅ Commit SHA: {cleaned_sha[:8]}...")
    else:
        state.add_error(f"Commit SHA validation failed: {sha_error}")
        print(f"   ❌ Commit SHA: {sha_error}")
        all_valid = False
    
    # Handle optional instructions (no validation needed)
    if state.user_instructions:
        print(f"   ✅ Instructions: {state.user_instructions[:50]}{'...' if len(state.user_instructions) > 50 else ''}")
    
    # Mark step completion status
    if all_valid:
        state.mark_step_complete("input_validation")
        print("   ✅ Input validation completed successfully")
    else:
        print("   ❌ Input validation failed - workflow will terminate")
        # Don't mark as complete if validation failed
    
    return state 