"""
WordPress integration functionality.
"""

import base64
import json
import os
from typing import Any, Dict, List, Optional

import requests

from ..types.integrations import (
    IntegrationResult,
    WordPressCategory,
    WordPressCredentials,
    WordPressImage,
    WordPressPostOptions,
    WordPressTag,
)


class WordPressIntegrationError(Exception):
    """Exception raised for errors in the WordPress integration process."""

    pass


def upload_post(
    credentials: WordPressCredentials, options: WordPressPostOptions
) -> IntegrationResult:
    """
    Upload a post to WordPress.

    Args:
        credentials: The WordPress credentials.
        options: The post options.

    Returns:
        The integration result.

    Raises:
        WordPressIntegrationError: If an error occurs during upload.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

        # Create post data
        post_data = {
            "title": options.title,
            "content": options.content,
            "status": options.status,
        }

        # Add optional fields
        if options.excerpt:
            post_data["excerpt"] = options.excerpt

        if options.slug:
            post_data["slug"] = options.slug

        if options.categories:
            post_data["categories"] = options.categories

        if options.tags:
            post_data["tags"] = options.tags

        if options.featured_media:
            post_data["featured_media"] = options.featured_media

        # Upload post
        response = requests.post(
            f"{credentials.site_url}/wp-json/wp/v2/posts",
            headers=headers,
            json=post_data,
        )

        # Check response
        if response.status_code in (200, 201):
            post_data = response.json()
            return IntegrationResult(
                success=True,
                message=f"Post uploaded successfully with ID {post_data['id']}",
                data={"post_id": post_data["id"], "post_url": post_data["link"]},
            )
        else:
            return IntegrationResult(
                success=False,
                message=f"Failed to upload post: {response.text}",
                data=None,
            )
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while uploading post: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.HTTPError as e:
        raise WordPressIntegrationError(f"WordPress HTTP error while uploading post: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while uploading post: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except (TypeError, ValueError) as e:
        raise WordPressIntegrationError(f"Error processing WordPress response: {str(e)}") from e
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error uploading post: {str(e)}") from e


def get_categories(credentials: WordPressCredentials) -> List[WordPressCategory]:
    """
    Get categories from WordPress.

    Args:
        credentials: The WordPress credentials.

    Returns:
        A list of WordPress categories.

    Raises:
        WordPressIntegrationError: If an error occurs during retrieval.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}

        # Get categories
        response = requests.get(
            f"{credentials.site_url}/wp-json/wp/v2/categories", headers=headers
        )

        # Check response
        if response.status_code == 200:
            categories_data = response.json()
            categories = []

            for category_data in categories_data:
                categories.append(
                    WordPressCategory(
                        id=category_data["id"],
                        name=category_data["name"],
                        slug=category_data["slug"],
                    )
                )

            return categories
        else:
            raise WordPressIntegrationError(
                f"Failed to get categories: {response.text}"
            )
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while getting categories: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while getting categories: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error getting categories: {str(e)}") from e


def get_tags(credentials: WordPressCredentials) -> List[WordPressTag]:
    """
    Get tags from WordPress.

    Args:
        credentials: The WordPress credentials.

    Returns:
        A list of WordPress tags.

    Raises:
        WordPressIntegrationError: If an error occurs during retrieval.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}

        # Get tags
        response = requests.get(
            f"{credentials.site_url}/wp-json/wp/v2/tags", headers=headers
        )

        # Check response
        if response.status_code == 200:
            tags_data = response.json()
            tags = []

            for tag_data in tags_data:
                tags.append(
                    WordPressTag(
                        id=tag_data["id"], name=tag_data["name"], slug=tag_data["slug"]
                    )
                )

            return tags
        else:
            raise WordPressIntegrationError(f"Failed to get tags: {response.text}")
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while getting tags: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while getting tags: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error getting tags: {str(e)}") from e


def create_category(
    credentials: WordPressCredentials, name: str, slug: Optional[str] = None
) -> WordPressCategory:
    """
    Create a category in WordPress.

    Args:
        credentials: The WordPress credentials.
        name: The name of the category.
        slug: The slug of the category.

    Returns:
        The created WordPress category.

    Raises:
        WordPressIntegrationError: If an error occurs during creation.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

        # Create category data
        category_data = {"name": name}

        if slug:
            category_data["slug"] = slug

        # Create category
        response = requests.post(
            f"{credentials.site_url}/wp-json/wp/v2/categories",
            headers=headers,
            json=category_data,
        )

        # Check response
        if response.status_code in (200, 201):
            category_data = response.json()
            return WordPressCategory(
                id=category_data["id"],
                name=category_data["name"],
                slug=category_data["slug"],
            )
        else:
            raise WordPressIntegrationError(
                f"Failed to create category: {response.text}"
            )
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while creating category: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while creating category: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error creating category: {str(e)}") from e


