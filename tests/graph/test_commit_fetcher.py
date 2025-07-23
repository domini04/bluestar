"""
Test Script for CommitFetcher Node

Tests the CommitFetcher node functionality including:
- Successful commit data fetching
- Error handling scenarios
- State mutations and workflow integration
- Enhanced user-friendly error messages
"""

import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from bluestar.agents.state import AgentState
from bluestar.agents.nodes.commit_fetcher import commit_fetcher_node, CommitFetcherErrorHandler
from bluestar.core.exceptions import ConfigurationError, RepositoryError, LLMError, InvalidCommitError


def test_successful_commit_fetching():
    """Test successful commit data fetching with real-like data."""
    print("🧪 Testing Successful Commit Fetching")
    print("=" * 50)
    
    # Create test state
    state = AgentState(
        repo_identifier="microsoft/vscode",
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
        user_instructions="Focus on performance improvements"
    )
    
    # Mock GitHub API responses
    mock_commit_response = {
        "sha": "a1b2c3d4e5f6789012345678901234567890abcd",
        "commit": {
            "message": "Improve editor performance with virtual scrolling",
            "author": {
                "name": "Developer",
                "email": "dev@example.com",
                "date": "2025-01-20T10:30:00Z"
            }
        },
        "files": [
            {
                "filename": "src/editor.ts",
                "status": "modified",
                "additions": 25,
                "deletions": 10
            }
        ]
    }
    
    mock_diff_content = """diff --git a/src/editor.ts b/src/editor.ts
index 1234567..abcdefg 100644
--- a/src/editor.ts
+++ b/src/editor.ts
@@ -100,7 +100,12 @@ class Editor {
   render() {
-    // Old rendering logic
+    // New virtual scrolling implementation
+    this.virtualScroll.render();
   }
 }"""
    
    # Mock the GitHub API calls
    with patch('bluestar.agents.nodes.commit_fetcher.GitHubClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_commit.return_value = mock_commit_response
        mock_client.get_commit_diff.return_value = mock_diff_content
        
        # Mock the parser
        with patch('bluestar.agents.nodes.commit_fetcher.CommitDataParser') as mock_parser_class:
            # Create a mock CommitData object
            mock_commit_data = Mock()
            mock_commit_data.sha = "a1b2c3d4e5f6789012345678901234567890abcd"
            mock_commit_data.message = "Improve editor performance with virtual scrolling"
            mock_commit_data.author = "Developer"
            mock_commit_data.files_changed = ["src/editor.ts"]
            mock_commit_data.total_additions = 25
            mock_commit_data.total_deletions = 10
            
            mock_parser_class.parse_commit_data.return_value = mock_commit_data
            
            # Execute the node
            result_state = commit_fetcher_node(state)
            
            # Verify results
            print(f"✅ Result: {result_state.commit_data is not None}")
            print(f"✅ No errors: {len(result_state.errors) == 0}")
            print(f"✅ Step completed: {'commit_fetching' in result_state.step_timestamps}")
            print(f"✅ Commit SHA: {result_state.commit_data.sha if result_state.commit_data else 'None'}")
            print(f"✅ Files changed: {len(result_state.commit_data.files_changed) if result_state.commit_data else 0}")
            
            return len(result_state.errors) == 0 and result_state.commit_data is not None


def test_configuration_error():
    """Test GitHub token configuration error handling."""
    print("\n🧪 Testing Configuration Error Handling")
    print("=" * 50)
    
    state = AgentState(
        repo_identifier="microsoft/vscode",
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
    )
    
    # Mock GitHubClient to raise ConfigurationError
    with patch('bluestar.agents.nodes.commit_fetcher.GitHubClient') as mock_client_class:
        mock_client_class.side_effect = ConfigurationError("GitHub token not configured. Set GITHUB_TOKEN environment variable.")
        
        # Execute the node
        result_state = commit_fetcher_node(state)
        
        # Verify error handling
        has_errors = len(result_state.errors) > 0
        user_friendly = "GitHub access not configured" in result_state.errors[0] if has_errors else False
        step_completed = "commit_fetching" in result_state.step_timestamps
        
        print(f"✅ Has errors: {has_errors}")
        print(f"✅ User-friendly message: {user_friendly}")
        print(f"✅ Step completed: {step_completed}")
        print(f"📝 Error message: {result_state.errors[0] if has_errors else 'None'}")
        
        return has_errors and user_friendly and step_completed


def test_repository_error():
    """Test repository not found error handling."""
    print("\n🧪 Testing Repository Error Handling")
    print("=" * 50)
    
    state = AgentState(
        repo_identifier="nonexistent/repository",
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
    )
    
    # Mock GitHubClient to raise RepositoryError
    with patch('bluestar.agents.nodes.commit_fetcher.GitHubClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_commit.side_effect = RepositoryError("Repository or commit not found: repos/nonexistent/repository/commits/abc123")
        
        # Execute the node
        result_state = commit_fetcher_node(state)
        
        # Verify error handling
        has_errors = len(result_state.errors) > 0
        contains_repo_name = "nonexistent/repository" in result_state.errors[0] if has_errors else False
        contains_commit_short = "a1b2c3d4" in result_state.errors[0] if has_errors else False
        
        print(f"✅ Has errors: {has_errors}")
        print(f"✅ Contains repo name: {contains_repo_name}")
        print(f"✅ Contains short commit: {contains_commit_short}")
        print(f"📝 Error message: {result_state.errors[0] if has_errors else 'None'}")
        
        return has_errors and contains_repo_name and contains_commit_short


def test_rate_limit_error():
    """Test GitHub API rate limit error handling."""
    print("\n🧪 Testing Rate Limit Error Handling")
    print("=" * 50)
    
    state = AgentState(
        repo_identifier="microsoft/vscode",
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
    )
    
    # Mock GitHubClient to raise rate limit error
    with patch('bluestar.agents.nodes.commit_fetcher.GitHubClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_commit.side_effect = LLMError("GitHub API rate limit exceeded. Reset in 1200 seconds.")
        
        # Execute the node
        result_state = commit_fetcher_node(state)
        
        # Verify error handling
        has_errors = len(result_state.errors) > 0
        rate_limit_message = "rate limit reached" in result_state.errors[0].lower() if has_errors else False
        helpful_guidance = "20 minutes" in result_state.errors[0] if has_errors else False
        
        print(f"✅ Has errors: {has_errors}")
        print(f"✅ Rate limit message: {rate_limit_message}")
        print(f"✅ Helpful guidance: {helpful_guidance}")
        print(f"📝 Error message: {result_state.errors[0] if has_errors else 'None'}")
        
        return has_errors and rate_limit_message and helpful_guidance


def test_invalid_commit_error():
    """Test invalid commit data error handling."""
    print("\n🧪 Testing Invalid Commit Error Handling")
    print("=" * 50)
    
    state = AgentState(
        repo_identifier="microsoft/vscode", 
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd"
    )
    
    # Mock GitHubClient success but CommitDataParser failure
    with patch('bluestar.agents.nodes.commit_fetcher.GitHubClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_commit.return_value = {"sha": "abc123"}
        mock_client.get_commit_diff.return_value = "diff content"
        
        with patch('bluestar.agents.nodes.commit_fetcher.CommitDataParser') as mock_parser_class:
            mock_parser_class.parse_commit_data.side_effect = InvalidCommitError("a1b2c3d4", "microsoft/vscode")
            
            # Execute the node
            result_state = commit_fetcher_node(state)
            
            # Verify error handling
            has_errors = len(result_state.errors) > 0
            invalid_commit_message = "invalid or incomplete" in result_state.errors[0] if has_errors else False
            
            print(f"✅ Has errors: {has_errors}")
            print(f"✅ Invalid commit message: {invalid_commit_message}")
            print(f"📝 Error message: {result_state.errors[0] if has_errors else 'None'}")
            
            return has_errors and invalid_commit_message


def test_error_handler_utility():
    """Test the CommitFetcherErrorHandler utility directly."""
    print("\n🧪 Testing Error Handler Utility")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Configuration Error",
            "exception": ConfigurationError("GitHub token not configured. Set GITHUB_TOKEN environment variable."),
            "expected_keywords": ["GitHub access not configured", "GITHUB_TOKEN", "github.com/settings/tokens"]
        },
        {
            "name": "Repository Error",
            "exception": RepositoryError("Repository not found"),
            "expected_keywords": ["test/repo", "a1b2c3d4", "verify"]
        },
        {
            "name": "Rate Limit Error",
            "exception": LLMError("GitHub API rate limit exceeded"),
            "expected_keywords": ["rate limit reached", "20 minutes", "GitHub Pro"]
        },
        {
            "name": "Timeout Error",
            "exception": LLMError("GitHub API request timed out"),
            "expected_keywords": ["timed out", "internet connection", "GitHub may be experiencing"]
        },
        {
            "name": "Permission Error",
            "exception": LLMError("GitHub API access forbidden"),
            "expected_keywords": ["access denied", "'repo' scope", "'public_repo' scope"]
        }
    ]
    
    repo = "test/repo"
    commit_sha = "a1b2c3d4e5f6789012345678901234567890abcd"
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        # Get user message
        user_message = CommitFetcherErrorHandler.get_user_message(
            test_case["exception"], repo, commit_sha
        )
        
        # Check for expected keywords
        keywords_found = []
        for keyword in test_case["expected_keywords"]:
            if keyword.lower() in user_message.lower():
                keywords_found.append(keyword)
        
        test_passed = len(keywords_found) == len(test_case["expected_keywords"])
        all_passed = all_passed and test_passed
        
        print(f"   {'✅' if test_passed else '❌'} Keywords found: {len(keywords_found)}/{len(test_case['expected_keywords'])}")
        print(f"   📝 Message: {user_message[:100]}...")
        
        if not test_passed:
            missing = set(test_case["expected_keywords"]) - set(keywords_found)
            print(f"   ❌ Missing keywords: {missing}")
    
    return all_passed


def main():
    """Run all CommitFetcher tests."""
    print("🚀 CommitFetcher Node Test Suite")
    print("=" * 60)
    
    tests = [
        ("Successful Commit Fetching", test_successful_commit_fetching),
        ("Configuration Error", test_configuration_error),
        ("Repository Error", test_repository_error),
        ("Rate Limit Error", test_rate_limit_error),
        ("Invalid Commit Error", test_invalid_commit_error),
        ("Error Handler Utility", test_error_handler_utility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {test_name}")
        if error:
            print(f"            Error: {error}")
        if success:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CommitFetcher is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the error details above.")


if __name__ == "__main__":
    main() 