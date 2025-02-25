"""
Competitor analysis functionality.
"""
import os
import json
from typing import List, Dict, Any, Optional

from ..text_generation.core import generate_text, LLMProvider, GenerationOptions
from ..types.planning import (
    Competitor,
    CompetitorContent,
    CompetitorAnalysisResult,
    ContentTopic
)
from ..research.web_researcher import conduct_web_research


class CompetitorAnalysisError(Exception):
    """Exception raised for errors in the competitor analysis process."""
    pass


def analyze_competitors(
    niche: str,
    competitors: List[str],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> CompetitorAnalysisResult:
    """
    Analyze competitors in a specific niche.
    
    Args:
        niche: The niche to analyze competitors for.
        competitors: The competitors to analyze.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The competitor analysis result.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during analysis.
    """
    try:
        # Analyze each competitor
        competitor_objects = []
        
        for competitor_name in competitors:
            # Get competitor website
            website = get_competitor_website(competitor_name, provider, options)
            
            # Get competitor content
            content = get_competitor_content(competitor_name, website, provider, options)
            
            # Create competitor object
            competitor = Competitor(
                name=competitor_name,
                website=website,
                content=content
            )
            
            competitor_objects.append(competitor)
        
        # Analyze common keywords
        common_keywords = analyze_common_keywords(competitor_objects, provider, options)
        
        # Identify content gaps
        content_gaps = identify_content_gaps(niche, competitor_objects, provider, options)
        
        # Generate recommendations
        recommendations = generate_recommendations(niche, competitor_objects, common_keywords, content_gaps, provider, options)
        
        return CompetitorAnalysisResult(
            competitors=competitor_objects,
            common_keywords=common_keywords,
            content_gaps=content_gaps,
            recommendations=recommendations
        )
    except Exception as e:
        raise CompetitorAnalysisError(f"Error analyzing competitors: {str(e)}")


def get_competitor_website(
    competitor_name: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> str:
    """
    Get the website of a competitor.
    
    Args:
        competitor_name: The name of the competitor.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The competitor's website.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during retrieval.
    """
    try:
        # Conduct web research
        research_results = conduct_web_research([competitor_name, "website"])
        
        # Create prompt for website extraction
        prompt = f"""
        Based on the following research, what is the official website of {competitor_name}?
        
        {str(research_results)[:2000]}...
        
        Return only the website URL, nothing else.
        """
        
        # Generate website
        website = generate_text(prompt, provider, options)
        
        # Clean up the website
        website = website.strip()
        
        # Ensure website starts with http:// or https://
        if not website.startswith("http://") and not website.startswith("https://"):
            website = "https://" + website
        
        return website
    except Exception as e:
        raise CompetitorAnalysisError(f"Error getting competitor website: {str(e)}")


def get_competitor_content(
    competitor_name: str,
    website: str,
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[CompetitorContent]:
    """
    Get the content of a competitor.
    
    Args:
        competitor_name: The name of the competitor.
        website: The website of the competitor.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The competitor's content.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during retrieval.
    """
    try:
        # Conduct web research
        research_results = conduct_web_research([competitor_name, "blog", "content"])
        
        # Create prompt for content extraction
        prompt = f"""
        Based on the following research, identify 5-10 pieces of content (blog posts, articles, etc.) from {competitor_name} ({website}).
        
        {str(research_results)[:2000]}...
        
        For each piece of content, provide:
        1. The title
        2. The URL (if available)
        3. The content type (blog post, article, video, etc.)
        4. 3-5 keywords that describe the content
        
        Return your response in the following format:
        
        Content 1:
        Title: [Title]
        URL: [URL]
        Content Type: [Content Type]
        Keywords: [keyword1, keyword2, keyword3]
        
        Content 2:
        Title: [Title]
        URL: [URL]
        Content Type: [Content Type]
        Keywords: [keyword1, keyword2, keyword3]
        
        And so on.
        """
        
        # Generate content
        content_text = generate_text(prompt, provider, options)
        
        # Parse the content
        content_objects = []
        
        current_title = None
        current_url = None
        current_content_type = None
        current_keywords = None
        
        lines = content_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Content "):
                # Save previous content if it exists
                if current_title and current_url and current_content_type and current_keywords:
                    content_objects.append(
                        CompetitorContent(
                            title=current_title,
                            url=current_url,
                            content_type=current_content_type,
                            keywords=current_keywords
                        )
                    )
                
                # Reset current content
                current_title = None
                current_url = None
                current_content_type = None
                current_keywords = None
            elif line.startswith("Title:"):
                current_title = line[6:].strip()
            elif line.startswith("URL:"):
                current_url = line[4:].strip()
            elif line.startswith("Content Type:"):
                current_content_type = line[13:].strip()
            elif line.startswith("Keywords:"):
                keywords_text = line[9:].strip()
                current_keywords = [k.strip() for k in keywords_text.split(",")]
        
        # Add the last content if it exists
        if current_title and current_url and current_content_type and current_keywords:
            content_objects.append(
                CompetitorContent(
                    title=current_title,
                    url=current_url,
                    content_type=current_content_type,
                    keywords=current_keywords
                )
            )
        
        return content_objects
    except Exception as e:
        raise CompetitorAnalysisError(f"Error getting competitor content: {str(e)}")


def analyze_common_keywords(
    competitors: List[Competitor],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[str]:
    """
    Analyze common keywords among competitors.
    
    Args:
        competitors: The competitors to analyze.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The common keywords.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during analysis.
    """
    try:
        # Extract all keywords from competitor content
        all_keywords = []
        
        for competitor in competitors:
            for content in competitor.content:
                all_keywords.extend(content.keywords)
        
        # Create prompt for keyword analysis
        prompt = f"""
        Analyze the following keywords from competitor content and identify the most common themes or topics:
        
        {", ".join(all_keywords)}
        
        Return a list of 10-15 common keywords or themes that appear frequently across the competitors.
        
        Return your response as a comma-separated list of keywords, nothing else.
        """
        
        # Generate common keywords
        keywords_text = generate_text(prompt, provider, options)
        
        # Parse the keywords
        keywords = [k.strip() for k in keywords_text.split(",")]
        
        return keywords
    except Exception as e:
        raise CompetitorAnalysisError(f"Error analyzing common keywords: {str(e)}")


def identify_content_gaps(
    niche: str,
    competitors: List[Competitor],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[str]:
    """
    Identify content gaps among competitors.
    
    Args:
        niche: The niche to identify content gaps for.
        competitors: The competitors to analyze.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The content gaps.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during identification.
    """
    try:
        # Extract all content titles from competitor content
        all_titles = []
        
        for competitor in competitors:
            for content in competitor.content:
                all_titles.append(content.title)
        
        # Create prompt for content gap analysis
        prompt = f"""
        Analyze the following content titles from competitors in the {niche} niche:
        
        {", ".join(all_titles)}
        
        Identify 5-10 potential content gaps or topics that are not being covered by these competitors but would be valuable for the audience in this niche.
        
        Return your response as a comma-separated list of content gap topics, nothing else.
        """
        
        # Generate content gaps
        gaps_text = generate_text(prompt, provider, options)
        
        # Parse the gaps
        gaps = [g.strip() for g in gaps_text.split(",")]
        
        return gaps
    except Exception as e:
        raise CompetitorAnalysisError(f"Error identifying content gaps: {str(e)}")


def generate_recommendations(
    niche: str,
    competitors: List[Competitor],
    common_keywords: List[str],
    content_gaps: List[str],
    provider: Optional[LLMProvider] = None,
    options: Optional[GenerationOptions] = None
) -> List[str]:
    """
    Generate recommendations based on competitor analysis.
    
    Args:
        niche: The niche to generate recommendations for.
        competitors: The competitors analyzed.
        common_keywords: The common keywords identified.
        content_gaps: The content gaps identified.
        provider: The LLM provider to use.
        options: Options for text generation.
        
    Returns:
        The recommendations.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during generation.
    """
    try:
        # Create prompt for recommendation generation
        prompt = f"""
        Based on the analysis of competitors in the {niche} niche, generate 5-10 strategic recommendations for content creation and marketing.
        
        Competitor Information:
        {", ".join([c.name for c in competitors])}
        
        Common Keywords:
        {", ".join(common_keywords)}
        
        Content Gaps:
        {", ".join(content_gaps)}
        
        Return your recommendations as a numbered list, with each recommendation being a concise, actionable item.
        """
        
        # Generate recommendations
        recommendations_text = generate_text(prompt, provider, options)
        
        # Parse the recommendations
        recommendations = []
        
        lines = recommendations_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering if present
            if line[0].isdigit() and line[1] == "." and line[2] == " ":
                line = line[3:]
            
            recommendations.append(line.strip())
        
        return recommendations
    except Exception as e:
        raise CompetitorAnalysisError(f"Error generating recommendations: {str(e)}")


def save_competitor_analysis_to_json(
    analysis: CompetitorAnalysisResult,
    file_path: str
) -> None:
    """
    Save a competitor analysis to a JSON file.
    
    Args:
        analysis: The competitor analysis to save.
        file_path: The path to save the analysis to.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during saving.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Convert analysis to JSON-serializable format
        analysis_data = {
            "competitors": [],
            "common_keywords": analysis.common_keywords,
            "content_gaps": analysis.content_gaps,
            "recommendations": analysis.recommendations
        }
        
        for competitor in analysis.competitors:
            competitor_data = {
                "name": competitor.name,
                "website": competitor.website,
                "content": []
            }
            
            for content in competitor.content:
                content_data = {
                    "title": content.title,
                    "url": content.url,
                    "content_type": content.content_type,
                    "keywords": content.keywords
                }
                
                if content.published_date:
                    content_data["published_date"] = content.published_date.strftime("%Y-%m-%d")
                
                competitor_data["content"].append(content_data)
            
            analysis_data["competitors"].append(competitor_data)
        
        # Write analysis to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2)
    except Exception as e:
        raise CompetitorAnalysisError(f"Error saving competitor analysis to JSON: {str(e)}")


def load_competitor_analysis_from_json(
    file_path: str
) -> CompetitorAnalysisResult:
    """
    Load a competitor analysis from a JSON file.
    
    Args:
        file_path: The path to load the analysis from.
        
    Returns:
        The loaded competitor analysis.
        
    Raises:
        CompetitorAnalysisError: If an error occurs during loading.
    """
    try:
        # Read analysis from JSON
        with open(file_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        # Convert JSON data to CompetitorAnalysisResult
        competitors = []
        
        for competitor_data in analysis_data["competitors"]:
            content = []
            
            for content_data in competitor_data["content"]:
                content_item = CompetitorContent(
                    title=content_data["title"],
                    url=content_data["url"],
                    content_type=content_data["content_type"],
                    keywords=content_data["keywords"]
                )
                
                content.append(content_item)
            
            competitor = Competitor(
                name=competitor_data["name"],
                website=competitor_data["website"],
                content=content
            )
            
            competitors.append(competitor)
        
        return CompetitorAnalysisResult(
            competitors=competitors,
            common_keywords=analysis_data["common_keywords"],
            content_gaps=analysis_data["content_gaps"],
            recommendations=analysis_data["recommendations"]
        )
    except Exception as e:
        raise CompetitorAnalysisError(f"Error loading competitor analysis from JSON: {str(e)}")
