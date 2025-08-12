"""
BlueStar Main Entry Point

Handles different execution modes:
- CLI mode for development and testing
"""

import sys
import argparse
import uuid
from typing import Optional

from .cli import run_cli
from .config import config


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="bluestar",
        description="BlueStar - AI-Powered Developer Blog Generation Agent"
    )
    
    parser.add_argument(
        "--mode",
        choices=["cli", "mcp"],
        default="cli",
        help="Execution mode (default: cli)"
    )
    
    # CLI-specific arguments
    parser.add_argument(
        "--repo",
        help="Repository identifier (owner/repo or GitHub URL)"
    )
    
    parser.add_argument(
        "--commit",
        help="Commit SHA hash"
    )
    
    parser.add_argument(
        "--instructions",
        help="Additional instructions for blog generation"
    )

    # LLM selection overrides
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "claude", "gemini", "grok"],
        help="Override LLM provider (allowed: openai, claude, gemini, grok)"
    )
    parser.add_argument(
        "--llm-model",
        help="Override LLM model (free-form, e.g., gpt-5, claude-4-opus, gemini-2.5-pro)"
    )
    
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Check configuration and exit"
    )
    
    return parser


def check_configuration() -> bool:
    """
    Check if BlueStar is properly configured.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    print("🔧 Checking BlueStar Configuration...")
    print("=" * 40)
    
    # Check LLM configuration
    print(f"LLM Provider: {config.llm_provider}")
    print(f"LLM Model: {config.llm_model}")
    print(f"LLM API Key: {'✅ Configured' if config.llm_api_key else '❌ Missing'}")
    
    # Check GitHub configuration
    import os
    github_token = os.getenv("GITHUB_TOKEN")
    print(f"GitHub Token: {'✅ Configured' if github_token else '❌ Missing'}")
    
    # Validate configuration
    is_valid = config.validate()
    
    print("=" * 40)
    if is_valid:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors!")
        print("\nPlease check your .env file and ensure all required API keys are set.")
    
    return is_valid


def run_cli_with_args(repo: str, commit: str, instructions: Optional[str] = None) -> None:
    """
    Run CLI mode with command line arguments.
    
    Args:
        repo: Repository identifier
        commit: Commit SHA
        instructions: Optional user instructions
    """
    from .agents.state import AgentState
    from .agents.graph import create_app
    from .cli import display_result
    
    print("🌟 BlueStar - AI Developer Blog Generator")
    print("=" * 50)
    print(f"📁 Repository: {repo}")
    print(f"🔗 Commit: {commit}")
    if instructions:
        print(f"📝 Instructions: {instructions}")
    print()

    try:
        # Create initial state with structured data
        initial_state = AgentState(
            repo_identifier=repo,
            commit_sha=commit,
            user_instructions=instructions
        )
        
        # Create and execute compiled app
        app = create_app()
        
        # Each run needs a unique thread_id for the checkpointer
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        print(f"🚀 Starting workflow (Thread ID: {thread_id})...")
        final_state = None
        # Use stream to get progress and final state
        for step in app.stream(initial_state, config=config, stream_mode="values"):
            step_name = list(step.keys())[0]
            print(f"  - ✅ Completed: {step_name}")
            final_state = step

        if not final_state:
            raise Exception("Workflow did not produce any output.")

        # The final state is the value of the last step
        result_state = list(final_state.values())[0]
        
        # Display results
        display_result(result_state)
        
    except Exception as e:
        print(f"❌ Workflow Execution Error: {e}")
        print("\nThis might be due to a configuration issue with the checkpointer or an error within a graph node.")
        print("Ensure your graph is correctly compiled and all required configurations (like thread_id) are provided.")
        sys.exit(1)


def main() -> None:
    """Main entry point for BlueStar application."""
    parser = create_parser()
    args = parser.parse_args()

    # Apply LLM overrides (CLI > env > defaults)
    try:
        config.apply_overrides(
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
        )
    except Exception as e:
        print(f"❌ Invalid LLM selection: {e}")
        sys.exit(1)
    
    # Configuration check mode
    if args.config_check:
        is_valid = check_configuration()
        sys.exit(0 if is_valid else 1)
    
    # Validate configuration before running
    if not check_configuration():
        print("\n❌ Please fix configuration issues before running BlueStar.")
        sys.exit(1)
    
    # CLI mode
    if args.mode == "cli":
        if args.repo and args.commit:
            # Run with command line arguments
            run_cli_with_args(args.repo, args.commit, args.instructions)
        else:
            # Run interactive CLI
            run_cli()
    
    # MCP mode (future implementation)
    elif args.mode == "mcp":
        print("🚧 MCP mode is not yet implemented.")
        print("Use --mode=cli for development and testing.")
        sys.exit(1)


if __name__ == "__main__":
    main() 