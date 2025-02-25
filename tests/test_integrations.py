"""
Tests for the integrations module.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integrations.github import (
    upload_file,
    create_repository,
    get_repositories,
    get_repository,
    create_branch,
    create_pull_request,
    upload_blog_post
)
from src.integrations.medium import (
    upload_post,
    get_user_publications,
    upload_post_to_publication,
    convert_markdown_to_medium,
    upload_blog_post as medium_upload_blog_post
)
from src.integrations.wordpress import (
    upload_post as wp_upload_post,
    get_categories,
    create_category,
    upload_image,
    upload_blog_post as wp_upload_blog_post
)
from src.types.integrations import (
    GitHubCredentials,
    GitHubRepository,
    GitHubFileOptions,
    MediumCredentials,
    MediumPostOptions,
    WordPressCredentials,
    WordPressPostOptions,
    IntegrationResult
)


class TestGitHubIntegration(unittest.TestCase):
    """Test cases for the GitHub integration module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample GitHub credentials and repository for testing
        self.credentials = GitHubCredentials(token="test_token")
        self.repository = GitHubRepository(owner="test_owner", name="test_repo")
        self.file_options = GitHubFileOptions(
            path="test/path.md",
            content="# Test Content",
            message="Test commit message",
            branch="main"
        )

    @patch('src.integrations.github.requests.get')
    @patch('src.integrations.github.requests.put')
    def test_upload_file(self, mock_put, mock_get):
        """Test the upload_file function."""
        # Set up mocks
        mock_get.return_value = MagicMock(status_code=404)  # File doesn't exist
        mock_put.return_value = MagicMock(
            status_code=201,
            json=lambda: {"content": {"html_url": "https://github.com/test_owner/test_repo/blob/main/test/path.md"}}
        )
        
        # Call the function
        result = upload_file(self.credentials, self.repository, self.file_options)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.data["file_url"], "https://github.com/test_owner/test_repo/blob/main/test/path.md")
        
        # Verify mocks were called
        mock_get.assert_called_once()
        mock_put.assert_called_once()

    @patch('src.integrations.github.requests.post')
    def test_create_repository(self, mock_post):
        """Test the create_repository function."""
        # Set up mocks
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"name": "test_repo", "owner": {"login": "test_owner"}}
        )
        
        # Call the function
        result = create_repository(self.credentials, "test_repo", "Test repository", False)
        
        # Assertions
        self.assertEqual(result.owner, "test_owner")
        self.assertEqual(result.name, "test_repo")
        
        # Verify mocks were called
        mock_post.assert_called_once()

    @patch('src.integrations.github.requests.get')
    def test_get_repositories(self, mock_get):
        """Test the get_repositories function."""
        # Set up mocks
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"name": "repo1", "owner": {"login": "test_owner"}},
                {"name": "repo2", "owner": {"login": "test_owner"}}
            ]
        )
        
        # Call the function
        result = get_repositories(self.credentials)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "repo1")
        self.assertEqual(result[0].owner, "test_owner")
        self.assertEqual(result[1].name, "repo2")
        self.assertEqual(result[1].owner, "test_owner")
        
        # Verify mocks were called
        mock_get.assert_called_once()

    @patch('src.integrations.github.upload_file')
    def test_upload_blog_post(self, mock_upload_file):
        """Test the upload_blog_post function."""
        # Set up mocks
        mock_upload_file.return_value = IntegrationResult(
            success=True,
            message="File uploaded successfully",
            data={"file_url": "https://github.com/test_owner/test_repo/blob/main/content/blog/test-blog-post.md"}
        )
        
        # Call the function
        result = upload_blog_post(
            credentials=self.credentials,
            repository=self.repository,
            title="Test Blog Post",
            content="# Test Blog Post\n\nThis is a test blog post.",
            path="content/blog/test-blog-post.md",
            branch="main",
            commit_message="Add blog post: Test Blog Post"
        )
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(
            result.data["file_url"], 
            "https://github.com/test_owner/test_repo/blob/main/content/blog/test-blog-post.md"
        )
        
        # Verify mocks were called
        mock_upload_file.assert_called_once()


