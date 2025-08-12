from typing import List
from ..formats.llm_outputs import (
    ContentBlock,
    ParagraphBlock,
    HeadingBlock,
    ListBlock,
    CodeBlock,
)

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
