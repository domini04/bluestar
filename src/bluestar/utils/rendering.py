from typing import List, TYPE_CHECKING
from ..formats.llm_outputs import (
    ContentBlock,
    ParagraphBlock,
    HeadingBlock,
    ListBlock,
    CodeBlock,
)

if TYPE_CHECKING:
    
    from ..formats.blog_formats import BlogPostOutput

def render_body_to_string(body: List[ContentBlock]) -> str:
    """Converts a list of ContentBlock objects into a single markdown-like string."""
    rendered_parts = []
    for block in body:
        if isinstance(block, ParagraphBlock):
            rendered_parts.append(block.content)
        elif isinstance(block, HeadingBlock):
            rendered_parts.append(f"{'#' * block.level} {block.content}")
        elif isinstance(block, ListBlock):
            rendered_parts.append("\n".join(f"- {item}" for item in block.items))
        elif isinstance(block, CodeBlock):
            rendered_parts.append(f"```{block.language}\n{block.content}\n```")
    return "\n\n".join(rendered_parts)

def render_blog_post_to_markdown(post: "BlogPostOutput") -> str:
    """Renders the entire BlogPostOutput object to a single Markdown string."""
    if not post:
        return "No content generated yet."
    
    # Start with the title
    content = f"# {post.title}\n\n"
    
    # Add the introduction if it exists
    if post.introduction:
        content += f"_{post.introduction}_\n\n"

    # Render the main body using the existing utility function
    content += render_body_to_string(post.content_blocks)
            
    return content
