#!/usr/bin/env python3
"""
Core Context Implementation Tests

Tests the enhanced GitHubClient core context methods and CommitDataParser integration.
Covers both success scenarios and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import json
from datetime import datetime, timezone

# Import our modules
from bluestar.tools.github_client import GitHubClient
from bluestar.tools.commit_parser import CommitDataParser
from bluestar.core.exceptions import ConfigurationError, RepositoryError, LLMError


class TestGitHubClientCoreContext:
    """Test GitHubClient core context methods."""
    
    def setup_method(self):
        """Set up test client with mocked session."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
            self.client = GitHubClient()
    
    def test_get_repository_metadata_success(self):
        """Test successful repository metadata fetching."""
        # Mock API response
        mock_response = {
            "description": "AI-powered blog generation agent",
            "language": "Python",
            "topics": ["ai", "blog", "automation"],
            "stargazers_count": 42,
            "license": {"name": "MIT"},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-20T10:30:00Z"
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response):
            result = self.client.get_repository_metadata("domini04", "bluestar")
        
        expected = {
            "description": "AI-powered blog generation agent",
            "language": "Python",
            "topics": ["ai", "blog", "automation"],
            "stars": 42,
            "license": "MIT",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-20T10:30:00Z"
        }
        
        assert result == expected
    
    def test_get_repository_metadata_minimal_data(self):
        """Test repository metadata with minimal/missing fields."""
        # Mock API response with missing optional fields
        mock_response = {
            "description": None,
            "language": None,
            "topics": [],
            "stargazers_count": 0,
            "license": None,
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response):
            result = self.client.get_repository_metadata("user", "minimal-repo")
        
        expected = {
            "description": "",
            "language": "unknown",
            "topics": [],
            "stars": 0,
            "license": None,
            "created_at": None,
            "updated_at": None
        }
        
        assert result == expected
    
    def test_get_readme_summary_success(self):
        """Test successful README summary fetching."""
        readme_content = "# BlueStar\n\nAI-powered blog generation agent for developers." + "x" * 1500
        encoded_content = base64.b64encode(readme_content.encode()).decode()
        
        mock_response = {
            "type": "file",
            "content": encoded_content
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response):
            result = self.client.get_readme_summary("domini04", "bluestar", "abc123")
        
        # Should be truncated to 1000 chars
        assert len(result) == 1000
        assert result.startswith("# BlueStar")
    
    def test_get_readme_summary_not_found(self):
        """Test README summary when file doesn't exist."""
        with patch.object(self.client, '_make_request', side_effect=Exception("404")):
            result = self.client.get_readme_summary("user", "no-readme", "abc123")
        
        assert result is None
    
    def test_get_readme_summary_invalid_format(self):
        """Test README summary with invalid response format."""
        mock_response = {
            "type": "tree",  # Not a file
            "content": "invalid"
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response):
            result = self.client.get_readme_summary("user", "repo", "abc123")
        
        assert result is None
    
    def test_get_primary_config_file_package_json(self):
        """Test config file detection for Node.js project."""
        package_json = {
            "name": "my-app",
            "version": "1.0.0",
            "dependencies": {"react": "^18.0.0"}
        }
        encoded_content = base64.b64encode(json.dumps(package_json).encode()).decode()
        
        mock_response = {
            "type": "file",
            "content": encoded_content
        }
        
        with patch.object(self.client, '_make_request', return_value=mock_response):
            result = self.client.get_primary_config_file("user", "react-app", "abc123")
        
        assert result["file_name"] == "package.json"
        assert result["project_type"] == "javascript/node"
        assert "react" in result["content"]
        assert len(result["content"]) <= 2000
    
    def test_get_primary_config_file_pyproject_toml(self):
        """Test config file detection for Python project."""
        pyproject_content = '''[project]
name = "bluestar"
version = "0.1.0"
dependencies = ["langchain", "pydantic"]
'''
        encoded_content = base64.b64encode(pyproject_content.encode()).decode()
        
        # First call fails (no package.json), second succeeds (pyproject.toml)
        def mock_make_request(endpoint):
            if "package.json" in endpoint:
                raise Exception("404")
            elif "pyproject.toml" in endpoint:
                return {"type": "file", "content": encoded_content}
            else:
                raise Exception("404")
        
        with patch.object(self.client, '_make_request', side_effect=mock_make_request):
            result = self.client.get_primary_config_file("domini04", "bluestar", "abc123")
        
        assert result["file_name"] == "pyproject.toml"
        assert result["project_type"] == "python"
        assert "langchain" in result["content"]
    
    def test_get_primary_config_file_none_found(self):
        """Test config file detection when no config files exist."""
        with patch.object(self.client, '_make_request', side_effect=Exception("404")):
            result = self.client.get_primary_config_file("user", "no-config", "abc123")
        
        assert result is None
    
    def test_get_core_context_full_success(self):
        """Test full core context fetching with all components successful."""
        # Mock all the individual methods
        mock_repo_meta = {"description": "Test repo", "language": "Python"}
        mock_readme = "# Test Project"
        mock_config = {"file_name": "pyproject.toml", "project_type": "python"}
        
        with patch.object(self.client, 'get_repository_metadata', return_value=mock_repo_meta), \
             patch.object(self.client, 'get_readme_summary', return_value=mock_readme), \
             patch.object(self.client, 'get_primary_config_file', return_value=mock_config):
            
            result = self.client.get_core_context("user", "repo", "abc123")
        
        assert result["repository_metadata"] == mock_repo_meta
        assert result["readme_summary"] == mock_readme
        assert result["primary_config"] == mock_config
        assert result["project_type"] == "python"
        assert "fetch_timestamp" in result
    
    def test_get_core_context_partial_failure(self):
        """Test core context fetching with some components failing."""
        mock_repo_meta = {"description": "Test repo", "language": "Python"}
        
        with patch.object(self.client, 'get_repository_metadata', return_value=mock_repo_meta), \
             patch.object(self.client, 'get_readme_summary', side_effect=Exception("README failed")), \
             patch.object(self.client, 'get_primary_config_file', return_value=None):
            
            result = self.client.get_core_context("user", "repo", "abc123")
        
        # Should have repo metadata but not README or config
        assert result["repository_metadata"] == mock_repo_meta
        assert result["readme_summary"] is None
        assert result["primary_config"] is None
        assert result["project_type"] == "unknown"
    
    def test_get_core_context_all_failures(self):
        """Test core context fetching when all components fail."""
        with patch.object(self.client, 'get_repository_metadata', side_effect=Exception("Repo failed")), \
             patch.object(self.client, 'get_readme_summary', side_effect=Exception("README failed")), \
             patch.object(self.client, 'get_primary_config_file', side_effect=Exception("Config failed")):
            
            result = self.client.get_core_context("user", "repo", "abc123")
        
        # Should still return structure with None values
        assert result["repository_metadata"] is None
        assert result["readme_summary"] is None
        assert result["primary_config"] is None
        assert result["project_type"] == "unknown"
        assert "fetch_timestamp" in result
    
    def test_detect_project_type_mappings(self):
        """Test project type detection for various config files."""
        test_cases = [
            ("package.json", "javascript/node"),
            ("pyproject.toml", "python"),
            ("requirements.txt", "python"),
            ("pom.xml", "java/maven"),
            ("build.gradle", "java/gradle"),
            ("Cargo.toml", "rust"),
            ("go.mod", "go"),
            ("composer.json", "php"),
            ("unknown.conf", "unknown")
        ]
        
        for config_file, expected_type in test_cases:
            result = self.client._detect_project_type(config_file)
            assert result == expected_type, f"Failed for {config_file}"


