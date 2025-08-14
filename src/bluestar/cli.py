"""
BlueStar CLI Interface

Simple command-line interface for development and testing.
Provides user input collection and workflow execution.
"""

import sys
from typing import Optional, Tuple

from .config import config as settings

from .agents.state import AgentState
from .agents.graph import create_workflow
from .core.exceptions import BlueStarError


def parse_cli_input(raw_input: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse CLI text input into structured components.
    
    Expected format: "repository commit_sha [| instructions]"
    
    Args:
        raw_input: Raw CLI input string
        
    Returns:
        Tuple of (repo_identifier, commit_sha, instructions)
    """
    if not raw_input or not raw_input.strip():
        return "", "", None
    
    # Split on | for instructions
    if "|" in raw_input:
        main_part, instructions_part = raw_input.split("|", 1)
        instructions = instructions_part.strip() if instructions_part.strip() else None
    else:
        main_part = raw_input
        instructions = None
    
    # Split main part into repository and commit
    parts = main_part.strip().split()
    
    if len(parts) < 2:
        # Not enough parts
        repo_part = parts[0] if parts else ""
        commit_part = ""
    elif len(parts) == 2:
        # Perfect: repo commit
        repo_part, commit_part = parts
    else:
        # Too many parts - assume first is repo, second is commit, ignore rest
        repo_part, commit_part = parts[0], parts[1]
    
    return repo_part.strip(), commit_part.strip(), instructions


def collect_user_input() -> AgentState:
    """
    Collect user input for repository and commit information.
    
    Returns:
        AgentState with structured input data
    """
    print("🌟 BlueStar - AI Developer Blog Generator")
    print("=" * 50)
    print()
    
    # Collect repository information
    print("📁 Repository Information:")
    repo_input = input("   Repository (owner/repo or GitHub URL): ").strip()
    
    if not repo_input:
        print("❌ Repository is required!")
        return collect_user_input()  # Retry
    
    # Collect commit SHA
    print("\n🔗 Commit Information:")
    commit_sha = input("   Commit SHA (40 characters): ").strip()
    
    if not commit_sha:
        print("❌ Commit SHA is required!")
        return collect_user_input()  # Retry
    
    # Optional user instructions
    print("\n📝 Additional Instructions (optional):")
    print("   Examples: 'Focus on performance improvements', 'Make it beginner-friendly'")
    instructions = input("   Instructions: ").strip()
    
    # Optional: preselect publishing decision via env var BLUESTAR_PUBLISH (ghost|notion|local|discard)
    preselect_publish = (settings and settings.__dict__.get("preselect_publish")) or None
    # Create structured AgentState
    return AgentState(
        repo_identifier=repo_input,
        commit_sha=commit_sha,
        user_instructions=instructions if instructions else None,
        publishing_decision=preselect_publish if preselect_publish in {"ghost", "notion", "local", "discard"} else None,
    )


def display_result(state: AgentState) -> None:
    """
    Display workflow results to the user.
    
    Args:
        state: Completed workflow state
    """
    print("\n" + "=" * 60)
    print("🎉 WORKFLOW COMPLETE")
    print("=" * 60)
    
    # Check if the final state is a valid AgentState object.
    # If not, the workflow likely terminated early.
    if not isinstance(state, AgentState):
        print("\nℹ️  Workflow was halted before completion.")
        print("This may be due to an error or a deliberate stop condition in the graph.")
        # Optionally print the raw state for debugging
        # print(f"\nDEBUG: Final state was: {state}")
        return

    # Display basic information
    print(f"📁 Repository: {state.repo_identifier}")
    print(f"🔗 Commit SHA: {state.commit_sha}")
    print(f"⏱️  Processing Time: {len(state.step_timestamps)} steps completed")
    
    # Display errors if any
    if state.errors:
        print("\n❌ ERRORS ENCOUNTERED:")
        for error in state.errors:
            print(f"   • {error}")
        return
    
    # Display generated blog post
    if state.blog_post:
        print("\n📝 GENERATED BLOG POST:")
        print("-" * 40)
        print(f"Title: {state.blog_post.title}")
        print(f"Excerpt: {state.blog_post.excerpt}")
        print("\nContent Preview:")
        # Show first 300 characters of content
        content_preview = state.blog_post.html[:300]
        if len(state.blog_post.html) > 300:
            content_preview += "..."
        print(content_preview)
        print("-" * 40)
    
    # Display workflow metadata
    if state.step_timestamps:
        print("\n📊 WORKFLOW STEPS:")
        for step, timestamp in state.step_timestamps.items():
            print(f"   ✅ {step}: {timestamp.strftime('%H:%M:%S')}")


def run_cli() -> None:
    """
    Main CLI execution function.
    Handles input collection, workflow execution, and result display.
    """
    try:
        # Collect user input
        initial_state = collect_user_input()
        
        print(f"\n🔄 Starting BlueStar workflow...")
        print(f"Input: {initial_state.repo_identifier} {initial_state.commit_sha}")
        if initial_state.user_instructions:
            print(f"Instructions: {initial_state.user_instructions}")
        print()
        
        # Create and execute workflow
        workflow = create_workflow()
        result_state = workflow.invoke(initial_state)
        
        # Display results
        display_result(result_state)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Workflow interrupted by user")
        sys.exit(0)
        
    except BlueStarError as e:
        print(f"\n❌ BlueStar Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Unexpected Error: {e}")
        print("This might be a bug - please report it!")
        sys.exit(1)


def main() -> None:
    """Entry point for CLI application."""
    run_cli()


if __name__ == "__main__":
    main() 