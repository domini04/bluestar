#!/usr/bin/env python3
"""
Test script for Input Validator Node

Tests various scenarios including valid inputs, invalid inputs, 
edge cases, and error handling.
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bluestar.agents.state import AgentState
from bluestar.agents.nodes.input_validator import input_validator_node, validate_repository, validate_commit_sha


def test_repository_validation():
    """Test repository validation function directly."""
    print("🧪 Testing Repository Validation")
    print("=" * 40)
    
    test_cases = [
        # (input, expected_valid, expected_normalized, description)
        ("microsoft/vscode", True, "microsoft/vscode", "Simple owner/repo format"),
        ("https://github.com/microsoft/vscode", True, "microsoft/vscode", "GitHub URL format"),
        ("https://github.com/microsoft/vscode.git", True, "microsoft/vscode", "GitHub URL with .git"),
        ("", False, "", "Empty string"),
        ("   ", False, "", "Whitespace only"),
        ("invalid", False, "", "Single word"),
        ("too/many/parts", False, "", "Too many parts"),
        ("user/repo-name", True, "user/repo-name", "Repo with dash"),
        ("user123/repo_name", True, "user123/repo_name", "User with numbers, repo with underscore"),
    ]
    
    for input_val, expected_valid, expected_normalized, description in test_cases:
        is_valid, normalized, error = validate_repository(input_val)
        
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"   {status} {description}")
        print(f"      Input: '{input_val}'")
        print(f"      Expected: valid={expected_valid}, normalized='{expected_normalized}'")
        print(f"      Got: valid={is_valid}, normalized='{normalized}'")
        
        if not is_valid and error:
            print(f"      Error: {error}")
        print()


def test_commit_sha_validation():
    """Test commit SHA validation function directly."""
    print("🧪 Testing Commit SHA Validation")
    print("=" * 40)
    
    test_cases = [
        # (input, expected_valid, expected_cleaned, description)
        ("1234567890abcdef1234567890abcdef12345678", True, "1234567890abcdef1234567890abcdef12345678", "Valid 40-char SHA"),
        ("ABCDEF1234567890abcdef1234567890ABCDEF12", True, "abcdef1234567890abcdef1234567890abcdef12", "Mixed case SHA (should lowercase)"),
        ("  1234567890abcdef1234567890abcdef12345678  ", True, "1234567890abcdef1234567890abcdef12345678", "SHA with whitespace"),
        ("", False, "", "Empty string"),
        ("   ", False, "", "Whitespace only"),
        ("short", False, "", "Too short"),
        ("1234567890abcdef1234567890abcdef123456789", False, "", "39 characters (too short)"),
        ("1234567890abcdef1234567890abcdef123456789a", True, "1234567890abcdef1234567890abcdef123456789a", "Exactly 40 characters"),
        ("1234567890abcdef1234567890abcdef123456789ab", False, "", "41 characters (too long)"),
        ("1234567890abcdef1234567890abcdef1234567g", False, "", "Invalid character 'g'"),
        ("1234567890abcdef1234567890abcdef1234567!", False, "", "Invalid character '!'"),
    ]
    
    for input_val, expected_valid, expected_cleaned, description in test_cases:
        is_valid, cleaned, error = validate_commit_sha(input_val)
        
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"   {status} {description}")
        print(f"      Input: '{input_val}'")
        print(f"      Expected: valid={expected_valid}, cleaned='{expected_cleaned}'")
        print(f"      Got: valid={is_valid}, cleaned='{cleaned}'")
        
        if not is_valid and error:
            print(f"      Error: {error}")
        print()


def test_input_validator_node():
    """Test the complete Input Validator node."""
    print("🧪 Testing Input Validator Node")
    print("=" * 40)
    
    test_cases = [
        {
            "name": "Valid inputs",
            "repo": "microsoft/vscode",
            "sha": "1234567890abcdef1234567890abcdef12345678",
            "instructions": "Make it beginner-friendly",
            "should_pass": True
        },
        {
            "name": "Valid inputs without instructions",
            "repo": "user/repo",
            "sha": "abcdef1234567890abcdef1234567890abcdef12",
            "instructions": None,
            "should_pass": True
        },
        {
            "name": "GitHub URL format",
            "repo": "https://github.com/microsoft/vscode",
            "sha": "1234567890abcdef1234567890abcdef12345678",
            "instructions": None,
            "should_pass": True
        },
        {
            "name": "Invalid repository",
            "repo": "invalid",
            "sha": "1234567890abcdef1234567890abcdef12345678",
            "instructions": None,
            "should_pass": False
        },
        {
            "name": "Invalid commit SHA",
            "repo": "microsoft/vscode",
            "sha": "short",
            "instructions": None,
            "should_pass": False
        },
        {
            "name": "Both invalid",
            "repo": "invalid",
            "sha": "short",
            "instructions": None,
            "should_pass": False
        },
        {
            "name": "Empty inputs",
            "repo": "",
            "sha": "",
            "instructions": None,
            "should_pass": False
        },
        {
            "name": "Whitespace inputs",
            "repo": "   ",
            "sha": "   ",
            "instructions": "   ",
            "should_pass": False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test Case: {test_case['name']}")
        print("-" * 30)
        
        # Create initial state
        state = AgentState(
            repo_identifier=test_case["repo"],
            commit_sha=test_case["sha"],
            user_instructions=test_case["instructions"]
        )
        
        # Run the validator
        result_state = input_validator_node(state)
        
        # Check results
        has_errors = result_state.has_errors()
        passed = not has_errors if test_case["should_pass"] else has_errors
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}")
        
        if test_case["should_pass"]:
            print(f"   Expected: No errors")
            print(f"   Got: {len(result_state.errors)} errors")
            if result_state.errors:
                for error in result_state.errors:
                    print(f"      - {error}")
        else:
            print(f"   Expected: Errors present")
            print(f"   Got: {len(result_state.errors)} errors")
            if result_state.errors:
                for error in result_state.errors:
                    print(f"      - {error}")
        
        # Show final state
        print(f"   Final repo: '{result_state.repo_identifier}'")
        print(f"   Final SHA: '{result_state.commit_sha}'")
        print(f"   Instructions: '{result_state.user_instructions}'")
        print(f"   Current step: '{result_state.current_step}'")


def test_state_mutations():
    """Test that the validator properly mutates the state."""
    print("\n🧪 Testing State Mutations")
    print("=" * 40)
    
    # Test normalization
    state = AgentState(
        repo_identifier="https://github.com/microsoft/vscode.git",
        commit_sha="  ABCDEF1234567890abcdef1234567890ABCDEF12  ",
        user_instructions="  Make it technical  "
    )
    
    print("Before validation:")
    print(f"   Repo: '{state.repo_identifier}'")
    print(f"   SHA: '{state.commit_sha}'")
    print(f"   Instructions: '{state.user_instructions}'")
    print(f"   Current step: '{state.current_step}'")
    
    result_state = input_validator_node(state)
    
    print("\nAfter validation:")
    print(f"   Repo: '{result_state.repo_identifier}' (normalized)")
    print(f"   SHA: '{result_state.commit_sha}' (cleaned & lowercased)")
    print(f"   Instructions: '{result_state.user_instructions}' (unchanged)")
    print(f"   Current step: '{result_state.current_step}' (should be 'input_validation')")
    
    # Verify mutations
    expected_repo = "microsoft/vscode"
    expected_sha = "abcdef1234567890abcdef1234567890abcdef12"
    expected_step = "input_validation"
    
    mutations_correct = (
        result_state.repo_identifier == expected_repo and
        result_state.commit_sha == expected_sha and
        result_state.current_step == expected_step and
        not result_state.has_errors()
    )
    
    status = "✅ PASSED" if mutations_correct else "❌ FAILED"
    print(f"\n   State mutations: {status}")


def main():
    """Run all tests."""
    print("🌟 BlueStar Input Validator Tests")
    print("=" * 50)
    
    try:
        test_repository_validation()
        test_commit_sha_validation()
        test_input_validator_node()
        test_state_mutations()
        
        print("\n🎉 All tests completed!")
        print("Review the output above to see individual test results.")
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 