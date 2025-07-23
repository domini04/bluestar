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
    
    def get_repository_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch repository metadata for project context.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository metadata (description, language, topics, etc.)
        """
        endpoint = f"repos/{owner}/{repo}"
        response = self._make_request(endpoint)
        
        return {
            "description": response.get("description") or "",
            "language": response.get("language") or "unknown",
            "topics": response.get("topics", []),
            "stars": response.get("stargazers_count", 0),
            "license": response.get("license", {}).get("name") if response.get("license") else None,
            "created_at": response.get("created_at"),
            "updated_at": response.get("updated_at")
        }
    
    def get_readme_summary(self, owner: str, repo: str, sha: str) -> Optional[str]:
        """
        Get first 1000 chars of README for context.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA to get README at specific point
            
        Returns:
            First 1000 characters of README content, or None if not found
        """
        try:
            endpoint = f"repos/{owner}/{repo}/readme?ref={sha}"
            response = self._make_request(endpoint)
            
            if response.get("type") == "file" and "content" in response:
                import base64
                content = base64.b64decode(response["content"]).decode("utf-8")
                return content[:1000]  # Token optimization
            
        except Exception:
            return None
        
        return None
    
    def get_primary_config_file(self, owner: str, repo: str, sha: str) -> Optional[Dict[str, Any]]:
        """
        Get main configuration file based on language detection.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA to get config at specific point
            
        Returns:
            Dictionary with config file info and content, or None if not found
        """
        # Try common config files in order of preference
        config_files = [
            "package.json",      # Node.js
            "pyproject.toml",    # Python (modern)
            "requirements.txt",  # Python (legacy)
            "pom.xml",          # Java/Maven
            "build.gradle",     # Java/Gradle
            "Cargo.toml",       # Rust
            "go.mod",           # Go
            "composer.json",    # PHP
        ]
        
        for config_file in config_files:
            try:
                endpoint = f"repos/{owner}/{repo}/contents/{config_file}?ref={sha}"
                response = self._make_request(endpoint)
                
                if response.get("type") == "file" and "content" in response:
                    import base64
                    content = base64.b64decode(response["content"]).decode("utf-8")
                    
                    return {
                        "file_name": config_file,
                        "content": content[:2000],  # Token limit
                        "project_type": self._detect_project_type(config_file)
                    }
                    
            except Exception:
                continue
        
        return None
    
    def get_core_context(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """
        Orchestrate core context fetching with error handling.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA for context
            
        Returns:
            Dictionary with all available core context data
        """
        from datetime import datetime, timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        context = {
            "repository_metadata": None,
            "readme_summary": None,
            "primary_config": None,
            "project_type": "unknown",
            "fetch_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Fetch repository metadata
        try:
            context["repository_metadata"] = self.get_repository_metadata(owner, repo)
            logger.debug(f"✅ Repository metadata fetched for {owner}/{repo}")
        except Exception as e:
            logger.debug(f"❌ Repository metadata fetch failed: {e}")
        
        # Fetch README summary
        try:
            readme = self.get_readme_summary(owner, repo, sha)
            if readme:
                context["readme_summary"] = readme
                logger.debug(f"✅ README summary fetched ({len(readme)} chars)")
        except Exception as e:
            logger.debug(f"❌ README summary fetch failed: {e}")
        
        # Fetch primary config
        try:
            config_data = self.get_primary_config_file(owner, repo, sha)
            if config_data:
                context["primary_config"] = config_data
                context["project_type"] = config_data["project_type"]
                logger.debug(f"✅ Primary config fetched: {config_data['file_name']}")
        except Exception as e:
            logger.debug(f"❌ Primary config fetch failed: {e}")
        
        return context
    
    def _detect_project_type(self, config_file: str) -> str:
        """
        Detect project type from config file name.
        
        Args:
            config_file: Name of the configuration file
            
        Returns:
            String identifier for project type
        """
        type_mapping = {
            "package.json": "javascript/node",
            "pyproject.toml": "python",
            "requirements.txt": "python", 
            "pom.xml": "java/maven",
            "build.gradle": "java/gradle",
            "Cargo.toml": "rust",
            "go.mod": "go",
            "composer.json": "php"
        }
        return type_mapping.get(config_file, "unknown") 