"""
Tests for the planning module.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.planning.content_calendar import (
    generate_content_calendar,
    generate_content_topics,
    generate_content_topics_with_research,
    save_content_calendar_to_json,
    load_content_calendar_from_json
)
from src.planning.competitor_analysis import (
    analyze_competitors,
    get_competitor_website,
    get_competitor_content,
    analyze_common_keywords,
    identify_content_gaps,
    generate_recommendations
)
from src.planning.topic_clusters import (
    generate_topic_clusters,
    generate_topic_clusters_with_research,
    generate_content_topics_from_cluster,
    visualize_topic_cluster
)
from src.planning.content_outline import (
    generate_content_outline,
    generate_detailed_content_outline,
    generate_content_outline_with_research,
    generate_content_outline_from_topic
)
from src.types.planning import (
    ContentCalendar,
    ContentTopic,
    ContentItem,
    CompetitorAnalysisResult,
    Competitor,
    CompetitorContent,
    TopicCluster,
    ContentOutline
)


class TestContentCalendar(unittest.TestCase):
    """Test cases for the content calendar module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample content calendar for testing
        self.sample_calendar = ContentCalendar(
            items=[
                ContentItem(
                    topic=ContentTopic(
                        title="Topic 1",
                        keywords=["key1", "key2"],
                        description="Description 1"
                    ),
                    date=datetime(2025, 3, 1),
                    content_type="blog",
                    status="planned"
                ),
                ContentItem(
                    topic=ContentTopic(
                        title="Topic 2",
                        keywords=["key3", "key4"],
                        description="Description 2"
                    ),
                    date=datetime(2025, 3, 8),
                    content_type="blog",
                    status="planned"
                )
            ],
            start_date=datetime(2025, 3, 1),
            end_date=datetime(2025, 3, 31)
        )

    @patch('src.planning.content_calendar.generate_content_topics')
    def test_generate_content_calendar(self, mock_generate_topics):
        """Test the generate_content_calendar function."""
        # Set up mocks
        mock_generate_topics.return_value = [
            ContentTopic(title="Topic 1", keywords=["key1", "key2"], description="Description 1"),
            ContentTopic(title="Topic 2", keywords=["key3", "key4"], description="Description 2")
        ]
        
        # Call the function
        result = generate_content_calendar(
            niche="test niche",
            timeframe="month",
            content_types=["blog"],
            frequency=7
        )
        
        # Assertions
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].topic.title, "Topic 1")
        self.assertEqual(result.items[1].topic.title, "Topic 2")
        self.assertEqual(result.items[0].content_type, "blog")
        self.assertEqual(result.items[1].content_type, "blog")
        
        # Verify mocks were called
        mock_generate_topics.assert_called_once()

    @patch('src.planning.content_calendar.generate_text')
    def test_generate_content_topics(self, mock_generate_text):
        """Test the generate_content_topics function."""
        # Set up mocks
        mock_generate_text.return_value = """
        Topic 1:
        Title: Test Topic 1
        Keywords: key1, key2, key3
        Description: This is a test topic.
        
        Topic 2:
        Title: Test Topic 2
        Keywords: key4, key5, key6
        Description: This is another test topic.
        """
        
        # Call the function
        result = generate_content_topics(
            niche="test niche",
            num_topics=2
        )
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Test Topic 1")
        self.assertEqual(result[0].keywords, ["key1", "key2", "key3"])
        self.assertEqual(result[0].description, "This is a test topic.")
        self.assertEqual(result[1].title, "Test Topic 2")
        self.assertEqual(result[1].keywords, ["key4", "key5", "key6"])
        self.assertEqual(result[1].description, "This is another test topic.")
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    def test_save_and_load_content_calendar(self):
        """Test saving and loading a content calendar to/from JSON."""
        # Create a temporary file path
        temp_file = "temp_calendar.json"
        
        try:
            # Save the calendar
            save_content_calendar_to_json(self.sample_calendar, temp_file)
            
            # Verify the file exists
            self.assertTrue(os.path.exists(temp_file))
            
            # Load the calendar
            loaded_calendar = load_content_calendar_from_json(temp_file)
            
            # Assertions
            self.assertEqual(len(loaded_calendar.items), len(self.sample_calendar.items))
            self.assertEqual(loaded_calendar.items[0].topic.title, self.sample_calendar.items[0].topic.title)
            self.assertEqual(loaded_calendar.items[1].topic.title, self.sample_calendar.items[1].topic.title)
            self.assertEqual(loaded_calendar.start_date.strftime("%Y-%m-%d"), 
                            self.sample_calendar.start_date.strftime("%Y-%m-%d"))
            self.assertEqual(loaded_calendar.end_date.strftime("%Y-%m-%d"), 
                            self.sample_calendar.end_date.strftime("%Y-%m-%d"))
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)


