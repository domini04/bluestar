"""
GitHub API Client for BlueStar

Handles GitHub API authentication, rate limiting, and commit data retrieval.
"""

import os
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.exceptions import (
    InvalidCommitError,
    RepositoryError,
    LLMError,
    ConfigurationError
)


@dataclass
class GitHubRateLimit:
    """GitHub API rate limit information."""
    limit: int
    remaining: int
    reset_time: datetime
    
    @property
    def is_exhausted(self) -> bool:
        return self.remaining <= 0
    
    @property
    def reset_in_seconds(self) -> int:
        return max(0, int((self.reset_time - datetime.now(timezone.utc)).total_seconds()))


class GitHubClient:
    """
    GitHub API client with authentication, rate limiting, and error handling.
    
    Handles all GitHub API interactions for commit data retrieval.
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ConfigurationError("GitHub token not configured. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://api.github.com"
        self.session = self._create_session()
        self._rate_limit: Optional[GitHubRateLimit] = None
    
    def _create_session(self) -> requests.Session:
        """Create configured requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BlueStar/1.0"
        })
        
        return session
    
    def _parse_rate_limit(self, response: requests.Response) -> GitHubRateLimit:
        """Parse rate limit information from response headers."""
        return GitHubRateLimit(
            limit=int(response.headers.get("X-RateLimit-Limit", 0)),
            remaining=int(response.headers.get("X-RateLimit-Remaining", 0)),
            reset_time=datetime.fromtimestamp(
                int(response.headers.get("X-RateLimit-Reset", 0)),
                tz=timezone.utc
            )
        )
    

    def _handle_rate_limit(self, rate_limit: GitHubRateLimit) -> None:
        """Handle rate limit by waiting if necessary."""
        if rate_limit.is_exhausted:
            wait_time = rate_limit.reset_in_seconds + 1  # Add 1 second buffer
            if wait_time > 300:  # Don't wait more than 5 minutes
                raise LLMError(f"GitHub API rate limit exceeded. Reset in {wait_time} seconds.")
            
            print(f"GitHub API rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make authenticated request to GitHub API with rate limit handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Check existing rate limit
        if self._rate_limit and self._rate_limit.is_exhausted:
            self._handle_rate_limit(self._rate_limit)
        
        try:
            response = self.session.get(url, timeout=30)
            
            # Update rate limit info
            self._rate_limit = self._parse_rate_limit(response)
            
            # Handle rate limit
            if response.status_code == 429:
                self._handle_rate_limit(self._rate_limit)
                # Retry once after waiting
                response = self.session.get(url, timeout=30)
                self._rate_limit = self._parse_rate_limit(response)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise LLMError(f"GitHub API request timed out: {url}")
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                raise RepositoryError(f"Repository or commit not found: {endpoint}")
            elif response.status_code == 403:
                raise ConfigurationError("GitHub API access forbidden. Check token permissions.")
            else:
                raise LLMError(f"GitHub API request failed: {e}")
    
    def get_commit(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """
        Get commit data from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name  
            sha: Commit SHA
            
        Returns:
            Commit data dictionary from GitHub API
        """
        endpoint = f"repos/{owner}/{repo}/commits/{sha}"
        return self._make_request(endpoint)
    
    def get_commit_diff(self, owner: str, repo: str, sha: str) -> str:
        """
        Get commit diff from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            
        Returns:
            Diff content as string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        
        # Request diff format
        headers = self.session.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.RequestException as e:
            raise LLMError(f"Failed to fetch commit diff: {e}")
    
    @staticmethod
    def parse_repo_identifier(repo_identifier: str) -> Tuple[str, str]:
        """
        Parse repository identifier into owner and repo name.
        
        Args:
            repo_identifier: Repository identifier (owner/repo or GitHub URL)
            
        Returns:
            Tuple of (owner, repo)
            
        Raises:
            RepositoryError: If identifier format is invalid
        """
        # Handle GitHub URLs
        if repo_identifier.startswith("https://github.com/"):
            repo_identifier = repo_identifier.replace("https://github.com/", "")
        elif repo_identifier.startswith("github.com/"):
            repo_identifier = repo_identifier.replace("github.com/", "")
        
        # Remove .git suffix if present
        if repo_identifier.endswith(".git"):
            repo_identifier = repo_identifier[:-4]
        
        # Split into owner/repo
        parts = repo_identifier.strip("/").split("/")
        if len(parts) != 2:
            raise RepositoryError(
                f"Invalid repository identifier: {repo_identifier}. "
                "Expected format: 'owner/repo' or 'https://github.com/owner/repo'"
            )
        
        return parts[0], parts[1]
    
    @property
    def rate_limit_info(self) -> Optional[GitHubRateLimit]:
        """Get current rate limit information."""
        return self._rate_limit 