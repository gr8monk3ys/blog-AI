"""
Content calendar generation functionality.
"""
import os
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.planning import (
    ContentTopic,
    ContentItem,
    ContentCalendar,
    TimeframeType,
    PlanningOptions
)
from ..research.web_researcher import conduct_web_research


class ContentCalendarError(Exception):
    """Exception raised for errors in the content calendar generation process."""
    pass


def generate_content_calendar(
    niche: str,
    timeframe: TimeframeType = "month",
    content_types: Optional[List[str]] = None,
    frequency: int = 1,
    start_date: Optional[datetime] = None,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> ContentCalendar:
    """
    Generate a content calendar for a specific niche.
    
    Args:
        niche: The niche to generate content for.
        timeframe: The timeframe for the content calendar.
        content_types: The types of content to include in the calendar.
        frequency: The frequency of content publication.
        start_date: The start date for the content calendar.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated content calendar.
        
    Raises:
        ContentCalendarError: If an error occurs during generation.
    """
    try:
        # Set default values
        content_types = content_types or ["blog"]
        start_date = start_date or datetime.now()
        
        # Calculate end date based on timeframe
        if timeframe == "week":
            end_date = start_date + timedelta(days=7)
            num_items = 7 // frequency
        elif timeframe == "month":
            end_date = start_date + timedelta(days=30)
            num_items = 30 // frequency
        elif timeframe == "quarter":
            end_date = start_date + timedelta(days=90)
            num_items = 90 // frequency
        elif timeframe == "year":
            end_date = start_date + timedelta(days=365)
            num_items = 365 // frequency
        else:
            raise ContentCalendarError(f"Invalid timeframe: {timeframe}")
        
        # Generate content topics
        topics = generate_content_topics(niche, num_items, provider, options)
        
        # Create content items
        items = []
        current_date = start_date
        
        for i, topic in enumerate(topics):
            # Calculate publication date
            if timeframe == "week":
                pub_date = start_date + timedelta(days=i * frequency)
            elif timeframe == "month":
                pub_date = start_date + timedelta(days=i * frequency)
            elif timeframe == "quarter":
                pub_date = start_date + timedelta(days=i * frequency)
            elif timeframe == "year":
                pub_date = start_date + timedelta(days=i * frequency)
            
            # Ensure publication date is within the timeframe
            if pub_date > end_date:
                break
            
            # Determine content type
            if len(content_types) == 1:
                content_type = content_types[0]
            else:
                content_type = content_types[i % len(content_types)]
            
            # Create content item
            item = ContentItem(
                topic=topic,
                date=pub_date,
                content_type=content_type,
                status="planned"
            )
            
            items.append(item)
        
        return ContentCalendar(
            items=items,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise ContentCalendarError(f"Error generating content calendar: {str(e)}")


def generate_content_topics(
    niche: str,
    num_topics: int,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[ContentTopic]:
    """
    Generate content topics for a specific niche.
    
    Args:
        niche: The niche to generate topics for.
        num_topics: The number of topics to generate.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated content topics.
        
    Raises:
        ContentCalendarError: If an error occurs during generation.
    """
    try:
        # Create prompt for topic generation
        prompt = f"""
        Generate {num_topics} content topics for a {niche} blog or website.
        
        For each topic, provide:
        1. A compelling title
        2. 3-5 relevant keywords
        3. A brief description (1-2 sentences)
        
        Return your response in the following format:
        
        Topic 1:
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        Topic 2:
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        And so on.
        """
        
        # Generate topics
        topics_text = generate_text(prompt, provider, options)
        
        # Parse the topics
        topics = []
        
        current_title = None
        current_keywords = None
        current_description = None
        
        lines = topics_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Topic "):
                # Save previous topic if it exists
                if current_title and current_keywords:
                    topics.append(
                        ContentTopic(
                            title=current_title,
                            keywords=current_keywords,
                            description=current_description
                        )
                    )
                
                # Reset current topic
                current_title = None
                current_keywords = None
                current_description = None
            elif line.startswith("Title:"):
                current_title = line[6:].strip()
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
            elif line.startswith("Description:"):
                current_description = line[12:].strip()
        
        # Add the last topic if it exists
        if current_title and current_keywords:
            topics.append(
                ContentTopic(
                    title=current_title,
                    keywords=current_keywords,
                    description=current_description
                )
            )
        
        return topics[:num_topics]
    except Exception as e:
        raise ContentCalendarError(f"Error generating content topics: {str(e)}")


def generate_content_topics_with_research(
    niche: str,
    num_topics: int,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[ContentTopic]:
    """
    Generate content topics for a specific niche using web research.
    
    Args:
        niche: The niche to generate topics for.
        num_topics: The number of topics to generate.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The generated content topics.
        
    Raises:
        ContentCalendarError: If an error occurs during generation.
    """
    try:
        # Conduct web research
        research_results = conduct_web_research([niche])
        
        # Create prompt for topic generation
        prompt = f"""
        Generate {num_topics} content topics for a {niche} blog or website based on the following research:
        
        {str(research_results)[:2000]}...
        
        For each topic, provide:
        1. A compelling title
        2. 3-5 relevant keywords
        3. A brief description (1-2 sentences)
        
        Return your response in the following format:
        
        Topic 1:
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        Topic 2:
        Title: [Title]
        Keywords: [keyword1, keyword2, keyword3]
        Description: [Description]
        
        And so on.
        """
        
        # Generate topics
        topics_text = generate_text(prompt, provider, options)
        
        # Parse the topics
        topics = []
        
        current_title = None
        current_keywords = None
        current_description = None
        
        lines = topics_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Topic "):
                # Save previous topic if it exists
                if current_title and current_keywords:
                    topics.append(
                        ContentTopic(
                            title=current_title,
                            keywords=current_keywords,
                            description=current_description
                        )
                    )
                
                # Reset current topic
                current_title = None
                current_keywords = None
                current_description = None
            elif line.startswith("Title:"):
                current_title = line[6:].strip()
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
            elif line.startswith("Description:"):
                current_description = line[12:].strip()
        
        # Add the last topic if it exists
        if current_title and current_keywords:
            topics.append(
                ContentTopic(
                    title=current_title,
                    keywords=current_keywords,
                    description=current_description
                )
            )
        
        return topics[:num_topics]
    except Exception as e:
        raise ContentCalendarError(f"Error generating content topics with research: {str(e)}")


def save_content_calendar_to_csv(
    calendar: ContentCalendar,
    file_path: str
) -> None:
    """
    Save a content calendar to a CSV file.
    
    Args:
        calendar: The content calendar to save.
        file_path: The path to save the calendar to.
        
    Raises:
        ContentCalendarError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write calendar to CSV
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Date", "Title", "Content Type", "Keywords", "Description", "Status"])
            
            # Write items
            for item in calendar.items:
                writer.writerow([
                    item.date.strftime("%Y-%m-%d"),
                    item.topic.title,
                    item.content_type,
                    ", ".join(item.topic.keywords),
                    item.topic.description or "",
                    item.status
                ])
    except Exception as e:
        raise ContentCalendarError(f"Error saving content calendar to CSV: {str(e)}")


def save_content_calendar_to_json(
    calendar: ContentCalendar,
    file_path: str
) -> None:
    """
    Save a content calendar to a JSON file.
    
    Args:
        calendar: The content calendar to save.
        file_path: The path to save the calendar to.
        
    Raises:
        ContentCalendarError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Convert calendar to JSON-serializable format
        calendar_data = {
            "start_date": calendar.start_date.strftime("%Y-%m-%d"),
            "end_date": calendar.end_date.strftime("%Y-%m-%d"),
            "items": []
        }
        
        for item in calendar.items:
            calendar_data["items"].append({
                "date": item.date.strftime("%Y-%m-%d"),
                "title": item.topic.title,
                "content_type": item.content_type,
                "keywords": item.topic.keywords,
                "description": item.topic.description,
                "status": item.status,
                "assigned_to": item.assigned_to
            })
        
        # Write calendar to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(calendar_data, f, indent=2)
    except Exception as e:
        raise ContentCalendarError(f"Error saving content calendar to JSON: {str(e)}")


def load_content_calendar_from_json(
    file_path: str
) -> ContentCalendar:
    """
    Load a content calendar from a JSON file.
    
    Args:
        file_path: The path to load the calendar from.
        
    Returns:
        The loaded content calendar.
        
    Raises:
        ContentCalendarError: If an error occurs during loading.
    """
    try:
        # Read calendar from JSON
        with open(file_path, "r", encoding="utf-8") as f:
            calendar_data = json.load(f)
        
        # Convert JSON data to ContentCalendar
        items = []
        
        for item_data in calendar_data["items"]:
            topic = ContentTopic(
                title=item_data["title"],
                keywords=item_data["keywords"],
                description=item_data.get("description")
            )
            
            item = ContentItem(
                topic=topic,
                date=datetime.strptime(item_data["date"], "%Y-%m-%d"),
                content_type=item_data["content_type"],
                status=item_data["status"],
                assigned_to=item_data.get("assigned_to")
            )
            
            items.append(item)
        
        return ContentCalendar(
            items=items,
            start_date=datetime.strptime(calendar_data["start_date"], "%Y-%m-%d"),
            end_date=datetime.strptime(calendar_data["end_date"], "%Y-%m-%d")
        )
    except Exception as e:
        raise ContentCalendarError(f"Error loading content calendar from JSON: {str(e)}")
