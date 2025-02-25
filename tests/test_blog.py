"""
Tests for the blog module.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.blog.make_blog import (
    generate_blog_post,
    generate_blog_post_with_research,
    post_process_blog_post,
    save_blog_post_to_markdown,
    save_blog_post_to_json,
    load_blog_post_from_json
)
from src.types.content import BlogPost, Section, SubTopic


class TestBlogModule(unittest.TestCase):
    """Test cases for the blog module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample blog post for testing
        self.sample_blog_post = BlogPost(
            title="Test Blog Post",
            description="This is a test blog post",
            sections=[
                Section(
                    title="Introduction",
                    subtopics=[
                        SubTopic(
                            title="",
                            content="This is the introduction content."
                        )
                    ]
                ),
                Section(
                    title="Main Section",
                    subtopics=[
                        SubTopic(
                            title="Subtopic 1",
                            content="This is subtopic 1 content."
                        ),
                        SubTopic(
                            title="Subtopic 2",
                            content="This is subtopic 2 content."
                        )
                    ]
                ),
                Section(
                    title="Conclusion",
                    subtopics=[
                        SubTopic(
                            title="",
                            content="This is the conclusion content."
                        )
                    ]
                )
            ],
            tags=["test", "blog"]
        )

    @patch('src.blog.make_blog.create_provider_from_env')
    @patch('src.blog.make_blog.generate_content_outline')
    @patch('src.blog.make_blog.generate_introduction')
    @patch('src.blog.make_blog.generate_section')
    @patch('src.blog.make_blog.generate_conclusion')
    @patch('src.blog.make_blog.generate_faqs')
    @patch('src.blog.make_blog.generate_meta_description')
    def test_generate_blog_post(self, mock_meta, mock_faqs, mock_conclusion, 
                               mock_section, mock_intro, mock_outline, mock_provider):
        """Test the generate_blog_post function."""
        # Set up mocks
        mock_provider.return_value = MagicMock()
        mock_outline.return_value = MagicMock(sections=["Introduction", "Section 1", "Conclusion"])
        mock_intro.return_value = MagicMock(content="Introduction content")
        mock_section.return_value = MagicMock(title="Section 1", subtopics=[MagicMock(content="Section content")])
        mock_conclusion.return_value = MagicMock(content="Conclusion content")
        mock_faqs.return_value = MagicMock(faqs=[MagicMock(question="Q1", answer="A1")])
        mock_meta.return_value = MagicMock(content="Meta description")
        
        # Call the function
        result = generate_blog_post(
            title="Test Blog",
            keywords=["test", "blog"],
            num_sections=1,
            include_faqs=True
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Blog")
        self.assertEqual(result.tags, ["test", "blog"])
        self.assertEqual(len(result.sections), 4)  # Intro, Section, Conclusion, FAQ
        
        # Verify mocks were called
        mock_provider.assert_called_once()
        mock_outline.assert_called_once()
        mock_intro.assert_called_once()
        mock_section.assert_called_once()
        mock_conclusion.assert_called_once()
        mock_faqs.assert_called_once()
        mock_meta.assert_called_once()

    @patch('src.blog.make_blog.create_provider_from_env')
    @patch('src.blog.make_blog.conduct_web_research')
    @patch('src.blog.make_blog.generate_content_outline_with_research')
    @patch('src.blog.make_blog.generate_introduction_section_with_research')
    @patch('src.blog.make_blog.generate_section_with_research')
    @patch('src.blog.make_blog.generate_conclusion_section')
    @patch('src.blog.make_blog.generate_faq_section')
    @patch('src.blog.make_blog.generate_meta_description')
    def test_generate_blog_post_with_research(self, mock_meta, mock_faqs, mock_conclusion, 
                                             mock_section, mock_intro, mock_outline, 
                                             mock_research, mock_provider):
        """Test the generate_blog_post_with_research function."""
        # Set up mocks
        mock_provider.return_value = MagicMock()
        mock_research.return_value = MagicMock()
        mock_outline.return_value = MagicMock(sections=["Introduction", "Section 1", "Conclusion"])
        mock_intro.return_value = MagicMock(title="Introduction", subtopics=[MagicMock(content="Intro content")])
        mock_section.return_value = MagicMock(title="Section 1", subtopics=[MagicMock(content="Section content")])
        mock_conclusion.return_value = MagicMock(title="Conclusion", subtopics=[MagicMock(content="Conclusion content")])
        mock_faqs.return_value = MagicMock(title="FAQ", subtopics=[MagicMock(title="Q1", content="A1")])
        mock_meta.return_value = MagicMock(content="Meta description")
        
        # Call the function
        result = generate_blog_post_with_research(
            title="Test Blog",
            keywords=["test", "blog"],
            num_sections=1,
            include_faqs=True
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Blog")
        self.assertEqual(result.tags, ["test", "blog"])
        
        # Verify mocks were called
        mock_provider.assert_called_once()
        mock_research.assert_called_once()
        mock_outline.assert_called_once()
        mock_intro.assert_called_once()
        mock_section.assert_called_once()
        mock_conclusion.assert_called_once()
        mock_faqs.assert_called_once()
        mock_meta.assert_called_once()

    @patch('src.blog.make_blog.proofread_content')
    @patch('src.blog.make_blog.humanize_content')
    def test_post_process_blog_post(self, mock_humanize, mock_proofread):
        """Test the post_process_blog_post function."""
        # Set up mocks
        mock_proofread.return_value = MagicMock(corrected_text="Corrected content")
        mock_humanize.return_value = "Humanized content"
        
        # Call the function
        result = post_process_blog_post(
            blog_post=self.sample_blog_post,
            proofread=True,
            humanize=True
        )
        
        # Assertions
        self.assertEqual(result.title, self.sample_blog_post.title)
        self.assertEqual(result.tags, self.sample_blog_post.tags)
        self.assertEqual(len(result.sections), len(self.sample_blog_post.sections))
        
        # Verify mocks were called
        self.assertEqual(mock_proofread.call_count, 4)  # Once for each subtopic
        self.assertEqual(mock_humanize.call_count, 4)  # Once for each subtopic

    def test_save_and_load_blog_post(self):
        """Test saving and loading a blog post to/from JSON."""
        # Create a temporary file path
        temp_file = "temp_blog_post.json"
        
        try:
            # Save the blog post
            save_blog_post_to_json(self.sample_blog_post, temp_file)
            
            # Verify the file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Load the blog post
            loaded_post = load_blog_post_from_json(temp_file)
            
            # Assertions
            self.assertEqual(loaded_post.title, self.sample_blog_post.title)
            self.assertEqual(loaded_post.description, self.sample_blog_post.description)
            self.assertEqual(len(loaded_post.sections), len(self.sample_blog_post.sections))
            self.assertEqual(loaded_post.tags, self.sample_blog_post.tags)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
