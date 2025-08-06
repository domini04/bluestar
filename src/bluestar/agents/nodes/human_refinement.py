from typing import List
from rich.console import Console
from rich.markdown import Markdown

from bluestar.agents.state import AgentState
from bluestar.formats.llm_outputs import BlogPostOutput, ContentBlock, HeadingBlock, ParagraphBlock, CodeBlock, ListBlock

def _convert_blog_post_to_markdown(blog_post: BlogPostOutput) -> str: #TODO: Adding this makes the BlogPostOutput render twice. Once to markdown, then to Ghost Blog format later. Consider if this is optimal.
    """Converts a BlogPostOutput object to a Markdown string."""
    markdown_parts = []
    
    # Add Title
    markdown_parts.append(f"# {blog_post.title}\n")
    
    # Add Summary
    markdown_parts.append(f"_{blog_post.summary}_\n")
    
    # Add Body Content
    for block in blog_post.body:
        if isinstance(block, HeadingBlock):
            markdown_parts.append(f"{'#' * block.level} {block.content}")
        elif isinstance(block, ParagraphBlock):
            markdown_parts.append(block.content)
        elif isinstance(block, CodeBlock):
            markdown_parts.append(f"```{block.language}\n{block.content}\n```")
        elif isinstance(block, ListBlock):
            for item in block.items:
                markdown_parts.append(f"- {item}")
        markdown_parts.append("\n") # Add a newline for spacing between blocks

    return "\n".join(markdown_parts)

def human_refinement_node(state: AgentState) -> AgentState:
    """
    Presents the draft to the user, gets feedback, and updates the state.
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
