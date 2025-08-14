"""
Thin Notion API client for BlueStar.

Responsibilities:
- Validate target database and discover schema
- Create pages in a database
- Append blocks to a page in chunks of <= 100
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import requests


class NotionApiError(RuntimeError):
    pass


class NotionApiClient:
    def __init__(self, api_key: str, notion_version: str = "2022-06-28") -> None:
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.notion_version = notion_version

    # ============================= Low-level =============================
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }

    def _request_with_retry(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        max_retries: int = 3,
        backoff_secs: float = 1.0,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.request(method, url, headers=self._headers(), json=json)
                if response.status_code == 429:
                    # Rate limited; honor Retry-After when present
                    retry_after = float(response.headers.get("Retry-After", backoff_secs))
                    time.sleep(retry_after)
                    continue
                if 500 <= response.status_code < 600:
                    time.sleep(backoff_secs * (2 ** attempt))
                    continue
                return response
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(backoff_secs * (2 ** attempt))
        if last_exc:
            raise NotionApiError(f"Network error calling Notion: {last_exc}")
        raise NotionApiError("Unknown error contacting Notion API")

    # ============================= Databases =============================
    def get_database(self, database_id: str) -> dict:
        response = self._request_with_retry("GET", f"/databases/{database_id}")
        if not response.ok:
            raise NotionApiError(f"Failed to fetch database {database_id}: {response.status_code} {response.text}")
        return response.json()

    def discover_schema(self, database_id: str) -> Tuple[str, dict]:
        """Return (title_property_name, full_properties_schema)."""
        db = self.get_database(database_id)
        properties: dict = db.get("properties", {})

        # Find the Title property (type == 'title')
        title_name = None
        for prop_name, prop_def in properties.items():
            if prop_def.get("type") == "title":
                title_name = prop_name
                break
        if not title_name:
            raise NotionApiError("No title property found in database schema")
        return title_name, properties

    # ============================= Pages =============================
    def create_page(
        self,
        database_id: Optional[str] = None,
        properties: dict = None,
        children: Optional[List[dict]] = None,
        page_id: Optional[str] = None,
    ) -> dict:
        if not properties:
            properties = {}
        # Exactly one of database_id or page_id must be provided
        if bool(database_id) == bool(page_id):
            raise NotionApiError("create_page requires exactly one of database_id or page_id")

        parent: dict
        if database_id:
            parent = {"database_id": database_id}
        else:
            parent = {"page_id": page_id}

        payload: dict = {
            "parent": parent,
            "properties": properties,
        }
        if children:
            payload["children"] = children[:100]

        response = self._request_with_retry("POST", "/pages", json=payload)
        if not response.ok:
            raise NotionApiError(f"Failed to create page: {response.status_code} {response.text}")
        return response.json()

    # ============================= Blocks =============================
    def append_blocks(self, parent_id: str, blocks: List[dict]) -> None:
        # Append in chunks of up to 100
        for i in range(0, len(blocks), 100):
            chunk = blocks[i : i + 100]
            payload = {"children": chunk}
            response = self._request_with_retry("PATCH", f"/blocks/{parent_id}/children", json=payload)
            if not response.ok:
                raise NotionApiError(
                    f"Failed to append blocks ({i}-{i+len(chunk)}): {response.status_code} {response.text}"
                )


