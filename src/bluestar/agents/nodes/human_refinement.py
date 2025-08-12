from typing import List
from rich.console import Console
from rich.markdown import Markdown

from ..state import AgentState
from ...formats.llm_outputs import BlogPostOutput
from ...utils.rendering import render_body_to_string


def _convert_blog_post_to_markdown(blog_post: BlogPostOutput) -> str:
    """Converts a BlogPostOutput object to a Markdown string."""
    
    # Render the structured body content using the shared utility
    body_markdown = render_body_to_string(blog_post.body)
    
    # Combine title, summary, and body into a single markdown string
    markdown_parts = [
        f"# {blog_post.title}",
        f"_{blog_post.summary}_",
        body_markdown
    ]
    
    return "\n\n".join(markdown_parts)


def human_refinement_node(state: AgentState) -> AgentState:
    """
    Human-in-the-Loop (HIL) node for refining generated content.
    """
    if not state.blog_post:
        # Should not happen, but as a safeguard
        state.errors.append("HumanRefinementNode: No blog post found in state to review.")
        return state

    console = Console()
    
    # 1. Convert BlogPostOutput to Markdown and render it
    markdown_content = _convert_blog_post_to_markdown(state.blog_post)
    console.print(Markdown(markdown_content, style="normal"))

    # 2. Ask for user satisfaction
    while True:
        satisfied_input = input("Are you satisfied with this draft? (y/n): ").lower().strip()
        if satisfied_input in ["y", "yes"]:
            state.user_satisfied = True
            state.user_feedback = None
            break
        elif satisfied_input in ["n", "no"]:
            state.user_satisfied = False
            # 3. If not satisfied, ask for feedback
            feedback = input("What would you like me to change?: ").strip()
            state.user_feedback = feedback
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    # 4. Update iteration count
    state.synthesis_iteration_count += 1
    
    return state