class TestCompetitorAnalysis(unittest.TestCase):
    """Test cases for the competitor analysis module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample competitor analysis result for testing
        self.sample_competitor = Competitor(
            name="Competitor 1",
            website="https://competitor1.com",
            content=[
                CompetitorContent(
                    title="Content 1",
                    url="https://competitor1.com/content1",
                    content_type="blog",
                    keywords=["key1", "key2"]
                ),
                CompetitorContent(
                    title="Content 2",
                    url="https://competitor1.com/content2",
                    content_type="blog",
                    keywords=["key3", "key4"]
                )
            ]
        )
        
        self.sample_analysis = CompetitorAnalysisResult(
            competitors=[self.sample_competitor],
            common_keywords=["key1", "key3"],
            content_gaps=["gap1", "gap2"],
            recommendations=["rec1", "rec2"]
        )

    @patch('src.planning.competitor_analysis.get_competitor_website')
    @patch('src.planning.competitor_analysis.get_competitor_content')
    @patch('src.planning.competitor_analysis.analyze_common_keywords')
    @patch('src.planning.competitor_analysis.identify_content_gaps')
    @patch('src.planning.competitor_analysis.generate_recommendations')
    def test_analyze_competitors(self, mock_recommendations, mock_gaps, 
                               mock_keywords, mock_content, mock_website):
        """Test the analyze_competitors function."""
        # Set up mocks
        mock_website.return_value = "https://competitor1.com"
        mock_content.return_value = [
            CompetitorContent(
                title="Content 1",
                url="https://competitor1.com/content1",
                content_type="blog",
                keywords=["key1", "key2"]
            )
        ]
        mock_keywords.return_value = ["key1", "key2"]
        mock_gaps.return_value = ["gap1", "gap2"]
        mock_recommendations.return_value = ["rec1", "rec2"]
        
        # Call the function
        result = analyze_competitors(
            niche="test niche",
            competitors=["Competitor 1"]
        )
        
        # Assertions
        self.assertEqual(len(result.competitors), 1)
        self.assertEqual(result.competitors[0].name, "Competitor 1")
        self.assertEqual(result.competitors[0].website, "https://competitor1.com")
        self.assertEqual(len(result.competitors[0].content), 1)
        self.assertEqual(result.common_keywords, ["key1", "key2"])
        self.assertEqual(result.content_gaps, ["gap1", "gap2"])
        self.assertEqual(result.recommendations, ["rec1", "rec2"])
        
        # Verify mocks were called
        mock_website.assert_called_once()
        mock_content.assert_called_once()
        mock_keywords.assert_called_once()
        mock_gaps.assert_called_once()
        mock_recommendations.assert_called_once()


class TestTopicClusters(unittest.TestCase):
    """Test cases for the topic clusters module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample topic cluster for testing
        self.sample_cluster = TopicCluster(
            main_topic="Main Topic",
            subtopics=["Subtopic 1", "Subtopic 2", "Subtopic 3"],
            keywords=["key1", "key2", "key3"]
        )

    @patch('src.planning.topic_clusters.generate_text')
    def test_generate_topic_clusters(self, mock_generate_text):
        """Test the generate_topic_clusters function."""
        # Set up mocks
        mock_generate_text.return_value = """
        Cluster 1:
        Main Topic: Main Topic 1
        Subtopics:
        - Subtopic 1.1
        - Subtopic 1.2
        - Subtopic 1.3
        Keywords: key1, key2, key3
        
        Cluster 2:
        Main Topic: Main Topic 2
        Subtopics:
        - Subtopic 2.1
        - Subtopic 2.2
        - Subtopic 2.3
        Keywords: key4, key5, key6
        """
        
        # Call the function
        result = generate_topic_clusters(
            niche="test niche",
            num_clusters=2,
            subtopics_per_cluster=3
        )
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].main_topic, "Main Topic 1")
        self.assertEqual(result[0].subtopics, ["Subtopic 1.1", "Subtopic 1.2", "Subtopic 1.3"])
        self.assertEqual(result[0].keywords, ["key1", "key2", "key3"])
        self.assertEqual(result[1].main_topic, "Main Topic 2")
        self.assertEqual(result[1].subtopics, ["Subtopic 2.1", "Subtopic 2.2", "Subtopic 2.3"])
        self.assertEqual(result[1].keywords, ["key4", "key5", "key6"])
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    @patch('src.planning.topic_clusters.generate_text')
    def test_generate_content_topics_from_cluster(self, mock_generate_text):
        """Test the generate_content_topics_from_cluster function."""
        # Set up mocks
        mock_generate_text.return_value = """
        Topic 1 (Main Topic):
        Title: Main Topic Title
        Keywords: key1, key2, key3
        Description: Main topic description.
        
        Topic 2 (Subtopic 1):
        Title: Subtopic 1 Title
        Keywords: key4, key5, key6
        Description: Subtopic 1 description.
        """
        
        # Call the function
        result = generate_content_topics_from_cluster(self.sample_cluster)
        
        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Main Topic Title")
        self.assertEqual(result[0].keywords, ["key1", "key2", "key3"])
        self.assertEqual(result[0].description, "Main topic description.")
        self.assertEqual(result[1].title, "Subtopic 1 Title")
        self.assertEqual(result[1].keywords, ["key4", "key5", "key6"])
        self.assertEqual(result[1].description, "Subtopic 1 description.")
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    def test_visualize_topic_cluster(self):
        """Test the visualize_topic_cluster function."""
        # Call the function
        result = visualize_topic_cluster(self.sample_cluster)
        
        # Assertions
        self.assertIn("graph TD", result)
        self.assertIn("main[Main Topic]", result)
        self.assertIn("sub1[Subtopic 1]", result)
        self.assertIn("sub2[Subtopic 2]", result)
        self.assertIn("sub3[Subtopic 3]", result)
        self.assertIn("main --> sub1", result)
        self.assertIn("main --> sub2", result)
        self.assertIn("main --> sub3", result)


