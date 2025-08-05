"""
Ghost HTML Renderer for BlueStar

This module provides a dedicated renderer to convert the platform-agnostic,
structured `BlogPostOutput` into a `GhostBlogPost` object, which is ready for
the Ghost Admin API.
"""

import html
from typing import List

from ..formats.llm_outputs import BlogPostOutput, ContentBlock, ParagraphBlock, HeadingBlock, ListBlock, CodeBlock
from ..formats.blog_formats import GhostBlogPost, GhostTag, GhostAuthor

class GhostHtmlRenderer:
    """
    Translates a structured BlogPostOutput into a Ghost-CMS-compatible format.
    """

    def render(self, blog_post_output: BlogPostOutput) -> GhostBlogPost:
        """
        Renders the structured BlogPostOutput into a GhostBlogPost object.

        Args:
            blog_post_output: The structured content from the ContentSynthesizer.

        Returns:
            A GhostBlogPost object ready for the Ghost Admin API.
        """
        # 1. Render the body content blocks into a single HTML string
        body_html = self._render_body(blog_post_output.body)

        # 2. Map the metadata from BlogPostOutput to GhostBlogPost fields
        ghost_post = GhostBlogPost(
            title=blog_post_output.title,
            html=body_html,
            excerpt=blog_post_output.summary,
            meta_description=blog_post_output.summary,
            tags=[GhostTag(name=tag) for tag in blog_post_output.tags],
            authors=[GhostAuthor(name=blog_post_output.author)],
            status="draft" # Default to draft status
        )
        
        return ghost_post

    def _render_body(self, body: List[ContentBlock]) -> str:
        """
        Iterates through content blocks and converts them to HTML.
        """
        html_parts = []
        for block in body:
            if isinstance(block, ParagraphBlock):
                html_parts.append(self._render_paragraph(block))
            elif isinstance(block, HeadingBlock):
                html_parts.append(self._render_heading(block))
            elif isinstance(block, ListBlock):
                html_parts.append(self._render_list(block))
            elif isinstance(block, CodeBlock):
                html_parts.append(self._render_code_block(block))
        return "\\n".join(html_parts)

    def _render_paragraph(self, block: ParagraphBlock) -> str:
        """Renders a ParagraphBlock to an HTML <p> tag."""
        return f"<p>{block.content}</p>"

    def _render_heading(self, block: HeadingBlock) -> str:
        """Renders a HeadingBlock to an HTML <h1>, <h2>, etc. tag."""
        return f"<h{block.level}>{block.content}</h{block.level}>"

    def _render_list(self, block: ListBlock) -> str:
        """Renders a ListBlock to an HTML <ul> with <li> items."""
        list_items = "".join([f"<li>{item}</li>" for item in block.items])
        return f"<ul>\\n{list_items}\\n</ul>"

    def _render_code_block(self, block: CodeBlock) -> str:
        """
        Renders a CodeBlock to a Ghost-compatible HTML <pre><code> block,
        ensuring the code content is properly escaped.
        """
        escaped_code = html.escape(block.content)
        return f'<pre><code class="language-{block.language}">{escaped_code}</code></pre>'
