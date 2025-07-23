#!/usr/bin/env python3
"""
Real GitHub API Test Script

Tests GitHubClient with actual GitHub API using real token and repository.
Repository: https://github.com/domini04/bluestar
Commit: e64997b24625a4e90c39d019d4fd25a37a4b3185
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bluestar.tools.github_client import GitHubClient
from bluestar.core.exceptions import ConfigurationError, RepositoryError, LLMError


def test_real_github_api():
    """Test GitHubClient with real GitHub API."""
    
    print("🔍 Testing GitHubClient with Real GitHub API")
    print("=" * 50)
    
    try:
        # Initialize client (will use GITHUB_TOKEN from .env)
        print("1. Initializing GitHubClient...")
        client = GitHubClient()
        print(f"   ✅ Client initialized with token: {client.token[:10]}...")
        
        # Test repository parsing
        print("\n2. Testing repository parsing...")
        repo_url = "https://github.com/domini04/bluestar"
        owner, repo = GitHubClient.parse_repo_identifier(repo_url)
        print(f"   ✅ Parsed '{repo_url}' → owner='{owner}', repo='{repo}'")
        
        # Test commit retrieval
        print("\n3. Fetching commit data...")
        commit_sha = "e64997b24625a4e90c39d019d4fd25a37a4b3185"
        commit_data = client.get_commit(owner, repo, commit_sha)
        
        print(f"   ✅ Successfully fetched commit: {commit_sha[:8]}...")
        print(f"   📝 Commit message: {commit_data['commit']['message']}")
        print(f"   👤 Author: {commit_data['commit']['author']['name']}")
        print(f"   📅 Date: {commit_data['commit']['author']['date']}")
        print(f"   📁 Files changed: {len(commit_data.get('files', []))}")
        
        # Show file changes
        if 'files' in commit_data:
            print(f"   📋 Changed files:")
            for file_info in commit_data['files'][:5]:  # Show first 5 files
                status = file_info.get('status', 'unknown')
                filename = file_info.get('filename', 'unknown')
                additions = file_info.get('additions', 0)
                deletions = file_info.get('deletions', 0)
                print(f"      • {filename} ({status}) +{additions}/-{deletions}")
            
            if len(commit_data['files']) > 5:
                print(f"      ... and {len(commit_data['files']) - 5} more files")
        
        # Test diff retrieval
        print("\n4. Fetching commit diff...")
        diff_content = client.get_commit_diff(owner, repo, commit_sha)
        
        print(f"   ✅ Successfully fetched diff")
        print(f"   📏 Diff size: {len(diff_content)} characters")
        
        # Show first few lines of diff
        diff_lines = diff_content.split('\n')[:10]
        print(f"   📄 First 10 lines of diff:")
        for line in diff_lines:
            print(f"      {line}")
        
        if len(diff_content.split('\n')) > 10:
            print(f"      ... and {len(diff_content.split('\n')) - 10} more lines")
        
        # Show rate limit info
        print("\n5. Rate limit information...")
        if client.rate_limit_info:
            rate_limit = client.rate_limit_info
            print(f"   📊 Rate limit: {rate_limit.remaining}/{rate_limit.limit} requests remaining")
            print(f"   ⏰ Resets at: {rate_limit.reset_time}")
            print(f"   🔄 Reset in: {rate_limit.reset_in_seconds} seconds")
        else:
            print("   ❓ No rate limit info available")
        
        print("\n🎉 All tests passed! GitHubClient works correctly with real GitHub API.")
        
    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("💡 Make sure GITHUB_TOKEN is set in your .env file")
        return False
        
    except RepositoryError as e:
        print(f"\n❌ Repository Error: {e}")
        print("💡 Check that the repository and commit exist and are accessible")
        return False
        
    except LLMError as e:
        print(f"\n❌ API Error: {e}")
        print("💡 This might be a GitHub API issue or network problem")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        return False
    
    return True


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded environment variables from .env file")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment variables")
    
    # Check if token is available
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not found in environment variables")
        print("💡 Make sure to set GITHUB_TOKEN in your .env file")
        sys.exit(1)
    
    # Run the test
    success = test_real_github_api()
    sys.exit(0 if success else 1) 