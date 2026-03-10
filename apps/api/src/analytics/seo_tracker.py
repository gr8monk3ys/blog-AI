"""
SEO tracking service for content analytics.

This service handles:
- Keyword ranking tracking via SERP API
- Ranking history and trend analysis
- Competitor ranking comparison
- Keyword opportunity detection
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from ..types.performance import (
    SEOAnalysis,
    SEORanking,
    TrendDirection,
)

logger = logging.getLogger(__name__)


class SEOTrackerError(Exception):
    """Exception raised for errors in SEO tracking."""

    pass


class SEOTracker:
    """
    Service for tracking SEO rankings and performance.

    This service integrates with SERP API to track keyword rankings
    and provides analysis of SEO performance over time.
    """

    SERP_API_BASE_URL = "https://serpapi.com/search"

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_client: Optional[Any] = None,
        default_location: str = "United States",
        default_language: str = "en",
    ):
        """
        Initialize the SEO tracker.

        Args:
            api_key: SERP API key (falls back to SERP_API_KEY env var).
            supabase_client: Optional Supabase client for storage.
            default_location: Default search location.
            default_language: Default search language.
        """
        self._api_key = api_key or os.environ.get("SERP_API_KEY")
        self._supabase = supabase_client
        self._default_location = default_location
        self._default_language = default_language

    def _get_supabase(self) -> Optional[Any]:
        """Get or create Supabase client."""
        if self._supabase is not None:
            return self._supabase

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

        if not supabase_url or not supabase_key:
            return None

        try:
            from supabase import create_client

            self._supabase = create_client(supabase_url, supabase_key)
            return self._supabase
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            return None

    @property
    def is_configured(self) -> bool:
        """Check if the SEO tracker is properly configured."""
        return bool(self._api_key)

    # =========================================================================
    # Keyword Ranking Tracking
    # =========================================================================

    def check_keyword_ranking(
        self,
        keyword: str,
        target_url: str,
        location: Optional[str] = None,
        language: Optional[str] = None,
        search_engine: str = "google",
    ) -> Optional[SEORanking]:
        """
        Check the ranking position for a keyword.

        Args:
            keyword: The keyword to check.
            target_url: The URL to find in search results.
            location: Search location (default: United States).
            language: Search language (default: en).
            search_engine: Search engine to use (default: google).

        Returns:
            SEORanking object or None if not found.

        Raises:
            SEOTrackerError: If the API call fails.
        """
        if not self._api_key:
            raise SEOTrackerError("SERP API key not configured")

        try:
            params = {
                "api_key": self._api_key,
                "q": keyword,
                "location": location or self._default_location,
                "hl": language or self._default_language,
                "num": 100,  # Check top 100 results
                "engine": search_engine,
            }

            response = requests.get(self.SERP_API_BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Find the target URL in organic results
            organic_results = data.get("organic_results", [])
            position = None
            found_url = None

            # Normalize target URL for comparison
            target_domain = self._extract_domain(target_url)

            for i, result in enumerate(organic_results, start=1):
                result_url = result.get("link", "")
                result_domain = self._extract_domain(result_url)

                # Check for exact URL match or domain match
                if target_url in result_url or target_domain == result_domain:
                    position = i
                    found_url = result_url
                    break

            if position is None:
                # Not found in top 100
                return SEORanking(
                    keyword=keyword,
                    position=0,  # 0 indicates not found
                    url=None,
                    search_engine=search_engine,
                    location=location or self._default_location,
                )

            # Get previous ranking for comparison
            previous_ranking = self._get_previous_ranking(keyword, target_url)
            previous_position = previous_ranking.position if previous_ranking else None
            change = (previous_position - position) if previous_position else 0

            # Get search volume if available
            search_volume = self._get_search_volume(keyword)

            ranking = SEORanking(
                keyword=keyword,
                position=position,
                previous_position=previous_position,
                change=change,
                search_volume=search_volume,
                url=found_url,
                search_engine=search_engine,
                location=location or self._default_location,
            )

            # Store the ranking
            self._store_ranking(ranking, target_url)

            return ranking

        except requests.Timeout:
            raise SEOTrackerError(f"SERP API request timed out for keyword: {keyword}")
        except requests.RequestException as e:
            raise SEOTrackerError(f"SERP API request failed: {str(e)}")
        except Exception as e:
            raise SEOTrackerError(f"Error checking keyword ranking: {str(e)}")

    def track_multiple_keywords(
        self,
        keywords: List[str],
        target_url: str,
        location: Optional[str] = None,
    ) -> List[SEORanking]:
        """
        Track rankings for multiple keywords.

        Args:
            keywords: List of keywords to track.
            target_url: The URL to find in search results.
            location: Search location.

        Returns:
            List of SEORanking objects.
        """
        rankings = []

        for keyword in keywords:
            try:
                ranking = self.check_keyword_ranking(
                    keyword=keyword,
                    target_url=target_url,
                    location=location,
                )
                if ranking:
                    rankings.append(ranking)
            except SEOTrackerError as e:
                logger.warning(f"Failed to track keyword '{keyword}': {e}")
                continue

        return rankings

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return url.lower()

    def _get_previous_ranking(
        self,
        keyword: str,
        target_url: str,
    ) -> Optional[SEORanking]:
        """Get the most recent previous ranking for a keyword."""
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            result = (
                supabase.table("seo_rankings")
                .select("*")
                .eq("keyword", keyword)
                .eq("url", target_url)
                .order("tracked_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                record = result.data[0]
                return SEORanking(
                    keyword=record["keyword"],
                    position=record["position"],
                    previous_position=record.get("previous_position"),
                    change=record.get("change", 0),
                    search_volume=record.get("search_volume"),
                    url=record.get("url"),
                    tracked_at=datetime.fromisoformat(record["tracked_at"]),
                    search_engine=record.get("search_engine", "google"),
                    location=record.get("location", "us"),
                )
        except Exception as e:
            logger.error(f"Failed to get previous ranking: {e}")

        return None

    def _store_ranking(self, ranking: SEORanking, target_url: str) -> None:
        """Store a ranking in the database."""
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            data = {
                "keyword": ranking.keyword,
                "position": ranking.position,
                "previous_position": ranking.previous_position,
                "change": ranking.change,
                "search_volume": ranking.search_volume,
                "difficulty": ranking.difficulty,
                "url": target_url,
                "tracked_at": ranking.tracked_at.isoformat(),
                "search_engine": ranking.search_engine,
                "location": ranking.location,
            }

            supabase.table("seo_rankings").insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to store ranking: {e}")

    def _get_search_volume(self, keyword: str) -> Optional[int]:
        """
        Get estimated search volume for a keyword.

        Note: This requires additional API calls to keyword tools.
        Returns None if not available.
        """
        # This would integrate with a keyword research tool
        # For now, return None
        return None

    # =========================================================================
    # Ranking History
    # =========================================================================

    def get_ranking_history(
        self,
        keyword: str,
        target_url: Optional[str] = None,
        days: int = 30,
    ) -> List[SEORanking]:
        """
        Get ranking history for a keyword.

        Args:
            keyword: The keyword to get history for.
            target_url: Optional URL filter.
            days: Number of days of history.

        Returns:
            List of SEORanking objects ordered by date.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = (
                supabase.table("seo_rankings")
                .select("*")
                .eq("keyword", keyword)
                .gte("tracked_at", start_date.isoformat())
                .order("tracked_at", desc=True)
            )

            if target_url:
                query = query.eq("url", target_url)

            result = query.execute()

            rankings = []
            for record in (result.data or []):
                rankings.append(
                    SEORanking(
                        keyword=record["keyword"],
                        position=record["position"],
                        previous_position=record.get("previous_position"),
                        change=record.get("change", 0),
                        search_volume=record.get("search_volume"),
                        url=record.get("url"),
                        tracked_at=datetime.fromisoformat(record["tracked_at"]),
                        search_engine=record.get("search_engine", "google"),
                        location=record.get("location", "us"),
                    )
                )

            return rankings

        except Exception as e:
            logger.error(f"Failed to get ranking history: {e}")
            return []

    def get_content_rankings(
        self,
        content_id: str,
        days: int = 30,
    ) -> List[SEORanking]:
        """
        Get all keyword rankings for a content item.

        Args:
            content_id: The content identifier.
            days: Number of days of history.

        Returns:
            List of SEORanking objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                supabase.table("seo_rankings")
                .select("*")
                .eq("content_id", content_id)
                .gte("tracked_at", start_date.isoformat())
                .order("tracked_at", desc=True)
                .execute()
            )

            rankings = []
            for record in (result.data or []):
                rankings.append(
                    SEORanking(
                        keyword=record["keyword"],
                        position=record["position"],
                        previous_position=record.get("previous_position"),
                        change=record.get("change", 0),
                        search_volume=record.get("search_volume"),
                        content_id=record.get("content_id"),
                        url=record.get("url"),
                        tracked_at=datetime.fromisoformat(record["tracked_at"]),
                        search_engine=record.get("search_engine", "google"),
                        location=record.get("location", "us"),
                    )
                )

            return rankings

        except Exception as e:
            logger.error(f"Failed to get content rankings: {e}")
            return []

    # =========================================================================
    # Competitor Analysis
    # =========================================================================

    def compare_with_competitors(
        self,
        keyword: str,
        target_url: str,
        competitor_urls: List[str],
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare rankings with competitors.

        Args:
            keyword: The keyword to compare.
            target_url: The target URL.
            competitor_urls: List of competitor URLs.
            location: Search location.

        Returns:
            Dictionary with comparison data.
        """
        if not self._api_key:
            return {"error": "SERP API key not configured"}

        try:
            params = {
                "api_key": self._api_key,
                "q": keyword,
                "location": location or self._default_location,
                "hl": self._default_language,
                "num": 100,
            }

            response = requests.get(self.SERP_API_BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            organic_results = data.get("organic_results", [])

            # Build URL to position map
            rankings = {}
            target_domain = self._extract_domain(target_url)
            all_urls = [target_url] + competitor_urls

            for i, result in enumerate(organic_results, start=1):
                result_url = result.get("link", "")
                result_domain = self._extract_domain(result_url)

                for url in all_urls:
                    url_domain = self._extract_domain(url)
                    if url_domain == result_domain:
                        if url not in rankings:
                            rankings[url] = {
                                "position": i,
                                "title": result.get("title", ""),
                                "snippet": result.get("snippet", ""),
                                "url": result_url,
                            }
                        break

            # Calculate comparison metrics
            target_position = rankings.get(target_url, {}).get("position", 0)
            competitors_ahead = 0
            competitors_behind = 0

            for comp_url in competitor_urls:
                comp_position = rankings.get(comp_url, {}).get("position", 0)
                if comp_position > 0:
                    if comp_position < target_position or target_position == 0:
                        competitors_ahead += 1
                    else:
                        competitors_behind += 1

            return {
                "keyword": keyword,
                "target": {
                    "url": target_url,
                    "position": target_position,
                    "data": rankings.get(target_url),
                },
                "competitors": [
                    {
                        "url": url,
                        "position": rankings.get(url, {}).get("position", 0),
                        "data": rankings.get(url),
                    }
                    for url in competitor_urls
                ],
                "summary": {
                    "competitors_ahead": competitors_ahead,
                    "competitors_behind": competitors_behind,
                    "total_competitors": len(competitor_urls),
                },
            }

        except requests.RequestException as e:
            logger.error(f"Competitor comparison failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # Opportunity Detection
    # =========================================================================

    def detect_opportunities(
        self,
        content_id: str,
        min_position: int = 11,
        max_position: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Detect keyword ranking opportunities.

        Keywords ranking between positions 11-30 are opportunities
        for improvement to reach the first page.

        Args:
            content_id: The content identifier.
            min_position: Minimum position to consider.
            max_position: Maximum position to consider.

        Returns:
            List of opportunity dictionaries.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            # Get recent rankings for the content
            result = (
                supabase.table("seo_rankings")
                .select("*")
                .eq("content_id", content_id)
                .gte("position", min_position)
                .lte("position", max_position)
                .order("search_volume", desc=True)
                .limit(20)
                .execute()
            )

            opportunities = []
            seen_keywords = set()

            for record in (result.data or []):
                keyword = record["keyword"]
                if keyword in seen_keywords:
                    continue
                seen_keywords.add(keyword)

                opportunities.append({
                    "keyword": keyword,
                    "current_position": record["position"],
                    "search_volume": record.get("search_volume"),
                    "difficulty": record.get("difficulty"),
                    "potential_impact": self._calculate_impact(
                        record["position"],
                        record.get("search_volume", 0),
                    ),
                    "recommendation": self._get_improvement_recommendation(
                        record["position"],
                    ),
                })

            # Sort by potential impact
            opportunities.sort(key=lambda x: x.get("potential_impact", 0), reverse=True)

            return opportunities

        except Exception as e:
            logger.error(f"Failed to detect opportunities: {e}")
            return []

    def _calculate_impact(self, position: int, search_volume: int) -> float:
        """Calculate potential impact of improving a ranking."""
        if search_volume == 0:
            return 0.0

        # CTR estimates by position
        ctr_by_position = {
            1: 0.30, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05,
            6: 0.04, 7: 0.03, 8: 0.03, 9: 0.02, 10: 0.02,
        }

        current_ctr = ctr_by_position.get(position, 0.01)
        target_ctr = ctr_by_position.get(1, 0.30)  # Assume moving to position 1

        potential_traffic_gain = search_volume * (target_ctr - current_ctr)
        return max(0, potential_traffic_gain)

    def _get_improvement_recommendation(self, position: int) -> str:
        """Get recommendation for improving a ranking."""
        if position <= 5:
            return "Focus on featured snippet optimization"
        elif position <= 10:
            return "Improve content depth and add internal links"
        elif position <= 20:
            return "Build backlinks and optimize on-page SEO"
        else:
            return "Consider content refresh and keyword optimization"

    # =========================================================================
    # SEO Analysis
    # =========================================================================

    def analyze_content_seo(
        self,
        content_id: str,
        url: str,
        keywords: Optional[List[str]] = None,
    ) -> SEOAnalysis:
        """
        Perform comprehensive SEO analysis for content.

        Args:
            content_id: The content identifier.
            url: The content URL.
            keywords: Optional list of keywords to track.

        Returns:
            SEOAnalysis object.
        """
        rankings = []
        opportunities = []

        # Track provided keywords
        if keywords:
            for keyword in keywords:
                try:
                    ranking = self.check_keyword_ranking(keyword, url)
                    if ranking:
                        ranking.content_id = content_id
                        rankings.append(ranking)
                except SEOTrackerError as e:
                    logger.warning(f"Failed to check ranking for '{keyword}': {e}")

        # Get historical rankings
        historical_rankings = self.get_content_rankings(content_id)
        all_rankings = rankings + [r for r in historical_rankings if r.keyword not in [rk.keyword for rk in rankings]]

        # Calculate average position
        positions = [r.position for r in all_rankings if r.position > 0]
        avg_position = sum(positions) / len(positions) if positions else None

        # Get top keywords (those ranking in top 10)
        top_keywords = [r.keyword for r in all_rankings if 0 < r.position <= 10]

        # Detect opportunities
        opportunities = self.detect_opportunities(content_id)

        return SEOAnalysis(
            content_id=content_id,
            url=url,
            rankings=all_rankings,
            avg_position=avg_position,
            top_keywords=top_keywords,
            opportunities=[opp["keyword"] for opp in opportunities[:5]],
        )
