"""
Notion Renderer for BlueStar

This module translates a structured `BlogPostOutput` into Notion API payloads.

Mappings from BlogPostOutput → Notion objects:
  - title (str)       → Page `properties` Title (type: title)
  - summary (str)     → Page `properties` Summary (type: rich_text), if present
  - tags (List[str])  → Page `properties` Tags (type: multi_select), if present
  - author (str)      → Page `properties` Author (type: rich_text), if present
  - body (blocks)     → Page content `children` (Notion blocks):
      * ParagraphBlock → `paragraph`
      * HeadingBlock   → `heading_1|2|3` (levels >3 clamped to 3)
      * ListBlock      → sequence of `bulleted_list_item`
      * CodeBlock      → `code` (language mapped as lowercased string)

Note: Only properties that exist in the destination database schema are included.
Title is required; others are optional and applied when available.
"""

from __future__ import annotations

from typing import List, Tuple

from ..formats.llm_outputs import (
    BlogPostOutput,
    ContentBlock,
    ParagraphBlock,
    HeadingBlock,
    ListBlock,
    CodeBlock,
)


class NotionRenderer:
    def __init__(self, title_property: str, db_properties_schema: dict):
        self.title_property = title_property
        self.db_properties_schema = db_properties_schema or {}

    def render(self, post: BlogPostOutput) -> Tuple[dict, List[dict]]:
        properties = self._render_properties(post)
        blocks = self._render_blocks(post.body)
        return properties, blocks

    def _render_properties(self, post: BlogPostOutput) -> dict:
        properties: dict = {}

        # Title is mandatory
        properties[self.title_property] = {
            "title": [{"type": "text", "text": {"content": post.title}}]
        }

        # Optional mappings based on available schema
        if self._has_prop_of_type("rich_text", "Summary"):
            properties["Summary"] = {
                "rich_text": [{"type": "text", "text": {"content": post.summary}}]
            }

        if self._has_prop_of_type("multi_select", "Tags"):
            properties["Tags"] = {
                "multi_select": [{"name": t} for t in post.tags]
            }

        # Author can be rich_text by default (people would require user IDs)
        if self._has_prop_of_type("rich_text", "Author"):
            properties["Author"] = {
                "rich_text": [{"type": "text", "text": {"content": post.author}}]
            }

        # Default Status to Draft if a select property exists
        if self._has_prop_of_type("select", "Status"):
            properties["Status"] = {"select": {"name": "Draft"}}

        return properties

    def _render_blocks(self, body: List[ContentBlock]) -> List[dict]:
        blocks: List[dict] = []
        for block in body:
            if isinstance(block, ParagraphBlock):
                blocks.append(self._paragraph(block.content))
            elif isinstance(block, HeadingBlock):
                blocks.append(self._heading(block.level, block.content))
            elif isinstance(block, ListBlock):
                blocks.extend(self._bulleted_list(block.items))
            elif isinstance(block, CodeBlock):
                blocks.append(self._code(block.language, block.content))
        return blocks

    # ============================= Block factories =============================
    @staticmethod
    def _paragraph(text: str) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    @staticmethod
    def _heading(level: int, text: str) -> dict:
        clamped = max(1, min(3, level))
        key = f"heading_{clamped}"
        return {
            "object": "block",
            "type": key,
            key: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }

    @staticmethod
    def _bulleted_list(items: List[str]) -> List[dict]:
        blocks: List[dict] = []
        for item in items:
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": item}}
                        ]
                    },
                }
            )
        return blocks

    @staticmethod
    def _code(language: str, code: str) -> dict:
        lang = (language or "plain text").lower()
        return {
            "object": "block",
            "type": "code",
            "code": {
                "language": lang,
                "rich_text": [{"type": "text", "text": {"content": code}}],
            },
        }

    def _has_prop_of_type(self, expected_type: str, name: str) -> bool:
        prop = self.db_properties_schema.get(name)
        return bool(prop and prop.get("type") == expected_type)


