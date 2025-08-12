"""
BlueStar LangGraph Workflow

Main workflow orchestration for AI-powered blog generation.
Defines the flow between nodes without implementing node details.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    input_validator_node, 
    commit_fetcher_node, 
    commit_analyzer_node,
    content_synthesizer_node,
    human_refinement_node,
    publishing_decision_node,
    save_local_draft_node,
    publish_to_ghost_node
)



# ============================ CONDITIONAL EDGES ============================
def check_commit_data(state: AgentState) -> Literal["continue", "end"]:
    """
    Check if commit_data was successfully fetched.
    
    If not, end the workflow to prevent errors in downstream nodes.
    """
    if state.commit_data:
        return "continue"
    else:
        print("❌ Halting workflow: Commit data could not be fetched.")
        return "end"


def should_continue_iteration(state: AgentState) -> Literal["content_synthesizer", "publishing_decision_step"]:
    """
    Determine if content synthesis should continue iterating or move to publishing.
    
    Args:
        state: Current workflow state
        
    Returns:
        Next node to execute based on user satisfaction and iteration limits
    """
    # First, check if we've hit the maximum number of iterations
    if state.synthesis_iteration_count >= state.max_iterations:
        print(f"⚠️ Max iterations ({state.max_iterations}) reached. Moving to publishing decision.")
        return "publishing_decision_step"

    # If user is satisfied, move to the next step
    if state.user_satisfied:
        return "publishing_decision_step"
    
    # Otherwise, loop back for another refinement iteration
    return "content_synthesizer"


def route_after_publishing_decision(state: AgentState) -> Literal["publish_to_ghost", "save_local_draft", "end"]:
    """
    Determines the next step based on the user's publishing decision.
    """
    decision = state.publishing_decision
    if decision == "ghost":
        return "publish_to_ghost"
    elif decision == "local":
        return "save_local_draft"
    else:  # This covers "discard" or any other case
        return "end"


# ============================ NODES (Placeholders) ============================

def create_workflow() -> StateGraph:
    """
    Create and configure the BlueStar workflow graph.
    """
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("input_validator", input_validator_node)
    workflow.add_node("commit_fetcher", commit_fetcher_node)
    workflow.add_node("commit_analyzer", commit_analyzer_node)
    workflow.add_node("content_synthesizer", content_synthesizer_node)
    workflow.add_node("human_refinement_node", human_refinement_node)
    workflow.add_node("publishing_decision_step", publishing_decision_node)
    workflow.add_node("publish_to_ghost", publish_to_ghost_node)
    workflow.add_node("save_local_draft", save_local_draft_node)

    # Define workflow edges
    workflow.add_edge("input_validator", "commit_fetcher")
    
    # Conditional edge: Check if commit data was fetched successfully
    workflow.add_conditional_edges(
        "commit_fetcher",
        check_commit_data,
        {
            "continue": "commit_analyzer",
            "end": END
        }
    )

    workflow.add_edge("commit_analyzer", "content_synthesizer")
    workflow.add_edge("content_synthesizer", "human_refinement_node")

    # Conditional edge: iteration control
    workflow.add_conditional_edges(
        "human_refinement_node",
        should_continue_iteration,
        {
            "content_synthesizer": "content_synthesizer",
            "publishing_decision_step": "publishing_decision_step"
        }
    )

    # Conditional edge: publishing decision
    workflow.add_conditional_edges(
        "publishing_decision_step",
        route_after_publishing_decision,
        {
            "publish_to_ghost": "publish_to_ghost",
            "save_local_draft": "save_local_draft",
            "end": END
        }
    )

    # End workflow after publishing or saving
    workflow.add_edge("publish_to_ghost", END)
    workflow.add_edge("save_local_draft", END)

    # Set entry point
    workflow.set_entry_point("input_validator")

    return workflow


def create_app():
    """
    Create compiled LangGraph application with checkpointing.
    
    Returns:
        Compiled LangGraph app ready for execution
    """
    workflow = create_workflow()
    
    # Add memory for conversation persistence
    memory = MemorySaver()
    
    # Compile with checkpointer for conversation history
    app = workflow.compile(checkpointer=memory)
    
    return app


# Example usage for testing
if __name__ == "__main__":
    # Create sample state for testing
    test_state = AgentState(
        raw_input="domini04/bluestar e64997b24625a4e90c39d019d4fd25a37a4b3185",
        repo_identifier="domini04/bluestar",
        commit_sha="e64997b24625a4e90c39d019d4fd25a37a4b3185"
    )
    
    # Create and run workflow
    app = create_app()
    
    print("🚀 Starting BlueStar workflow...")
    print(f"📝 Initial state: {test_state}")
    print("=" * 50)
    
    # Execute workflow
    config = {"configurable": {"thread_id": "test_workflow"}}
    
    try:
        for event in app.stream(test_state, config, stream_mode="values"):
            current_state = event
            print(f"📊 Current step: {current_state.current_step}")
            print(f"⏱️  Workflow duration: {current_state.get_workflow_duration():.2f}s")
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Workflow error: {e}")
    
    print("✅ Workflow completed!") 