class TestCommitDataParserCoreContext:
    """Test CommitDataParser integration with core context."""
    
    def test_parse_commit_data_with_context(self):
        """Test commit parsing with core context data."""
        # Mock commit response
        commit_response = {
            "sha": "abc123def456",
            "commit": {
                "message": "Add authentication feature",
                "author": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "date": "2025-01-20T10:30:00Z"
                }
            },
            "files": [
                {"filename": "auth.py", "status": "added", "additions": 50, "deletions": 0}
            ]
        }
        
        # Mock core context (simpler format that matches our implementation)
        core_context = {
            "repository_metadata": {
                "description": "Authentication library",
                "language": "Python",
                "topics": ["auth", "security"],
                "stars": 100,
                "license": "MIT"
            },
            "readme_summary": "# Auth Library\nSecure authentication for web apps",
            "primary_config": {
                "file_name": "pyproject.toml",
                "project_type": "python",
                "content": "[project]\nname = \"auth-lib\""
            },
            "project_type": "python",
            "fetch_timestamp": "2025-01-20T10:30:00Z"
        }
        
        result = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content="diff --git a/auth.py b/auth.py\n+def authenticate():",
            repo_identifier="user/auth-lib",
            core_context=core_context
        )
        
        # Verify basic commit data
        assert result.sha == "abc123def456"
        assert result.message == "Add authentication feature"
        assert result.author == "John Doe"
        
        # Verify core context integration (raw context passed through)
        assert result.project_structure is not None
        project_data = result.project_structure
        
        assert project_data["repository_metadata"]["description"] == "Authentication library"
        assert project_data["repository_metadata"]["language"] == "Python"
        assert project_data["readme_summary"] == "# Auth Library\nSecure authentication for web apps"
        assert project_data["primary_config"]["project_type"] == "python"
        assert project_data["project_type"] == "python"
    
    def test_parse_commit_data_without_context(self):
        """Test commit parsing without core context (backward compatibility)."""
        commit_response = {
            "sha": "def456ghi789",
            "commit": {
                "message": "Fix bug",
                "author": {
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "date": "2025-01-20T11:00:00Z"
                }
            },
            "files": []
        }
        
        result = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content="",
            repo_identifier="user/repo"
            # No core_context parameter
        )
        
        assert result.sha == "def456ghi789"
        assert result.project_structure is None  # Should be None when no context
    
    def test_parse_commit_data_empty_context(self):
        """Test commit parsing with empty core context."""
        commit_response = {
            "sha": "ghi789jkl012",
            "commit": {
                "message": "Update docs",
                "author": {
                    "name": "Bob Smith",
                    "email": "bob@example.com",
                    "date": "2025-01-20T12:00:00Z"
                }
            },
            "files": []
        }
        
        result = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content="",
            repo_identifier="user/repo",
            core_context={}  # Empty context
        )
        
        assert result.sha == "ghi789jkl012"
        assert result.project_structure == {}  # Should be empty dict
    
    # REMOVED: Tests for _process_core_context method (not implemented in simpler approach)
    # def test_process_core_context_partial_data(self):
    # def test_process_core_context_config_content_truncation(self):
    
    def test_parse_commit_data_backward_compatibility(self):
        """Test that old tests still work with our enhanced parser."""
        commit_response = {
            "sha": "compat123",
            "commit": {
                "message": "Compatibility test",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2025-01-20T10:30:00Z"
                }
            },
            "files": []
        }
        
        # Test both old way (no context) and new way (with context)
        old_result = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content="",
            repo_identifier="user/repo"
        )
        
        new_result = CommitDataParser.parse_commit_data(
            commit_response=commit_response,
            diff_content="",
            repo_identifier="user/repo",
            core_context={"test": "context"}
        )
        
        # Basic data should be the same
        assert old_result.sha == new_result.sha
        assert old_result.message == new_result.message
        
        # Only project_structure should differ
        assert old_result.project_structure is None
        assert new_result.project_structure == {"test": "context"}


