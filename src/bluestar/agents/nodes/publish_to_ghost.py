"""
PublishToGhost Node for BlueStar LangGraph Workflow

This node is responsible for publishing the generated blog post to Ghost CMS.
"""
import logging
from typing import Dict, Any

from src.bluestar.agents.state import AgentState
from src.bluestar.utils.ghost_client import GhostAdminAPI
from src.bluestar.utils.ghost_renderer import GhostHtmlRenderer
from src.bluestar.config import config as settings
from src.bluestar.core.exceptions import PublishingError, ConfigurationError

logger = logging.getLogger(__name__)

def publish_to_ghost_node(state: AgentState) -> Dict[str, Any]:
    """
    Publishes the final blog post draft to Ghost CMS using the Admin API.
    """
    logger.info("🚀 PublishToGhostNode: Publishing post to Ghost...")

    if not state.blog_post:
        error_msg = "Cannot publish to Ghost because no blog post content is available in the state."
        logger.error(error_msg)
        return {"errors": state.errors + [error_msg]}

    try:
        # 1. Get Ghost API credentials from config
        ghost_api_url = settings.ghost_api_url
        ghost_admin_api_key = settings.ghost_admin_api_key

        if not ghost_api_url or not ghost_admin_api_key:
            raise ConfigurationError("GHOST_API_URL and GHOST_ADMIN_API_KEY must be set in the environment.")

        # 2. Render the final HTML from the structured blog post content
        renderer = GhostHtmlRenderer()
        html_content = renderer.render(state.blog_post)
        
        # The GhostBlogPost model for the API needs the final rendered HTML.
        state.blog_post.html = html_content

        # 3. Initialize API client and publish the post
        ghost_client = GhostAdminAPI(api_url=ghost_api_url, admin_api_key=ghost_admin_api_key)
        published_post_data = ghost_client.publish_post(state.blog_post)

        # 4. Process the successful response and update the state
        published_url = published_post_data.get("url")
        if not published_url:
            raise PublishingError("Ghost API response did not contain a URL for the published post.")
            
        logger.info(f"✅ Successfully published post to Ghost: {published_url}")
        return {"published_url": published_url}

    except (PublishingError, ConfigurationError) as e:
        error_msg = f"Failed to publish to Ghost: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}
    except Exception as e:
        error_msg = f"An unexpected error occurred in PublishToGhostNode: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}

