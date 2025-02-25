"""
Web research functionality.
"""
import os
from typing import List, Dict, Any, Optional

from ..types.research import (
    SearchOptions,
    ResearchResults,
    GoogleSerpResult,
    TavilySearchResult,
    MetaphorResult,
    GoogleTrendsResult,
    SearchResult,
    PeopleAlsoAsk,
    RelatedSearch,
    TavilyResult,
    TrendPoint
)


class ResearchError(Exception):
    """Exception raised for errors in the research process."""
    pass


def conduct_web_research(
    keywords: List[str],
    options: Optional[SearchOptions] = None
) -> ResearchResults:
    """
    Conduct web research using multiple sources.
    
    Args:
        keywords: The keywords to research.
        options: Options for the search.
        
    Returns:
        The research results.
        
    Raises:
        ResearchError: If an error occurs during research.
    """
    options = options or SearchOptions()
    
    try:
        # Convert keywords list to a string for searching
        search_query = " ".join(keywords)
        
        # Conduct research using different sources
        google_results = google_serp_search(search_query, options)
        tavily_results = tavily_ai_search(search_query, options)
        metaphor_results = metaphor_ai_search(search_query, options)
        trends_results = google_trends_analysis(keywords, options)
        
        # Combine results
        return ResearchResults(
            google=google_results,
            tavily=tavily_results,
            metaphor=metaphor_results,
            trends=trends_results
        )
    except Exception as e:
        raise ResearchError(f"Error conducting web research: {str(e)}")


def google_serp_search(
    query: str,
    options: SearchOptions
) -> Optional[GoogleSerpResult]:
    """
    Search using Google SERP API.
    
    Args:
        query: The search query.
        options: Options for the search.
        
    Returns:
        The search results.
        
    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests
        
        api_key = os.environ.get("SERP_API_KEY")
        if not api_key:
            raise ResearchError("SERP_API_KEY environment variable not set")
        
        url = "https://serpapi.com/search"
        
        params = {
            "api_key": api_key,
            "q": query,
            "location": options.location,
            "hl": options.language,
            "num": options.num_results,
            "tbm": "search",
            "tbs": f"qdr:{options.time_range}" if options.time_range != "anytime" else ""
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organic results
        organic_results = []
        for result in data.get("organic_results", []):
            organic_results.append(
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", "")
                )
            )
        
        # Extract "People Also Ask" questions
        paa_results = []
        for paa in data.get("related_questions", []):
            paa_results.append(
                PeopleAlsoAsk(
                    question=paa.get("question", ""),
                    answer=paa.get("answer", "")
                )
            )
        
        # Extract related searches
        related_searches = []
        for related in data.get("related_searches", []):
            related_searches.append(
                RelatedSearch(
                    query=related.get("query", "")
                )
            )
        
        return GoogleSerpResult(
            organic=organic_results,
            people_also_ask=paa_results,
            related_searches=related_searches
        )
    except ImportError:
        raise ResearchError("Requests package not installed. Install it with 'pip install requests'.")
    except Exception as e:
        raise ResearchError(f"Error searching with Google SERP: {str(e)}")


def tavily_ai_search(
    query: str,
    options: SearchOptions
) -> Optional[TavilySearchResult]:
    """
    Search using Tavily AI.
    
    Args:
        query: The search query.
        options: Options for the search.
        
    Returns:
        The search results.
        
    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests
        
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ResearchError("TAVILY_API_KEY environment variable not set")
        
        url = "https://api.tavily.com/search"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "query": query,
            "search_depth": "advanced",
            "max_results": options.num_results,
            "include_answer": True,
            "include_domains": options.include_domains,
            "include_raw_content": False,
            "include_images": False
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract results
        tavily_results = []
        for item in result.get("results", []):
            tavily_results.append(
                TavilyResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", "")
                )
            )
        
        return TavilySearchResult(
            results=tavily_results,
            answer=result.get("answer", ""),
            follow_up_questions=result.get("follow_up_questions", [])
        )
    except ImportError:
        raise ResearchError("Requests package not installed. Install it with 'pip install requests'.")
    except Exception as e:
        raise ResearchError(f"Error searching with Tavily AI: {str(e)}")


def metaphor_ai_search(
    query: str,
    options: SearchOptions
) -> Optional[List[MetaphorResult]]:
    """
    Search using Metaphor AI.
    
    Args:
        query: The search query.
        options: Options for the search.
        
    Returns:
        The search results.
        
    Raises:
        ResearchError: If an error occurs during search.
    """
    try:
        import requests
        
        api_key = os.environ.get("METAPHOR_API_KEY")
        if not api_key:
            raise ResearchError("METAPHOR_API_KEY environment variable not set")
        
        url = "https://api.metaphor.systems/search"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        
        data = {
            "query": query,
            "numResults": options.num_results,
            "useAutoprompt": True
        }
        
        if options.similar_url:
            data["type"] = "neural"
            data["url"] = options.similar_url
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract results
        metaphor_results = []
        for item in result.get("results", []):
            # Get content for each result
            content_url = f"https://api.metaphor.systems/contents"
            content_data = {
                "ids": [item.get("id")]
            }
            
            content_response = requests.post(content_url, headers=headers, json=content_data)
            content_response.raise_for_status()
            
            content_result = content_response.json()
            content = content_result.get("contents", [{}])[0].get("extract", "")
            
            metaphor_results.append(
                MetaphorResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    text=content
                )
            )
        
        return metaphor_results
    except ImportError:
        raise ResearchError("Requests package not installed. Install it with 'pip install requests'.")
    except Exception as e:
        raise ResearchError(f"Error searching with Metaphor AI: {str(e)}")


def google_trends_analysis(
    keywords: List[str],
    options: SearchOptions
) -> Optional[GoogleTrendsResult]:
    """
    Analyze trends using Google Trends.
    
    Args:
        keywords: The keywords to analyze.
        options: Options for the analysis.
        
    Returns:
        The analysis results.
        
    Raises:
        ResearchError: If an error occurs during analysis.
    """
    try:
        from pytrends.request import TrendReq
        
        # Use the first keyword for trends analysis
        keyword = keywords[0] if keywords else ""
        
        if not keyword:
            return None
        
        # Initialize pytrends
        pytrends = TrendReq(hl=options.language, geo=options.location.upper())
        
        # Build payload
        pytrends.build_payload([keyword], timeframe="today 12-m")
        
        # Get interest over time
        interest_over_time = pytrends.interest_over_time()
        
        # Get related topics
        related_topics = pytrends.related_topics()
        
        # Get related queries
        related_queries = pytrends.related_queries()
        
        # Extract timeline data
        timeline = []
        if not interest_over_time.empty:
            for date, row in interest_over_time.iterrows():
                timeline.append(
                    TrendPoint(
                        date=date.strftime("%Y-%m-%d"),
                        value=float(row[keyword])
                    )
                )
        
        # Extract related topics
        topics = []
        if keyword in related_topics:
            for _, row in related_topics[keyword]["top"].iterrows():
                topics.append(row["topic_title"])
        
        # Extract related queries
        queries = []
        if keyword in related_queries:
            for _, row in related_queries[keyword]["top"].iterrows():
                queries.append(row["query"])
        
        return GoogleTrendsResult(
            keyword=keyword,
            timeline=timeline,
            related_topics=topics,
            related_queries=queries
        )
    except ImportError:
        raise ResearchError("Pytrends package not installed. Install it with 'pip install pytrends'.")
    except Exception as e:
        raise ResearchError(f"Error analyzing with Google Trends: {str(e)}")
