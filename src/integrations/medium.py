"""
Medium integration functionality.
"""
import os
import json
from typing import Dict, Any, List, Optional

import requests

from ..types.integrations import (
    MediumCredentials,
    MediumPostOptions,
    IntegrationResult
)


class MediumIntegrationError(Exception):
    """Exception raised for errors in the Medium integration process."""
    pass


def upload_post(
    credentials: MediumCredentials,
    options: MediumPostOptions
) -> IntegrationResult:
    """
    Upload a post to Medium.
    
    Args:
        credentials: The Medium credentials.
        options: The post options.
        
    Returns:
        The integration result.
        
    Raises:
        MediumIntegrationError: If an error occurs during upload.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get user ID
        response = requests.get(
            "https://api.medium.com/v1/me",
            headers=headers
        )
        
        # Check response
        if response.status_code != 200:
            return IntegrationResult(
                success=False,
                message=f"Failed to get user ID: {response.text}",
                data=None
            )
        
        user_id = response.json()["data"]["id"]
        
        # Create post data
        post_data = {
            "title": options.title,
            "contentFormat": options.content_format,
            "content": options.content,
            "tags": options.tags,
            "publishStatus": options.publish_status
        }
        
        if options.canonical_url:
            post_data["canonicalUrl"] = options.canonical_url
        
        # Upload post
        response = requests.post(
            f"https://api.medium.com/v1/users/{user_id}/posts",
            headers=headers,
            json=post_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            post_data = response.json()["data"]
            return IntegrationResult(
                success=True,
                message=f"Post uploaded successfully",
                data={"post_id": post_data["id"], "post_url": post_data["url"]}
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to upload post: {response.text}",
                data=None
            )
    except Exception as e:
        raise MediumIntegrationError(f"Error uploading post: {str(e)}")


def get_user_publications(
    credentials: MediumCredentials
) -> List[Dict[str, Any]]:
    """
    Get publications for the authenticated user.
    
    Args:
        credentials: The Medium credentials.
        
    Returns:
        A list of publications.
        
    Raises:
        MediumIntegrationError: If an error occurs during retrieval.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Accept": "application/json"
        }
        
        # Get user ID
        response = requests.get(
            "https://api.medium.com/v1/me",
            headers=headers
        )
        
        # Check response
        if response.status_code != 200:
            raise MediumIntegrationError(f"Failed to get user ID: {response.text}")
        
        user_id = response.json()["data"]["id"]
        
        # Get publications
        response = requests.get(
            f"https://api.medium.com/v1/users/{user_id}/publications",
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise MediumIntegrationError(f"Failed to get publications: {response.text}")
    except Exception as e:
        raise MediumIntegrationError(f"Error getting publications: {str(e)}")


def upload_post_to_publication(
    credentials: MediumCredentials,
    publication_id: str,
    options: MediumPostOptions
) -> IntegrationResult:
    """
    Upload a post to a Medium publication.
    
    Args:
        credentials: The Medium credentials.
        publication_id: The ID of the publication.
        options: The post options.
        
    Returns:
        The integration result.
        
    Raises:
        MediumIntegrationError: If an error occurs during upload.
    """
    try:
        # Create authentication header
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get user ID
        response = requests.get(
            "https://api.medium.com/v1/me",
            headers=headers
        )
        
        # Check response
        if response.status_code != 200:
            return IntegrationResult(
                success=False,
                message=f"Failed to get user ID: {response.text}",
                data=None
            )
        
        user_id = response.json()["data"]["id"]
        
        # Create post data
        post_data = {
            "title": options.title,
            "contentFormat": options.content_format,
            "content": options.content,
            "tags": options.tags,
            "publishStatus": options.publish_status
        }
        
        if options.canonical_url:
            post_data["canonicalUrl"] = options.canonical_url
        
        # Upload post
        response = requests.post(
            f"https://api.medium.com/v1/publications/{publication_id}/posts",
            headers=headers,
            json=post_data
        )
        
        # Check response
        if response.status_code in (200, 201):
            post_data = response.json()["data"]
            return IntegrationResult(
                success=True,
                message=f"Post uploaded to publication successfully",
                data={"post_id": post_data["id"], "post_url": post_data["url"]}
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to upload post to publication: {response.text}",
                data=None
            )
    except Exception as e:
        raise MediumIntegrationError(f"Error uploading post to publication: {str(e)}")


def convert_markdown_to_medium(
    markdown_content: str
) -> str:
    """
    Convert Markdown content to Medium-compatible format.
    
    Args:
        markdown_content: The Markdown content.
        
    Returns:
        The Medium-compatible content.
        
    Raises:
        MediumIntegrationError: If an error occurs during conversion.
    """
    try:
        # Medium supports most Markdown syntax, but there are some differences
        # This function handles those differences
        
        # Replace image syntax
        # Markdown: ![alt text](image_url)
        # Medium: <img src="image_url" alt="alt text">
        import re
        
        # Replace image syntax
        medium_content = re.sub(
            r"!\[(.*?)\]\((.*?)\)",
            r'<img src="\2" alt="\1">',
            markdown_content
        )
        
        return medium_content
    except Exception as e:
        raise MediumIntegrationError(f"Error converting Markdown to Medium format: {str(e)}")


def upload_blog_post(
    credentials: MediumCredentials,
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    publication_id: Optional[str] = None,
    canonical_url: Optional[str] = None,
    publish_status: str = "draft"
) -> IntegrationResult:
    """
    Upload a blog post to Medium.
    
    Args:
        credentials: The Medium credentials.
        title: The title of the blog post.
        content: The content of the blog post.
        tags: The tags for the blog post.
        publication_id: The ID of the publication to upload to.
        canonical_url: The canonical URL of the blog post.
        publish_status: The publish status of the blog post.
        
    Returns:
        The integration result.
        
    Raises:
        MediumIntegrationError: If an error occurs during upload.
    """
    try:
        # Convert content to Medium format if it's Markdown
        if "<" not in content and "[" in content:
            content = convert_markdown_to_medium(content)
            content_format = "markdown"
        else:
            content_format = "html"
        
        # Create post options
        options = MediumPostOptions(
            title=title,
            content=content,
            content_format=content_format,
            tags=tags or [],
            canonical_url=canonical_url,
            publish_status=publish_status
        )
        
        # Upload post
        if publication_id:
            return upload_post_to_publication(credentials, publication_id, options)
        else:
            return upload_post(credentials, options)
    except Exception as e:
        raise MediumIntegrationError(f"Error uploading blog post: {str(e)}")