def create_tag(
    credentials: WordPressCredentials, name: str, slug: Optional[str] = None
) -> WordPressTag:
    """
    Create a tag in WordPress.

    Args:
        credentials: The WordPress credentials.
        name: The name of the tag.
        slug: The slug of the tag.

    Returns:
        The created WordPress tag.

    Raises:
        WordPressIntegrationError: If an error occurs during creation.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

        # Create tag data
        tag_data = {"name": name}

        if slug:
            tag_data["slug"] = slug

        # Create tag
        response = requests.post(
            f"{credentials.site_url}/wp-json/wp/v2/tags", headers=headers, json=tag_data
        )

        # Check response
        if response.status_code in (200, 201):
            tag_data = response.json()
            return WordPressTag(
                id=tag_data["id"], name=tag_data["name"], slug=tag_data["slug"]
            )
        else:
            raise WordPressIntegrationError(f"Failed to create tag: {response.text}")
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while creating tag: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while creating tag: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error creating tag: {str(e)}") from e


def upload_image(
    credentials: WordPressCredentials, image_path: str, alt_text: Optional[str] = None
) -> WordPressImage:
    """
    Upload an image to WordPress.

    Args:
        credentials: The WordPress credentials.
        image_path: The path to the image.
        alt_text: The alt text for the image.

    Returns:
        The uploaded WordPress image.

    Raises:
        WordPressIntegrationError: If an error occurs during upload.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}"}

        # Get image filename
        filename = os.path.basename(image_path)

        # Read image file
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Upload image
        files = {"file": (filename, image_data)}

        response = requests.post(
            f"{credentials.site_url}/wp-json/wp/v2/media", headers=headers, files=files
        )

        # Check response
        if response.status_code in (200, 201):
            image_data = response.json()

            # Update alt text if provided
            if alt_text:
                update_image_alt_text(credentials, image_data["id"], alt_text)

            return WordPressImage(
                id=image_data["id"], url=image_data["source_url"], alt=alt_text or ""
            )
        else:
            raise WordPressIntegrationError(f"Failed to upload image: {response.text}")
    except FileNotFoundError as e:
        raise WordPressIntegrationError(f"Image file not found: {str(e)}") from e
    except PermissionError as e:
        raise WordPressIntegrationError(f"Permission denied reading image file: {str(e)}") from e
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while uploading image: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while uploading image: {str(e)}") from e
    except KeyError as e:
        raise WordPressIntegrationError(f"Unexpected WordPress response format, missing key: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error uploading image: {str(e)}") from e


