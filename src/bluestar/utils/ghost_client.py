"""
Ghost Admin API Client

A client for interacting with the Ghost Admin API to publish and manage posts.
This client handles JWT authentication and post creation.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import jwt
import requests
from requests.exceptions import RequestException

from src.bluestar.core.exceptions import PublishingError
from src.bluestar.formats.blog_formats import GhostBlogPost

logger = logging.getLogger(__name__)

class GhostAdminAPI:
    """A wrapper for the Ghost Admin API."""

    def __init__(self, api_url: str, admin_api_key: str):
        if not api_url or not admin_api_key:
            raise PublishingError("Ghost API URL and Admin API Key are required.")
        
        self.api_url = api_url.rstrip('/')
        self.admin_api_key = admin_api_key
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self):
        """Generates a JWT and sets it in the session headers."""
        try:
            key_id, secret = self.admin_api_key.split(':')
            
            headers = {'alg': 'HS256', 'typ': 'JWT', 'kid': key_id}
            
            payload = {
                'iat': int(datetime.now().timestamp()),
                'exp': int((datetime.now() + timedelta(minutes=5)).timestamp()),
                'aud': '/admin/'
            }
            
            token = jwt.encode(
                payload,
                bytes.fromhex(secret),
                algorithm='HS256',
                headers=headers
            )
            
            self.session.headers.update({"Authorization": f"Ghost {token}"})
            logger.debug("Successfully generated Ghost Admin API token.")

        except (ValueError, TypeError) as e:
            raise PublishingError(f"Invalid Ghost Admin API Key format. It should be 'id:secret'. Error: {e}")
        except Exception as e:
            logger.error(f"Failed to generate Ghost token: {e}", exc_info=True)
            raise PublishingError(f"An unexpected error occurred during JWT generation: {e}")

    def publish_post(self, post: GhostBlogPost) -> Dict[str, Any]:
        """
        Publishes a new post to Ghost.

        Args:
            post: A GhostBlogPost object containing all post details.

        Returns:
            The JSON response from the Ghost API for the created post.
        """
        endpoint = f"{self.api_url}/ghost/api/admin/posts/"
        
        # Ghost API expects a specific JSON structure with a 'posts' array
        payload = {
            "posts": [post.model_dump(include={'title', 'html', 'tags', 'authors', 'status', 'slug'})]
        }

        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            
            json_response = response.json()
            created_post = json_response.get("posts", [])[0]
            
            logger.info(f"Successfully published post: {created_post.get('title')}")
            return created_post
            
        except RequestException as e:
            logger.error(f"Failed to publish post to Ghost: {e}", exc_info=True)
            raise PublishingError(f"Error connecting to Ghost API: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Malformed response from Ghost API: {response.text}", exc_info=True)
            raise PublishingError(f"Malformed response received from Ghost API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Ghost publishing: {e}", exc_info=True)
            raise PublishingError(f"An unexpected publishing error occurred: {e}")

