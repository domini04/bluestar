"""
Tests for GitHubClient module

Tests GitHub API client functionality including initialization, rate limiting,
and API interactions using mocked responses.
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone

from src.bluestar.tools.github_client import GitHubClient, GitHubRateLimit
from src.bluestar.core.exceptions import (
    ConfigurationError, RepositoryError, LLMError
)


class TestGitHubClientInitialization:
    """Test GitHubClient initialization and setup."""
    
    def test_initialization_with_explicit_token(self):
        """
        Test: GitHubClient initializes correctly with explicit token
        
        Checks:
        - Token is stored correctly
        - Base URL is set to GitHub API
        - Session is created
        - Rate limit starts as None
        """
        # Arrange & Act
        client = GitHubClient(token="test_token_123")
        
        # Assert
        assert client.token == "test_token_123"
        assert client.base_url == "https://api.github.com"
        assert client.session is not None
        assert client._rate_limit is None
        
        # Verify session has correct headers
        assert client.session.headers["Authorization"] == "token test_token_123"
        assert client.session.headers["Accept"] == "application/vnd.github.v3+json"
        assert client.session.headers["User-Agent"] == "BlueStar/1.0"
    
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token_456'})
    def test_initialization_with_environment_variable(self):
        """
        Test: GitHubClient uses GITHUB_TOKEN environment variable when no token provided
        
        Checks:
        - Environment variable is read correctly
        - Client initializes successfully with env token
        - Token precedence: explicit token overrides env var
        """
        # Arrange & Act - No explicit token provided
        client = GitHubClient()
        
        # Assert
        assert client.token == "env_token_456"
        assert client.session.headers["Authorization"] == "token env_token_456"
        
        # Test explicit token overrides env var
        client_explicit = GitHubClient(token="explicit_token")
        assert client_explicit.token == "explicit_token"
    
    @patch.dict('os.environ', {}, clear=True)
    def test_initialization_no_token_raises_error(self):
        """
        Test: GitHubClient raises ConfigurationError when no token is available
        
        Checks:
        - ConfigurationError is raised when no token provided and no env var
        - Error message is informative
        - No client instance is created
        """
        # Arrange & Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            GitHubClient()
        
        # Verify error message is helpful
        assert "GitHub token not configured" in str(exc_info.value)
        assert "GITHUB_TOKEN environment variable" in str(exc_info.value)


class TestGitHubClientRateLimit:
    """Test rate limit parsing and management functionality."""
    
    def test_rate_limit_parsing_from_headers(self):
        """
        Test: Rate limit information is correctly parsed from GitHub response headers
        
        Checks:
        - X-RateLimit-Limit header parsed as integer
        - X-RateLimit-Remaining header parsed as integer  
        - X-RateLimit-Reset header converted to datetime
        - GitHubRateLimit dataclass created correctly
        """
        # Arrange
        client = GitHubClient(token="test_token")
        mock_response = Mock()
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999", 
            "X-RateLimit-Reset": "1642694400"  # Unix timestamp
        }
        
        # Act
        rate_limit = client._parse_rate_limit(mock_response)
        
        # Assert
        assert isinstance(rate_limit, GitHubRateLimit)
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4999
        assert isinstance(rate_limit.reset_time, datetime)
        assert rate_limit.reset_time.tzinfo == timezone.utc
        
        # Test properties
        assert not rate_limit.is_exhausted  # 4999 > 0
        assert isinstance(rate_limit.reset_in_seconds, int)


class TestGitHubClientRepositoryParsing:
    """Test repository identifier parsing functionality."""
    
    def test_parse_repo_identifier_simple_format(self):
        """
        Test: Repository identifier parsing for simple "owner/repo" format
        
        Checks:
        - Simple format "owner/repo" parsed correctly
        - Returns tuple (owner, repo)
        - No modification of simple format
        """
        # Arrange & Act
        owner, repo = GitHubClient.parse_repo_identifier("microsoft/vscode")
        
        # Assert
        assert owner == "microsoft"
        assert repo == "vscode"
    
    def test_parse_repo_identifier_https_url(self):
        """
        Test: Repository identifier parsing for full HTTPS GitHub URLs
        
        Checks:
        - Full GitHub URL parsed correctly
        - "https://github.com/" prefix removed
        - ".git" suffix removed if present
        - Various URL formats handled
        """
        # Test full HTTPS URL
        owner, repo = GitHubClient.parse_repo_identifier("https://github.com/microsoft/vscode")
        assert owner == "microsoft"
        assert repo == "vscode"
        
        # Test HTTPS URL with .git suffix
        owner, repo = GitHubClient.parse_repo_identifier("https://github.com/microsoft/vscode.git")
        assert owner == "microsoft"
        assert repo == "vscode"
        
        # Test domain without protocol
        owner, repo = GitHubClient.parse_repo_identifier("github.com/microsoft/vscode")
        assert owner == "microsoft"
        assert repo == "vscode"
    
    def test_parse_repo_identifier_invalid_formats(self):
        """
        Test: Repository identifier parsing raises RepositoryError for invalid formats
        
        Checks:
        - Too few parts (just "owner") raises error
        - Too many parts ("owner/repo/extra") raises error
        - Empty string raises error
        - Error messages are helpful
        """
        # Test too few parts
        with pytest.raises(RepositoryError) as exc_info:
            GitHubClient.parse_repo_identifier("microsoft")
        assert "Invalid repository identifier" in str(exc_info.value)
        assert "Expected format" in str(exc_info.value)
        
        # Test too many parts
        with pytest.raises(RepositoryError) as exc_info:
            GitHubClient.parse_repo_identifier("microsoft/vscode/subfolder")
        assert "Invalid repository identifier" in str(exc_info.value)
        
        # Test empty string
        with pytest.raises(RepositoryError):
            GitHubClient.parse_repo_identifier("")


class TestGitHubClientAPIRequests:
    """Test actual GitHub API request functionality with mocked responses."""
    
    @patch('requests.Session.get')
    def test_get_commit_success(self, mock_get):
        """
        Test: Successful commit retrieval from GitHub API
        
        Checks:
        - Correct API endpoint called
        - Response JSON returned
        - Rate limit updated from headers
        - Session timeout applied
        """
        # Arrange
        client = GitHubClient(token="test_token")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sha": "abc123",
            "commit": {
                "message": "Fix authentication bug",
                "author": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "date": "2025-01-20T10:00:00Z"
                }
            },
            "files": [
                {
                    "filename": "auth.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2
                }
            ]
        }
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1642694400"
        }
        mock_get.return_value = mock_response
        
        # Act
        result = client.get_commit("microsoft", "vscode", "abc123")
        
        # Assert
        # Verify correct API call
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/microsoft/vscode/commits/abc123",
            timeout=30
        )
        
        # Verify response data
        assert result["sha"] == "abc123"
        assert result["commit"]["message"] == "Fix authentication bug"
        assert result["commit"]["author"]["name"] == "John Doe"
        assert len(result["files"]) == 1
        assert result["files"][0]["filename"] == "auth.py"
        
        # Verify rate limit was updated
        assert client._rate_limit is not None
        assert client._rate_limit.remaining == 4999
    
    @patch('requests.Session.get')
    def test_get_commit_404_error(self, mock_get):
        """
        Test: 404 error handling for non-existent repository or commit
        
        Checks:
        - 404 response raises RepositoryError
        - Error message indicates repo/commit not found
        - Rate limit still updated from headers
        - Proper exception type mapping
        """
        # Arrange
        client = GitHubClient(token="test_token")
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4998",
            "X-RateLimit-Reset": "1642694400"
        }
        
        # Configure the mock to raise HTTPError when raise_for_status() is called
        from requests.exceptions import HTTPError
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            client.get_commit("nonexistent", "repo", "invalid_sha")
        
        # Verify error message
        assert "Repository or commit not found" in str(exc_info.value)
        
        # Verify API was called
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/nonexistent/repo/commits/invalid_sha",
            timeout=30
        )
        
        # Verify rate limit was still updated
        assert client._rate_limit is not None
        assert client._rate_limit.remaining == 4998 