def update_image_alt_text(
    credentials: WordPressCredentials, image_id: int, alt_text: str
) -> None:
    """
    Update the alt text of an image in WordPress.

    Args:
        credentials: The WordPress credentials.
        image_id: The ID of the image.
        alt_text: The alt text for the image.

    Raises:
        WordPressIntegrationError: If an error occurs during update.
    """
    try:
        # Create authentication header
        auth = base64.b64encode(
            f"{credentials.username}:{credentials.password}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

        # Update alt text
        response = requests.post(
            f"{credentials.site_url}/wp-json/wp/v2/media/{image_id}",
            headers=headers,
            json={"alt_text": alt_text},
        )

        # Check response
        if response.status_code != 200:
            raise WordPressIntegrationError(
                f"Failed to update image alt text: {response.text}"
            )
    except requests.Timeout as e:
        raise WordPressIntegrationError(f"WordPress request timed out while updating image alt text: {str(e)}") from e
    except requests.ConnectionError as e:
        raise WordPressIntegrationError(f"Network error connecting to WordPress: {str(e)}") from e
    except requests.RequestException as e:
        raise WordPressIntegrationError(f"WordPress request failed while updating image alt text: {str(e)}") from e
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error updating image alt text: {str(e)}") from e


def get_or_create_category(
    credentials: WordPressCredentials, name: str
) -> WordPressCategory:
    """
    Get or create a category in WordPress.

    Args:
        credentials: The WordPress credentials.
        name: The name of the category.

    Returns:
        The WordPress category.

    Raises:
        WordPressIntegrationError: If an error occurs during retrieval or creation.
    """
    try:
        # Get categories
        categories = get_categories(credentials)

        # Check if category exists
        for category in categories:
            if category.name.lower() == name.lower():
                return category

        # Create category
        return create_category(credentials, name)
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error getting or creating category: {str(e)}") from e


def get_or_create_tag(credentials: WordPressCredentials, name: str) -> WordPressTag:
    """
    Get or create a tag in WordPress.

    Args:
        credentials: The WordPress credentials.
        name: The name of the tag.

    Returns:
        The WordPress tag.

    Raises:
        WordPressIntegrationError: If an error occurs during retrieval or creation.
    """
    try:
        # Get tags
        tags = get_tags(credentials)

        # Check if tag exists
        for tag in tags:
            if tag.name.lower() == name.lower():
                return tag

        # Create tag
        return create_tag(credentials, name)
    except WordPressIntegrationError:
        raise
    except Exception as e:
        raise WordPressIntegrationError(f"Unexpected error getting or creating tag: {str(e)}") from e


def upload_blog_post(
    credentials: WordPressCredentials,
    title: str,
    content: str,
    excerpt: Optional[str] = None,
    categories: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    status: str = "draft",
    featured_image: Optional[str] = None,
) -> IntegrationResult:
    """
    Upload a blog post to WordPress.

    Args:
        credentials: The WordPress credentials.
        title: The title of the blog post.
        content: The content of the blog post.
        excerpt: The excerpt of the blog post.
        categories: The categories of the blog post.
        tags: The tags of the blog post.
        status: The status of the blog post.
        featured_image: The path to the featured image.

    Returns:
        The integration result.

    Raises:
        WordPressIntegrationError: If an error occurs during upload.
    """
    try:
        # Process categories
        category_ids = []
        if categories:
            for category_name in categories:
                category = get_or_create_category(credentials, category_name)
                category_ids.append(category.id)

        # Process tags
        tag_ids = []
        if tags:
            for tag_name in tags:
                tag = get_or_create_tag(credentials, tag_name)
                tag_ids.append(tag.id)

        # Process featured image
        featured_media_id = 0
        if featured_image:
            image = upload_image(credentials, featured_image)
            featured_media_id = image.id

        # Create post options
        post_options = WordPressPostOptions(
            title=title,
            content=content,
            excerpt=excerpt,
            slug=None,  # Let WordPress generate the slug
            status=status,
            categories=category_ids,
            tags=tag_ids,
            featured_media=featured_media_id,
        )

        # Upload post
        return upload_post(credentials, post_options)
    except WordPressIntegrationError as e:
        return IntegrationResult(
            success=False, message=str(e), data=None
        )
    except ValueError as e:
        return IntegrationResult(
            success=False, message=f"Invalid blog post data: {str(e)}", data=None
        )
    except Exception as e:
        return IntegrationResult(
            success=False, message=f"Unexpected error uploading blog post: {str(e)}", data=None
        )
