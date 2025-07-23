"""
CommitFetcher Node for BlueStar LangGraph Workflow

Step 3: Enhanced error handling with user-friendly messages.
"""

import logging
from ..state import AgentState
from ...tools.github_client import GitHubClient
from ...tools.commit_parser import CommitDataParser
from ...core.exceptions import (
    ConfigurationError,
    RepositoryError, 
    LLMError,
    InvalidCommitError
)

logger = logging.getLogger(__name__)


class CommitFetcherErrorHandler:
    """Helper utility for translating technical exceptions to user-friendly messages."""
    
    @staticmethod
    def get_user_message(exception: Exception, repo: str, commit_sha: str) -> str:
        """
        Translate technical exceptions to user-friendly error messages.
        
        Args:
            exception: The caught exception
            repo: Repository identifier for context
            commit_sha: Commit SHA for context
            
        Returns:
            User-friendly error message with actionable guidance
        """
        if isinstance(exception, ConfigurationError):
            if "GitHub token" in str(exception):
                return (
                    "GitHub access not configured. Please set your GITHUB_TOKEN environment variable "
                    "with a valid GitHub personal access token. Visit https://github.com/settings/tokens "
                    "to create one with 'repo' permissions."
                )
            else:
                return f"Configuration error: {str(exception)}. Please check your GitHub settings."
        
        elif isinstance(exception, RepositoryError):
            commit_short = commit_sha[:8] if len(commit_sha) >= 8 else commit_sha
            return (
                f"Repository '{repo}' or commit '{commit_short}...' not found. "
                "Please verify: 1) Repository name is correct, 2) Repository is public or you have access, "
                "3) Commit SHA exists in this repository."
            )
        
        elif isinstance(exception, LLMError):
            if "rate limit" in str(exception).lower():
                return (
                    "GitHub API rate limit reached. Please wait 20 minutes or use a different GitHub token. "
                    "Consider upgrading to GitHub Pro for higher rate limits."
                )
            elif "timed out" in str(exception).lower():
                return (
                    "GitHub API connection timed out. Please check your internet connection and try again. "
                    "If the problem persists, GitHub may be experiencing issues."
                )
            elif "forbidden" in str(exception).lower():
                return (
                    "GitHub access denied. Your token may lack repository permissions. "
                    "Please ensure your GitHub token has 'repo' scope for private repositories "
                    "or 'public_repo' scope for public repositories."
                )
            else:
                return (
                    "GitHub API request failed. This may be a temporary issue. "
                    "Please try again in a few moments."
                )
        
        elif isinstance(exception, InvalidCommitError):
            return (
                f"Commit data from '{repo}' is invalid or incomplete. "
                "This may indicate a corrupted commit or GitHub API issue. Please try a different commit."
            )
        
        else:
            # Fallback for unexpected errors
            return (
                f"Unexpected error while fetching commit data: {str(exception)}. "
                "Please try again or contact support if the issue persists."
            )


def commit_fetcher_node(state: AgentState) -> AgentState:
    """
    CommitFetcher LangGraph node - Enhanced error handling.
    
    Step 3: Fetches commit data from GitHub API with user-friendly error messages.
    
    Args:
        state: AgentState with validated repo_identifier and commit_sha
        
    Returns:
        Updated AgentState with commit_data populated or user-friendly errors
        
    Note: Input validation is handled by Input Validator node - 
          this node can trust that data is already validated.
    """
    logger.info(f"🔄 CommitFetcher: Fetching commit {state.commit_sha} from {state.repo_identifier}")
    
    try:
        # Initialize GitHub client (uses existing configuration)
        github_client = GitHubClient()
        
        # Parse repository identifier into owner/repo components
        logger.debug(f"Parsing repository identifier: {state.repo_identifier}")
        owner, repo = GitHubClient.parse_repo_identifier(state.repo_identifier)
        logger.debug(f"Parsed repository: {owner}/{repo}")
        
        # Fetch commit metadata from GitHub API
        logger.debug(f"Fetching commit metadata for {state.commit_sha}")
        commit_response = github_client.get_commit(owner, repo, state.commit_sha)
        
        # Fetch commit diff content from GitHub API  
        logger.debug(f"Fetching commit diff for {state.commit_sha}")
        diff_content = github_client.get_commit_diff(owner, repo, state.commit_sha)
        
        # Fetch core project context for enhanced analysis
        logger.debug(f"Fetching core project context for {owner}/{repo}")
        try:
            core_context = github_client.get_core_context(owner, repo, state.commit_sha)
            context_sources = []
            if core_context.get("repository_metadata"):
                context_sources.append("repository_metadata")
            if core_context.get("readme_summary"):
                context_sources.append("readme_summary")
            if core_context.get("primary_config"):
                context_sources.append("primary_config")
            
            logger.info(f"✅ Core context fetched: {len(context_sources)} sources ({', '.join(context_sources)})")
            logger.debug(f"Project type detected: {core_context.get('project_type', 'unknown')}")
            
        except Exception as context_error:
            logger.warning(f"⚠️ Core context fetch failed: {context_error}")
            logger.debug("Continuing with basic commit analysis (context enhancement can be applied later)")
            core_context = None
        
        # Parse API responses into structured CommitData with enhanced context
        logger.debug("Parsing commit data using enhanced CommitDataParser")
        commit_data = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content=diff_content,
            repo_identifier=state.repo_identifier,
            core_context=core_context
        )
        
        # Update state with structured commit data
        state.commit_data = commit_data
        logger.info(f"✅ CommitFetcher: Successfully fetched commit data for {commit_data.sha}")
        logger.debug(f"Commit summary: {commit_data.message[:100]}...")
        
        # Log enhanced context information
        if commit_data.project_structure:
            logger.info(f"📊 Enhanced context available: project type '{commit_data.project_structure.get('project_type', 'unknown')}'")
            if commit_data.project_structure.get('readme_summary'):
                readme_len = len(commit_data.project_structure['readme_summary'])
                logger.debug(f"📄 README summary: {readme_len} characters")
            if commit_data.project_structure.get('primary_config'):
                config_name = commit_data.project_structure['primary_config'].get('file_name', 'unknown')
                logger.debug(f"⚙️ Primary config: {config_name}")
        else:
            logger.debug("📊 Using basic commit analysis (no enhanced context)")
        
    except (ConfigurationError, RepositoryError, LLMError, InvalidCommitError) as e:
        # Handle known BlueStar exceptions with user-friendly messages
        user_msg = CommitFetcherErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.errors.append(user_msg)
        
        # Log technical details for debugging
        logger.error(f"CommitFetcher technical error: {e}", exc_info=True)
        logger.debug(f"Error context: repo={state.repo_identifier}, sha={state.commit_sha}")
        
    except Exception as e:
        # Handle unexpected errors
        user_msg = CommitFetcherErrorHandler.get_user_message(
            e, state.repo_identifier, state.commit_sha
        )
        state.errors.append(user_msg)
        
        # Log unexpected error with full context
        logger.error(
            f"Unexpected error in CommitFetcher: {e}",
            exc_info=True,
            extra={
                'repo_identifier': state.repo_identifier,
                'commit_sha': state.commit_sha,
                'workflow_id': state.workflow_id
            }
        )
    
    # Mark step complete regardless of success/failure
    state.mark_step_complete("commit_fetching")
    
    return state 