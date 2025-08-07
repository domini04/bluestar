"""
SaveLocalDraft Node for BlueStar LangGraph Workflow

This node is responsible for saving the generated blog post as a local HTML file.
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..state import AgentState
from ...utils.ghost_renderer import GhostHtmlRenderer

logger = logging.getLogger(__name__)

def _create_slug(title: str) -> str:
    """Converts a string into a URL-friendly slug."""
    title = title.lower()
    title = re.sub(r'[^\w\s-]', '', title)  # Remove special characters
    title = re.sub(r'[-\s]+', '-', title)   # Replace spaces/hyphens with a single dash
    return title.strip('-')

def save_local_draft_node(state: AgentState) -> Dict[str, str]:
    """
    Saves the final blog post draft to a local HTML file in the `output/` directory.

    This is a non-interactive node that executes the user's decision to save the draft.
    """
    logger.info("💾 SaveLocalDraftNode: Saving draft locally...")

    if not state.blog_post:
        error_msg = "Cannot save local draft because no blog post content is available in the state."
        logger.error(error_msg)
        return {"errors": state.errors + [error_msg]}

    try:
        # 1. Prepare filename and output path
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        title_slug = _create_slug(state.blog_post.title)
        commit_sha_short = state.commit_sha[:7]
        filename = f"{date_str}_{commit_sha_short}_{title_slug}.html"
        file_path = output_dir / filename

        # 2. Render content to a GhostBlogPost object
        renderer = GhostHtmlRenderer()
        rendered_post = renderer.render(state.blog_post)
        html_content = rendered_post.html

        # 3. Write file to disk
        file_path.write_text(html_content, encoding="utf-8")

        logger.info(f"✅ Successfully saved draft to: {file_path}")

        # 4. Update state
        return {"local_draft_path": str(file_path)}

    except IOError as e:
        error_msg = f"File system error while saving draft: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}
    except Exception as e:
        error_msg = f"An unexpected error occurred in SaveLocalDraftNode: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}