class TestMediumIntegration(unittest.TestCase):
    """Test cases for the Medium integration module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample Medium credentials and post options for testing
        self.credentials = MediumCredentials(token="test_token")
        self.post_options = MediumPostOptions(
            title="Test Post",
            content="# Test Post\n\nThis is a test post.",
            content_format="markdown",
            tags=["test", "blog"],
            canonical_url=None,
            publish_status="draft"
        )

    @patch('src.integrations.medium.requests.get')
    @patch('src.integrations.medium.requests.post')
    def test_upload_post(self, mock_post, mock_get):
        """Test the upload_post function."""
        # Set up mocks
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"id": "user123"}}
        )
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"data": {"id": "post123", "url": "https://medium.com/@user/test-post-123"}}
        )
        
        # Call the function
        result = upload_post(self.credentials, self.post_options)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.data["post_id"], "post123")
        self.assertEqual(result.data["post_url"], "https://medium.com/@user/test-post-123")
        
        # Verify mocks were called
        mock_get.assert_called_once()
        mock_post.assert_called_once()

    @patch('src.integrations.medium.requests.get')
    def test_get_user_publications(self, mock_get):
        """Test the get_user_publications function."""
        # Set up mocks
        mock_get.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {"data": {"id": "user123"}}
            ),
            MagicMock(
                status_code=200,
                json=lambda: {"data": [
                    {"id": "pub1", "name": "Publication 1"},
                    {"id": "pub2", "name": "Publication 2"}
                ]}
            )
        ]
        
        # Call the function
        result = get_user_publications(self.credentials)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "pub1")
        self.assertEqual(result[0]["name"], "Publication 1")
        self.assertEqual(result[1]["id"], "pub2")
        self.assertEqual(result[1]["name"], "Publication 2")
        
        # Verify mocks were called
        self.assertEqual(mock_get.call_count, 2)

    def test_convert_markdown_to_medium(self):
        """Test the convert_markdown_to_medium function."""
        # Test data
        markdown = "# Heading\n\nThis is a paragraph with an ![image](https://example.com/image.jpg)."
        
        # Call the function
        result = convert_markdown_to_medium(markdown)
        
        # Assertions
        self.assertIn("# Heading", result)
        self.assertIn("This is a paragraph with an", result)
        self.assertIn('<img src="https://example.com/image.jpg" alt="image">', result)

    @patch('src.integrations.medium.upload_post')
    def test_upload_blog_post(self, mock_upload_post):
        """Test the upload_blog_post function."""
        # Set up mocks
        mock_upload_post.return_value = IntegrationResult(
            success=True,
            message="Post uploaded successfully",
            data={"post_id": "post123", "post_url": "https://medium.com/@user/test-post-123"}
        )
        
        # Call the function
        result = medium_upload_blog_post(
            credentials=self.credentials,
            title="Test Blog Post",
            content="# Test Blog Post\n\nThis is a test blog post.",
            tags=["test", "blog"],
            publish_status="draft"
        )
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.data["post_id"], "post123")
        self.assertEqual(result.data["post_url"], "https://medium.com/@user/test-post-123")
        
        # Verify mocks were called
        mock_upload_post.assert_called_once()


class TestWordPressIntegration(unittest.TestCase):
    """Test cases for the WordPress integration module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample WordPress credentials and post options for testing
        self.credentials = WordPressCredentials(
            site_url="https://example.com/wp-json",
            username="test_user",
            password="test_password"
        )
        self.post_options = WordPressPostOptions(
            title="Test Post",
            content="<!-- wp:paragraph --><p>This is a test post.</p><!-- /wp:paragraph -->",
            excerpt="This is a test post.",
            slug="test-post",
            status="draft",
            categories=[1],
            tags=[],
            featured_media=0
        )

    @patch('src.integrations.wordpress.requests.post')
    def test_upload_post(self, mock_post):
        """Test the upload_post function."""
        # Set up mocks
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "id": 123,
                "link": "https://example.com/test-post",
                "title": {"rendered": "Test Post"}
            }
        )
        
        # Call the function
        result = wp_upload_post(self.credentials, self.post_options)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.data["post_id"], 123)
        self.assertEqual(result.data["post_url"], "https://example.com/test-post")
        
        # Verify mocks were called
        mock_post.assert_called_once()

    @patch('src.integrations.wordpress.requests.get')
    def test_get_categories(self, mock_get):
        """Test the get_categories function."""
        # Set up mocks
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"id": 1, "name": "Category 1", "slug": "category-1"},
                {"id": 2, "name": "Category 2", "slug": "category-2"}
            ]
        )
        
        # Call the function
        result = get_categories(self.credentials)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[0].name, "Category 1")
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[1].name, "Category 2")
        
        # Verify mocks were called
        mock_get.assert_called_once()

    @patch('src.integrations.wordpress.requests.post')
    def test_create_category(self, mock_post):
        """Test the create_category function."""
        # Set up mocks
        mock_post.return_value = MagicMock(
            status_code=201,
            json=lambda: {"id": 3, "name": "New Category", "slug": "new-category"}
        )
        
        # Call the function
        result = create_category(self.credentials, "New Category")
        
        # Assertions
        self.assertEqual(result.id, 3)
        self.assertEqual(result.name, "New Category")
        self.assertEqual(result.slug, "new-category")
        
        # Verify mocks were called
        mock_post.assert_called_once()

    @patch('src.integrations.wordpress.get_categories')
    @patch('src.integrations.wordpress.create_category')
    @patch('src.integrations.wordpress.upload_post')
    def test_upload_blog_post(self, mock_upload_post, mock_create_category, mock_get_categories):
        """Test the upload_blog_post function."""
        # Set up mocks
        from src.types.integrations import WordPressCategory, WordPressTag
        mock_get_categories.return_value = [
            WordPressCategory(id=1, name="Category 1", slug="category-1")
        ]
        mock_create_category.return_value = WordPressCategory(id=2, name="Blog", slug="blog")
        
        # Mock get_or_create_tag to avoid errors
        with patch('src.integrations.wordpress.get_or_create_tag') as mock_get_or_create_tag:
            mock_get_or_create_tag.return_value = WordPressTag(id=3, name="test", slug="test")
            
            # Set up mock for upload_post
            mock_upload_post.return_value = IntegrationResult(
                success=True,
                message="Post uploaded successfully",
                data={"post_id": 123, "post_url": "https://example.com/test-post"}
            )
            
            # Call the function
            result = wp_upload_blog_post(
                credentials=self.credentials,
                title="Test Blog Post",
                content="<p>This is a test blog post.</p>",
                excerpt="This is a test blog post.",
                categories=["Blog"],
                tags=["test", "blog"],
                status="draft"
            )
            
            # Assertions
            self.assertTrue(result.success)
            self.assertEqual(result.data["post_id"], 123)
            self.assertEqual(result.data["post_url"], "https://example.com/test-post")
        
        # Verify mocks were called
        mock_get_categories.assert_called_once()
        mock_create_category.assert_called_once()
        mock_upload_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()