class TestCoreContextIntegration:
    """Integration tests for core context end-to-end workflow."""
    
    def test_full_integration_success(self):
        """Test complete workflow from GitHubClient to CommitData."""
        # This would be a more complex integration test
        # For now, let's test the key integration points
        
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
            client = GitHubClient()
        
        # Mock the core context response
        mock_context = {
            "repository_metadata": {"description": "Test", "language": "Python"},
            "readme_summary": "# Test Project",
            "primary_config": {"file_name": "pyproject.toml", "project_type": "python"},
            "project_type": "python",
            "fetch_timestamp": "2025-01-20T10:30:00Z"
        }
        
        mock_commit_response = {
            "sha": "test123",
            "commit": {
                "message": "Test commit",
                "author": {"name": "Test", "email": "test@test.com", "date": "2025-01-20T10:30:00Z"}
            },
            "files": []
        }
        
        with patch.object(client, 'get_core_context', return_value=mock_context):
            # This simulates what the CommitFetcher will do
            core_context = client.get_core_context("user", "repo", "abc123")
            
            commit_data = CommitDataParser.parse_commit_data(
                commit_response=mock_commit_response,
                diff_content="",
                repo_identifier="user/repo",
                core_context=core_context
            )
        
        # Verify integration (simpler format matching our implementation)
        assert commit_data.project_structure is not None
        assert commit_data.project_structure["project_type"] == "python"
        assert "repository_metadata" in commit_data.project_structure
        assert "primary_config" in commit_data.project_structure


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"]) 