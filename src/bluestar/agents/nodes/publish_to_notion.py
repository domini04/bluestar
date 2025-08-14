"""
PublishToNotion Node for BlueStar LangGraph Workflow

Creates a page in a user-specified Notion database using the Notion API.
Relies on:
- NOTION_API_KEY and NOTION_URL in environment (parsed in config for database_id)
- NotionApiClient for API operations
- NotionRenderer to map BlogPostOutput to Notion properties and blocks
"""

import logging
from typing import Dict, Any, Optional, List

from src.bluestar.agents.state import AgentState
from src.bluestar.config import config as settings
from src.bluestar.core.exceptions import PublishingError, ConfigurationError
from src.bluestar.utils.notion_client import NotionApiClient, NotionApiError
from src.bluestar.utils.notion_renderer import NotionRenderer


logger = logging.getLogger(__name__)


def publish_to_notion_node(state: AgentState) -> Dict[str, Any]:
    """
    Publishes the final blog post to a Notion database as a new page.
    """
    logger.info("🚀 PublishToNotionNode: Publishing post to Notion...")

    if not state.blog_post:
        error_msg = "Cannot publish to Notion because no blog post content is available in the state."
        logger.error(error_msg)
        return {"errors": state.errors + [error_msg]}

    try:
        # 1) Validate configuration
        notion_api_key: Optional[str] = settings.notion_api_key
        notion_database_id: Optional[str] = settings.notion_database_id

        if not notion_api_key:
            raise ConfigurationError("NOTION_API_KEY must be set in the environment.")
        if not notion_database_id:
            raise ConfigurationError(
                "NOTION_URL must be set (and parseable) in the environment to derive the database ID."
            )

        # 2) Initialize client and attempt database discovery; if it's a page, fall back to page-parent mode
        client = NotionApiClient(api_key=notion_api_key)
        title_property: str
        properties_schema: dict
        parent_kwargs: dict

        try:
            title_property, properties_schema = client.discover_schema(notion_database_id)
            parent_kwargs = {"database_id": notion_database_id}
        except NotionApiError as e:
            # Detect the specific case where ID is a page, not a database
            if "is a page, not a database" in str(e):
                logger.info("Notion ID is a page; using page-parent mode.")
                title_property = "title"
                properties_schema = {}
                parent_kwargs = {"page_id": notion_database_id}
            else:
                raise

        # 3) Render properties and blocks
        renderer = NotionRenderer(title_property=title_property, db_properties_schema=properties_schema)
        properties, blocks = renderer.render(state.blog_post)

        # 4) Create page (include children when <= 100 to reduce round trips)
        children: Optional[List[dict]] = blocks if len(blocks) <= 100 else None
        created_page = client.create_page(
            properties=properties,
            children=children,
            **parent_kwargs,
        )
        page_id = created_page.get("id")
        published_url = created_page.get("url")

        if not page_id:
            raise PublishingError("Notion API response did not contain a page id.")

        # 5) Append remaining blocks in chunks if needed
        if children is None and blocks:
            client.append_blocks(page_id, blocks)

        if not published_url:
            # Notion usually returns a URL; if missing, construct nothing and log.
            logger.warning("Notion page created but URL missing from response.")

        logger.info(f"✅ Successfully created Notion page: {published_url or page_id}")
        return {"published_url": published_url or page_id}

    except (ConfigurationError, PublishingError, NotionApiError) as e:
        error_msg = f"Failed to publish to Notion: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}
    except Exception as e:
        error_msg = f"An unexpected error occurred in PublishToNotionNode: {e}"
        logger.error(error_msg, exc_info=True)
        return {"errors": state.errors + [error_msg]}


