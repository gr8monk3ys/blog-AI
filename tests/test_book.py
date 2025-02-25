"""
Tests for the book module.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.book.make_book import (
    generate_book,
    generate_book_with_research,
    generate_chapter,
    generate_introduction_chapter,
    generate_conclusion_chapter,
    post_process_book,
    save_book_to_markdown,
    save_book_to_json,
    load_book_from_json
)
from src.types.content import Book, Chapter, Section, SubTopic


class TestBookModule(unittest.TestCase):
    """Test cases for the book module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample book for testing
        from src.types.content import Topic
        
        self.sample_book = Book(
            title="Test Book",
            chapters=[
                Chapter(
                    number=0,
                    title="Introduction",
                    topics=[
                        Topic(
                            title="Introduction",
                            content="This is the introduction content."
                        )
                    ]
                ),
                Chapter(
                    number=1,
                    title="Chapter 1",
                    topics=[
                        Topic(
                            title="Introduction",
                            content="Chapter 1 introduction."
                        ),
                        Topic(
                            title="Section 1",
                            content="This is section 1 content."
                        ),
                        Topic(
                            title="Conclusion",
                            content="Chapter 1 conclusion."
                        )
                    ]
                ),
                Chapter(
                    number=2,
                    title="Conclusion",
                    topics=[
                        Topic(
                            title="Conclusion",
                            content="This is the conclusion content."
                        )
                    ]
                )
            ]
        )

    @patch('src.book.make_book.create_provider_from_env')
    @patch('src.book.make_book.generate_topic_clusters')
    @patch('src.book.make_book.generate_chapter')
    @patch('src.book.make_book.generate_introduction_chapter')
    @patch('src.book.make_book.generate_conclusion_chapter')
    def test_generate_book(self, mock_conclusion_chapter, mock_intro_chapter, 
                          mock_chapter, mock_clusters, mock_provider):
        """Test the generate_book function."""
        # Set up mocks
        mock_provider.return_value = MagicMock()
        mock_clusters.return_value = [
            MagicMock(main_topic="Chapter 1", subtopics=["Section 1", "Section 2"], keywords=["key1", "key2"])
        ]
        mock_chapter.return_value = MagicMock(title="Chapter 1", topics=[MagicMock()])
        mock_intro_chapter.return_value = MagicMock(title="Introduction", topics=[MagicMock()])
        mock_conclusion_chapter.return_value = MagicMock(title="Conclusion", topics=[MagicMock()])
        
        # Call the function
        result = generate_book(
            title="Test Book",
            num_chapters=1,
            sections_per_chapter=2,
            keywords=["test", "book"]
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Book")
        self.assertEqual(result.tags, ["test", "book"])
        self.assertEqual(len(result.chapters), 3)  # Intro, Chapter, Conclusion
        
        # Verify mocks were called
        mock_provider.assert_called_once()
        mock_clusters.assert_called_once()
        mock_chapter.assert_called_once()
        mock_intro_chapter.assert_called_once()
        mock_conclusion_chapter.assert_called_once()

    @patch('src.book.make_book.create_provider_from_env')
    @patch('src.book.make_book.conduct_web_research')
    @patch('src.book.make_book.generate_topic_clusters_with_research')
    @patch('src.book.make_book.generate_chapter_with_research')
    @patch('src.book.make_book.generate_introduction_chapter_with_research')
    @patch('src.book.make_book.generate_conclusion_chapter')
    def test_generate_book_with_research(self, mock_conclusion, mock_intro, 
                                        mock_chapter, mock_clusters, 
                                        mock_research, mock_provider):
        """Test the generate_book_with_research function."""
        # Set up mocks
        mock_provider.return_value = MagicMock()
        mock_research.return_value = MagicMock()
        mock_clusters.return_value = [
            MagicMock(main_topic="Chapter 1", subtopics=["Section 1", "Section 2"], keywords=["key1", "key2"])
        ]
        mock_chapter.return_value = MagicMock(title="Chapter 1", topics=[MagicMock()])
        mock_intro.return_value = MagicMock(title="Introduction", topics=[MagicMock()])
        mock_conclusion.return_value = MagicMock(title="Conclusion", topics=[MagicMock()])
        
        # Call the function
        result = generate_book_with_research(
            title="Test Book",
            num_chapters=1,
            sections_per_chapter=2,
            keywords=["test", "book"]
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Book")
        self.assertEqual(result.tags, ["test", "book"])
        self.assertEqual(len(result.chapters), 3)  # Intro, Chapter, Conclusion
        
        # Verify mocks were called
        mock_provider.assert_called_once()
        mock_research.assert_called_once()
        mock_clusters.assert_called_once()
        mock_chapter.assert_called_once()
        mock_intro.assert_called_once()
        mock_conclusion.assert_called_once()

    @patch('src.book.make_book.generate_introduction_section')
    @patch('src.book.make_book.generate_section')
    @patch('src.book.make_book.generate_conclusion_section')
    def test_generate_chapter(self, mock_conclusion, mock_section, mock_intro):
        """Test the generate_chapter function."""
        # Set up mocks
        mock_intro.return_value = MagicMock(title="Introduction", subtopics=[MagicMock()])
        mock_section.return_value = MagicMock(title="Section 1", subtopics=[MagicMock()])
        mock_conclusion.return_value = MagicMock(title="Conclusion", subtopics=[MagicMock()])
        
        # Call the function
        result = generate_chapter(
            title="Test Chapter",
            subtopics=["Section 1", "Section 2"],
            keywords=["test", "chapter"]
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Chapter")
        self.assertEqual(len(result.topics), 4)  # Intro, 2 Sections, Conclusion
        
        # Verify mocks were called
        mock_intro.assert_called_once()
        self.assertEqual(mock_section.call_count, 2)
        mock_conclusion.assert_called_once()

    @patch('src.book.make_book.generate_text')
    def test_generate_introduction_chapter(self, mock_generate_text):
        """Test the generate_introduction_chapter function."""
        # Set up mocks
        mock_generate_text.return_value = "Introduction content"
        
        # Create sample chapters
        chapters = [
            MagicMock(title="Chapter 1"),
            MagicMock(title="Chapter 2")
        ]
        
        # Call the function
        result = generate_introduction_chapter(
            title="Test Book",
            chapters=chapters,
            keywords=["test", "book"]
        )
        
        # Assertions
        self.assertEqual(result.title, "Introduction")
        self.assertEqual(len(result.topics), 1)
        self.assertEqual(result.topics[0].title, "Introduction")
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    @patch('src.book.make_book.proofread_content')
    @patch('src.book.make_book.humanize_content')
    def test_post_process_book(self, mock_humanize, mock_proofread):
        """Test the post_process_book function."""
        # Set up mocks
        mock_proofread.return_value = MagicMock(corrected_text="Corrected content")
        mock_humanize.return_value = "Humanized content"
        
        # Call the function
        result = post_process_book(
            book=self.sample_book,
            proofread=True,
            humanize=True
        )
        
        # Assertions
        self.assertEqual(result.title, self.sample_book.title)
        self.assertEqual(result.tags, self.sample_book.tags)
        self.assertEqual(len(result.chapters), len(self.sample_book.chapters))
        
        # Count the number of topics in the book
        topic_count = sum(
            len(chapter.topics) 
            for chapter in self.sample_book.chapters
        )
        
        # Verify mocks were called
        self.assertEqual(mock_proofread.call_count, topic_count)
        self.assertEqual(mock_humanize.call_count, topic_count)

    def test_save_and_load_book(self):
        """Test saving and loading a book to/from JSON."""
        # Create a temporary file path
        temp_file = "temp_book.json"
        
        try:
            # Save the book
            save_book_to_json(self.sample_book, temp_file)
            
            # Verify the file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Load the book
            loaded_book = load_book_from_json(temp_file)
            
            # Assertions
            self.assertEqual(loaded_book.title, self.sample_book.title)
            self.assertEqual(len(loaded_book.chapters), len(self.sample_book.chapters))
            self.assertEqual(loaded_book.tags, self.sample_book.tags)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == '__main__':
    unittest.main()
