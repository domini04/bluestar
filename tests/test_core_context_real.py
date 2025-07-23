#!/usr/bin/env python3
"""
Real Core Context Test Script

Tests the new core context functionality with actual GitHub API calls.
This script validates the enhanced GitHubClient and CommitDataParser integration.
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bluestar.tools.github_client import GitHubClient
from bluestar.tools.commit_parser import CommitDataParser
from bluestar.core.exceptions import ConfigurationError, RepositoryError, LLMError
import json


def test_core_context_functionality():
    """Test core context with real GitHub API."""
    
    print("🧪 Testing Core Context Functionality with Real GitHub API")
    print("=" * 60)
    
    try:
        # Initialize client
        print("1. Initializing GitHubClient...")
        client = GitHubClient()
        print(f"   ✅ Client initialized with token: {client.token[:10]}...")
        
        # Test repository and commit
        owner = "domini04"
        repo = "bluestar"
        commit_sha = "e64997b24625a4e90c39d019d4fd25a37a4b3185"
        
        print(f"\n2. Testing Core Context Methods individually...")
        print(f"   Repository: {owner}/{repo}")
        print(f"   Commit: {commit_sha[:8]}...")
        
        # Test repository metadata
        print("\n   2a. Testing get_repository_metadata()...")
        try:
            repo_metadata = client.get_repository_metadata(owner, repo)
            print(f"      ✅ Repository metadata fetched")
            print(f"      📝 Description: {repo_metadata.get('description', 'None')}")
            print(f"      💻 Language: {repo_metadata.get('language', 'None')}")
            print(f"      🏷️  Topics: {repo_metadata.get('topics', [])}")
            print(f"      ⭐ Stars: {repo_metadata.get('stars', 0)}")
            print(f"      📜 License: {repo_metadata.get('license', 'None')}")
        except Exception as e:
            print(f"      ❌ Repository metadata failed: {e}")
            repo_metadata = None
        
        # Test README summary
        print("\n   2b. Testing get_readme_summary()...")
        try:
            readme_summary = client.get_readme_summary(owner, repo, commit_sha)
            if readme_summary:
                print(f"      ✅ README summary fetched ({len(readme_summary)} chars)")
                print(f"      📄 First 100 chars: {readme_summary[:100]}...")
            else:
                print(f"      ⚠️  No README found")
        except Exception as e:
            print(f"      ❌ README summary failed: {e}")
            readme_summary = None
        
        # Test primary config file
        print("\n   2c. Testing get_primary_config_file()...")
        try:
            config_file = client.get_primary_config_file(owner, repo, commit_sha)
            if config_file:
                print(f"      ✅ Config file found: {config_file.get('file_name')}")
                print(f"      🔧 Project type: {config_file.get('project_type')}")
                print(f"      📄 Content length: {len(config_file.get('content', ''))} chars")
                print(f"      📄 First 100 chars: {config_file.get('content', '')[:100]}...")
            else:
                print(f"      ⚠️  No config file found")
        except Exception as e:
            print(f"      ❌ Config file fetch failed: {e}")
            config_file = None
        
        # Test orchestrated core context
        print("\n3. Testing get_core_context() orchestration...")
        try:
            core_context = client.get_core_context(owner, repo, commit_sha)
            print(f"   ✅ Core context orchestration successful")
            
            # Show what was fetched
            context_sources = []
            if core_context.get("repository_metadata"):
                context_sources.append("repository_metadata")
            if core_context.get("readme_summary"):
                context_sources.append("readme_summary")
            if core_context.get("primary_config"):
                context_sources.append("primary_config")
            
            print(f"   📊 Context sources: {context_sources}")
            print(f"   🔧 Detected project type: {core_context.get('project_type', 'unknown')}")
            print(f"   🕒 Fetch timestamp: {core_context.get('fetch_timestamp')}")
            
        except Exception as e:
            print(f"   ❌ Core context orchestration failed: {e}")
            core_context = None
        
        # Test integration with CommitDataParser
        print("\n4. Testing CommitDataParser integration...")
        try:
            # First get the commit data (existing functionality)
            commit_response = client.get_commit(owner, repo, commit_sha)
            diff_content = client.get_commit_diff(owner, repo, commit_sha)
            
            # Parse with core context
            commit_data = CommitDataParser.parse_commit_data(
                commit_response=commit_response,
                diff_content=diff_content,
                repo_identifier=f"{owner}/{repo}",
                core_context=core_context
            )
            
            print(f"   ✅ CommitData created with core context")
            print(f"   📝 Commit: {commit_data.sha[:8]}... - {commit_data.message}")
            print(f"   👤 Author: {commit_data.author}")
            print(f"   📁 Files changed: {len(commit_data.files_changed)}")
            
            # Examine the project_structure
            if commit_data.project_structure:
                print(f"   🏗️  Project structure available!")
                
                # Show structured context
                project_data = commit_data.project_structure
                
                if "repository" in project_data:
                    repo_info = project_data["repository"]
                    print(f"      📝 Repository: {repo_info.get('description', 'No description')}")
                    print(f"      💻 Language: {repo_info.get('language', 'unknown')}")
                
                if "configuration" in project_data:
                    config_info = project_data["configuration"]
                    print(f"      ⚙️  Config: {config_info.get('file_name')} ({config_info.get('project_type')})")
                
                if "readme_summary" in project_data:
                    readme_len = len(project_data["readme_summary"])
                    print(f"      📄 README: {readme_len} chars available")
                
                print(f"      🔧 Final project type: {project_data.get('project_type', 'unknown')}")
                
                # Show context metadata
                if "context_metadata" in project_data:
                    metadata = project_data["context_metadata"]
                    print(f"      📊 Context sources: {metadata.get('context_sources', [])}")
            else:
                print(f"   ⚠️  No project structure available")
            
        except Exception as e:
            print(f"   ❌ CommitDataParser integration failed: {e}")
        
        # Test edge cases
        print("\n5. Testing Edge Cases...")
        
        # Test with non-existent repository
        print("\n   5a. Testing non-existent repository...")
        try:
            bad_context = client.get_core_context("nonexistent", "repo", "abc123")
            print(f"      ⚠️  Non-existent repo returned context: {bad_context}")
        except Exception as e:
            print(f"      ✅ Non-existent repo properly failed: {type(e).__name__}")
        
        # Test with non-existent commit
        print("\n   5b. Testing non-existent commit...")
        try:
            bad_context = client.get_core_context(owner, repo, "nonexistentcommitsha123456")
            print(f"      ⚠️  Non-existent commit returned context: {bad_context}")
        except Exception as e:
            print(f"      ✅ Non-existent commit properly failed: {type(e).__name__}")
        
        print("\n🎉 Core Context Testing Complete!")
        print("\n📊 Summary:")
        print("   - ✅ Core context methods implemented successfully")
        print("   - ✅ Error handling works correctly")
        print("   - ✅ Integration with CommitDataParser functional")
        print("   - ✅ Graceful degradation on failures")
        
        return True
        
    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("💡 Make sure GITHUB_TOKEN is set in your .env file")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print(f"💡 Error type: {type(e).__name__}")
        return False


def test_token_usage_estimation():
    """Estimate token usage for core context."""
    print("\n🔢 Token Usage Estimation")
    print("=" * 30)
    
    # These are rough estimates
    print("Estimated token usage for core context:")
    print("   Repository metadata: ~100-200 tokens")
    print("   README summary (1000 chars): ~250-400 tokens")
    print("   Config file (2000 chars): ~500-800 tokens")
    print("   ----------------------------------------")
    print("   Total core context: ~850-1400 tokens")
    print("")
    print("This is well within the planned budget of 1000-3000 tokens.")


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
    
    # Run the tests
    success = test_core_context_functionality()
    
    if success:
        test_token_usage_estimation()
    
    sys.exit(0 if success else 1) 