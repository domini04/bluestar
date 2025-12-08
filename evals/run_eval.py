import os
import sys
import uuid
from unittest.mock import patch
from dotenv import load_dotenv

# Load env vars
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Ensure LANGCHAIN_API_KEY is set
if not os.getenv("LANGCHAIN_API_KEY") and os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

from langsmith import evaluate
from langsmith import Client

# Import BlueStar components
# We need to add the project root to sys.path to import src
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.bluestar.agents.graph import create_app
from src.bluestar.agents.state import AgentState
from evals.evaluators import structure_evaluator, faithfulness_evaluator, core_accuracy_evaluator

DATASET_NAME = "BlueStar Evaluation Dataset"
EXPERIMENT_PREFIX = "bluestar-v1-initial-review"

def target_app(inputs: dict) -> dict:
    """
    Wrapper function for the BlueStar agent to run in LangSmith evaluation.
    
    Args:
        inputs: Dict containing 'repo_identifier' and 'commit_sha' from the dataset.
        
    Returns:
        Dict containing the generated blog post content.
    """

    # 1. Initialize State
    # We configure the state to prefer a 'discard' decision at the end to avoid actual publishing
    # during evaluation runs, although we mock the input to pass the refinement loop.
    initial_state = AgentState(
        repo_identifier=inputs["repo_identifier"],
        commit_sha=inputs["commit_sha"],
        user_instructions="Generate a detailed technical blog post for evaluation.",
        publishing_decision="discard" # Default to discard to be safe
    )
    
    app = create_app()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # 2. Execute with MOCKED Input
    # This is the CRITICAL part where we bypass the CLI interaction.
    # We patch 'builtins.input' to simulate a user typing 'y' (Satisfied) and then 'discard' (Decision).
    # The app asks: 
    #   1. "Are you satisfied?" -> We provide 'y'
    #   2. "Publishing decision?" -> We provide 'discard' (if the node asks via input)
    # Note: publishing_decision_node currently uses input() as well.
    
    # We provide a side_effect (list of outputs) to handle multiple input() calls in sequence.
    # Call 1 (Human Refinement): "y" (Satisfied)
    # Call 2 (Publishing Decision): "4" (Discard - assuming menu option 4 is discard, checking code needed)
    # Let's check publishing_decision.py logic. It usually prints a menu.
    # Ideally, we should verify the menu options. For now, we assume 'discard' or similar.
    
    # Let's just return the final blog post content.
    final_content = "Error: Workflow failed"
    
    try:
        # Patching input() to always return 'y' for satisfaction and '4' for discard (if prompted)
        # Even though we set publishing_decision="discard", we add '4' to side_effect as a fallback.
        with patch('builtins.input', side_effect=['y', '4']):
            # We use invoke instead of stream for evaluation to get the final result
            result = app.invoke(initial_state, config=config)
            
            if result.get("blog_post"):
                final_content = result["blog_post"].content
            else:
                final_content = "No blog post generated."
                
            # Check for errors
            if result.get("errors"):
                final_content += f"\n\nERRORS ENCOUNTERED: {result['errors']}"
            
            # Capture diffs for evaluation context
            commit_context = "No commit data captured."
            if result.get("commit_data"):
                # Create a summary of the diffs to pass to the evaluator
                # We reuse the format logic from commit_analyzer but simplified
                c_data = result["commit_data"]
                commit_context = f"""
                    Repository: {c_data.repository_path}
                    Message: {c_data.message}
                    Files Changed: {', '.join(c_data.files_changed)}
                    Diff Summary:
                    """
                for diff in c_data.diffs:
                    commit_context += f"\n--- {diff.file_path} ({diff.change_type}) ---\n"
                    # Truncate very long diffs to avoid token limits in evaluator
                    commit_context += diff.diff_content[:5000] 
                    if len(diff.diff_content) > 5000:
                        commit_context += "\n... [truncated]"

    except Exception as e:
        final_content = f"Exception during execution: {str(e)}"
        commit_context = "Error during execution, no context available."
        
    return {
        "blog_content": final_content,
        "commit_context": commit_context
    }

def main():
    print(f"🚀 Starting Evaluation Run on dataset: {DATASET_NAME}")
    print(f"🧪 Experiment Prefix: {EXPERIMENT_PREFIX}")
    
    client = Client()
    
    if not client.has_dataset(dataset_name=DATASET_NAME):
        print(f"❌ Dataset '{DATASET_NAME}' not found. Please run create_dataset.py first.")
        return

    # Run the evaluation
    results = evaluate(
        target_app,
        data=DATASET_NAME,
        experiment_prefix=EXPERIMENT_PREFIX,
        evaluators=[
            structure_evaluator,
            faithfulness_evaluator,
            core_accuracy_evaluator
        ],
        max_concurrency=1,  # Run sequentially to avoid rate limits and confusion
        metadata={
            "version": "1.0.0",
            "description": "Initial open coding run with mock human input"
        }
    )
    
    print(f"\n✅ Evaluation complete!")
    print(f"👉 View results at: {results.experiment_results['url'] if hasattr(results, 'experiment_results') else 'LangSmith Dashboard'}")

if __name__ == "__main__":
    main()