class TestContentOutline(unittest.TestCase):
    """Test cases for the content outline module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample content outline for testing
        self.sample_outline = ContentOutline(
            title="Test Outline",
            sections=["Introduction", "Section 1", "Section 2", "Conclusion"],
            keywords=["key1", "key2", "key3"]
        )

    @patch('src.planning.content_outline.generate_text')
    def test_generate_content_outline(self, mock_generate_text):
        """Test the generate_content_outline function."""
        # Set up mocks
        mock_generate_text.return_value = """
        # Introduction
        
        # Section 1
        
        # Section 2
        
        # Conclusion
        """
        
        # Call the function
        result = generate_content_outline(
            title="Test Outline",
            keywords=["key1", "key2", "key3"],
            num_sections=2
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Outline")
        self.assertEqual(result.sections, ["Introduction", "Section 1", "Section 2", "Conclusion"])
        self.assertEqual(result.keywords, ["key1", "key2", "key3"])
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    @patch('src.planning.content_outline.generate_text')
    def test_generate_detailed_content_outline(self, mock_generate_text):
        """Test the generate_detailed_content_outline function."""
        # Set up mocks
        mock_generate_text.return_value = """
        # Introduction
        - Key point 1
        - Key point 2
        - Key point 3
        
        # Section 1
        - Key point 1
        - Key point 2
        - Key point 3
        
        # Conclusion
        - Key point 1
        - Key point 2
        """
        
        # Call the function
        result = generate_detailed_content_outline(
            title="Test Outline",
            keywords=["key1", "key2", "key3"],
            num_sections=1
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Outline")
        self.assertEqual(result.sections, ["Introduction", "Section 1", "Conclusion"])
        self.assertEqual(result.keywords, ["key1", "key2", "key3"])
        
        # Verify mocks were called
        mock_generate_text.assert_called_once()

    @patch('src.planning.content_outline.conduct_web_research')
    @patch('src.planning.content_outline.generate_text')
    def test_generate_content_outline_with_research(self, mock_generate_text, mock_research):
        """Test the generate_content_outline_with_research function."""
        # Set up mocks
        mock_research.return_value = MagicMock()
        mock_generate_text.return_value = """
        # Introduction
        
        # Section 1
        
        # Section 2
        
        # Conclusion
        """
        
        # Call the function
        result = generate_content_outline_with_research(
            title="Test Outline",
            keywords=["key1", "key2", "key3"],
            num_sections=2
        )
        
        # Assertions
        self.assertEqual(result.title, "Test Outline")
        self.assertEqual(result.sections, ["Introduction", "Section 1", "Section 2", "Conclusion"])
        self.assertEqual(result.keywords, ["key1", "key2", "key3"])
        
        # Verify mocks were called
        mock_research.assert_called_once()
        mock_generate_text.assert_called_once()


if __name__ == '__main__':
    unittest.main()
