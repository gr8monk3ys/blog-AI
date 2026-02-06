"""
AI-powered recommendation engine for content analytics.

This engine provides:
- Content topic recommendations based on performance
- Optimal posting time suggestions
- Format recommendations (blog vs social vs email)
- Keyword opportunity detection
"""

import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types.performance import (
    ContentFormat,
    ContentPerformance,
    ContentRecommendation,
    FormatRecommendation,
    PerformanceTimeRange,
    RecommendationType,
    TimingRecommendation,
    TopicRecommendation,
)

logger = logging.getLogger(__name__)


class RecommendationEngineError(Exception):
    """Exception raised for errors in the recommendation engine."""

    pass


class RecommendationEngine:
    """
    AI-powered engine for generating content recommendations.

    This engine analyzes historical performance data to generate
    actionable recommendations for content strategy.
    """

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
        min_data_points: int = 5,
    ):
        """
        Initialize the recommendation engine.

        Args:
            supabase_client: Optional Supabase client for data access.
            llm_provider: Optional LLM provider for AI-powered insights.
            min_data_points: Minimum data points needed for recommendations.
        """
        self._supabase = supabase_client
        self._llm_provider = llm_provider
        self._min_data_points = min_data_points

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

    # =========================================================================
    # Topic Recommendations
    # =========================================================================

    async def get_topic_recommendations(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[TopicRecommendation]:
        """
        Get topic recommendations based on historical performance.

        Args:
            organization_id: Optional organization filter.
            user_id: Optional user filter.
            limit: Maximum recommendations to return.

        Returns:
            List of TopicRecommendation objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return self._get_default_topic_recommendations(limit)

        try:
            # Get high-performing content
            query = supabase.table("content_performance").select(
                "content_id, title, content_type, views, shares, conversions, metadata"
            ).order("views", desc=True).limit(50)

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data or len(result.data) < self._min_data_points:
                return self._get_default_topic_recommendations(limit)

            # Analyze topics from high-performing content
            topic_scores = self._analyze_topics(result.data)

            # Get existing topics to avoid duplicates
            existing_topics = {item.get("title", "").lower() for item in result.data}

            # Generate recommendations
            recommendations = []
            for topic, score_data in sorted(
                topic_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True,
            )[:limit]:
                if topic.lower() in existing_topics:
                    continue

                rec = TopicRecommendation(
                    recommendation_type=RecommendationType.TOPIC,
                    title=f"Create content about: {topic}",
                    description=f"Based on your top-performing content, this topic shows high potential. "
                    f"Related content has averaged {score_data['avg_views']:.0f} views.",
                    confidence=min(score_data["score"] / 100, 1.0),
                    priority=len(recommendations) + 1,
                    topic=topic,
                    related_keywords=score_data.get("keywords", []),
                    estimated_traffic=int(score_data["avg_views"] * 0.8),
                    competition_level=self._estimate_competition(score_data),
                    based_on=score_data.get("content_ids", []),
                )
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get topic recommendations: {e}")
            return self._get_default_topic_recommendations(limit)

    def _analyze_topics(self, content_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze topics from content data."""
        topic_scores = defaultdict(lambda: {
            "score": 0,
            "count": 0,
            "total_views": 0,
            "total_shares": 0,
            "avg_views": 0,
            "keywords": [],
            "content_ids": [],
        })

        for item in content_data:
            # Extract topics from title and metadata
            title = item.get("title", "")
            metadata = item.get("metadata", {}) or {}
            keywords = metadata.get("keywords", [])
            tags = metadata.get("tags", [])

            # Simple topic extraction from title
            topics = self._extract_topics_from_title(title)
            topics.extend(keywords[:3])
            topics.extend(tags[:3])

            views = item.get("views", 0)
            shares = item.get("shares", 0)
            content_id = item.get("content_id")

            for topic in topics:
                if not topic or len(topic) < 3:
                    continue

                topic = topic.strip().lower()
                data = topic_scores[topic]
                data["count"] += 1
                data["total_views"] += views
                data["total_shares"] += shares
                data["score"] += views + (shares * 10)  # Weight shares higher
                data["content_ids"].append(content_id)

        # Calculate averages
        for topic, data in topic_scores.items():
            if data["count"] > 0:
                data["avg_views"] = data["total_views"] / data["count"]

        return dict(topic_scores)

    def _extract_topics_from_title(self, title: str) -> List[str]:
        """Extract potential topics from a title."""
        if not title:
            return []

        # Remove common words and extract key phrases
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "how",
            "what", "when", "where", "why", "which", "who", "whom", "this",
            "that", "these", "those", "your", "our", "my", "their", "its",
        }

        words = title.lower().split()
        topics = []

        # Extract individual important words
        for word in words:
            word = word.strip(",.!?;:\"'()-")
            if len(word) >= 4 and word not in stop_words:
                topics.append(word)

        # Extract bigrams
        for i in range(len(words) - 1):
            w1 = words[i].strip(",.!?;:\"'()-")
            w2 = words[i + 1].strip(",.!?;:\"'()-")
            if w1 not in stop_words and w2 not in stop_words:
                topics.append(f"{w1} {w2}")

        return topics[:5]

    def _estimate_competition(self, score_data: Dict[str, Any]) -> str:
        """Estimate competition level for a topic."""
        avg_views = score_data.get("avg_views", 0)
        count = score_data.get("count", 0)

        # Simple heuristic based on existing content
        if avg_views > 1000 and count > 3:
            return "high"
        elif avg_views > 500 or count > 2:
            return "medium"
        return "low"

    def _get_default_topic_recommendations(self, limit: int) -> List[TopicRecommendation]:
        """Return default topic recommendations when data is insufficient."""
        defaults = [
            ("AI and Machine Learning Trends", ["ai", "machine learning", "automation"]),
            ("Content Marketing Strategies", ["content marketing", "seo", "engagement"]),
            ("Productivity Tips", ["productivity", "efficiency", "workflow"]),
            ("Industry Best Practices", ["best practices", "tips", "guide"]),
            ("Future of Technology", ["technology", "innovation", "trends"]),
        ]

        recommendations = []
        for i, (topic, keywords) in enumerate(defaults[:limit]):
            recommendations.append(
                TopicRecommendation(
                    recommendation_type=RecommendationType.TOPIC,
                    title=f"Create content about: {topic}",
                    description="This topic consistently performs well across the industry.",
                    confidence=0.6,
                    priority=i + 1,
                    topic=topic,
                    related_keywords=keywords,
                    competition_level="medium",
                )
            )

        return recommendations

    # =========================================================================
    # Timing Recommendations
    # =========================================================================

    async def get_timing_recommendations(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> List[TimingRecommendation]:
        """
        Get optimal posting time recommendations.

        Args:
            organization_id: Optional organization filter.
            user_id: Optional user filter.
            content_type: Optional content type filter.

        Returns:
            List of TimingRecommendation objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return self._get_default_timing_recommendations()

        try:
            # Get content with performance data
            query = supabase.table("content_performance").select(
                "content_id, views, shares, published_at, metadata"
            ).not_.is_("published_at", "null")

            if organization_id:
                query = query.eq("organization_id", organization_id)
            if user_id:
                query = query.eq("user_id", user_id)
            if content_type:
                query = query.eq("content_type", content_type)

            result = query.execute()

            if not result.data or len(result.data) < self._min_data_points:
                return self._get_default_timing_recommendations()

            # Analyze performance by day and hour
            timing_data = self._analyze_timing(result.data)

            # Generate recommendations
            recommendations = []

            # Best day recommendation
            best_day = max(timing_data["by_day"].items(), key=lambda x: x[1]["avg_engagement"])
            recommendations.append(
                TimingRecommendation(
                    recommendation_type=RecommendationType.TIMING,
                    title=f"Publish on {best_day[0].capitalize()}",
                    description=f"Content published on {best_day[0]} shows "
                    f"{best_day[1]['avg_engagement']:.0f}% higher engagement.",
                    confidence=min(best_day[1]["count"] / 10, 0.9),
                    priority=1,
                    day_of_week=best_day[0],
                    hour_utc=timing_data["best_hour"],
                    expected_engagement_boost=best_day[1]["avg_engagement"],
                )
            )

            # Best hour recommendation
            best_hour = timing_data["best_hour"]
            hour_data = timing_data["by_hour"].get(best_hour, {})
            recommendations.append(
                TimingRecommendation(
                    recommendation_type=RecommendationType.TIMING,
                    title=f"Post at {best_hour}:00 UTC",
                    description=f"Content posted at this time receives "
                    f"{hour_data.get('avg_views', 0):.0f} average views.",
                    confidence=min(hour_data.get("count", 0) / 10, 0.85),
                    priority=2,
                    day_of_week="",
                    hour_utc=best_hour,
                    expected_engagement_boost=hour_data.get("avg_engagement", 0),
                )
            )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get timing recommendations: {e}")
            return self._get_default_timing_recommendations()

    def _analyze_timing(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content performance by timing."""
        by_day = defaultdict(lambda: {"count": 0, "total_views": 0, "total_shares": 0})
        by_hour = defaultdict(lambda: {"count": 0, "total_views": 0, "total_shares": 0})

        for item in content_data:
            published_at = item.get("published_at")
            if not published_at:
                continue

            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            day = dt.strftime("%A").lower()
            hour = dt.hour
            views = item.get("views", 0)
            shares = item.get("shares", 0)

            by_day[day]["count"] += 1
            by_day[day]["total_views"] += views
            by_day[day]["total_shares"] += shares

            by_hour[hour]["count"] += 1
            by_hour[hour]["total_views"] += views
            by_hour[hour]["total_shares"] += shares

        # Calculate averages and engagement scores
        for data in by_day.values():
            if data["count"] > 0:
                data["avg_views"] = data["total_views"] / data["count"]
                data["avg_engagement"] = (data["avg_views"] + data["total_shares"] * 10) / data["count"]

        for data in by_hour.values():
            if data["count"] > 0:
                data["avg_views"] = data["total_views"] / data["count"]
                data["avg_engagement"] = (data["avg_views"] + data["total_shares"] * 10) / data["count"]

        # Find best hour
        best_hour = 9  # Default
        if by_hour:
            best_hour = max(by_hour.items(), key=lambda x: x[1].get("avg_views", 0))[0]

        return {
            "by_day": dict(by_day),
            "by_hour": dict(by_hour),
            "best_hour": best_hour,
        }

    def _get_default_timing_recommendations(self) -> List[TimingRecommendation]:
        """Return default timing recommendations."""
        return [
            TimingRecommendation(
                recommendation_type=RecommendationType.TIMING,
                title="Publish on Tuesday",
                description="Tuesday is statistically one of the best days for content engagement.",
                confidence=0.7,
                priority=1,
                day_of_week="tuesday",
                hour_utc=9,
                expected_engagement_boost=15.0,
            ),
            TimingRecommendation(
                recommendation_type=RecommendationType.TIMING,
                title="Post at 9:00 AM UTC",
                description="Morning posts tend to get higher initial engagement.",
                confidence=0.65,
                priority=2,
                day_of_week="",
                hour_utc=9,
                expected_engagement_boost=12.0,
            ),
        ]

    # =========================================================================
    # Format Recommendations
    # =========================================================================

    async def get_format_recommendations(
        self,
        content_id: Optional[str] = None,
        topic: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> List[FormatRecommendation]:
        """
        Get content format recommendations.

        Args:
            content_id: Optional specific content to analyze.
            topic: Optional topic to recommend formats for.
            organization_id: Optional organization filter.

        Returns:
            List of FormatRecommendation objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return self._get_default_format_recommendations()

        try:
            # Analyze performance by content type
            query = supabase.table("content_performance").select(
                "content_type, views, shares, conversions"
            )

            if organization_id:
                query = query.eq("organization_id", organization_id)

            result = query.execute()

            if not result.data or len(result.data) < self._min_data_points:
                return self._get_default_format_recommendations()

            # Calculate performance by format
            format_performance = defaultdict(lambda: {
                "count": 0,
                "total_views": 0,
                "total_shares": 0,
                "total_conversions": 0,
            })

            for item in result.data:
                content_type = item.get("content_type", "blog")
                format_performance[content_type]["count"] += 1
                format_performance[content_type]["total_views"] += item.get("views", 0)
                format_performance[content_type]["total_shares"] += item.get("shares", 0)
                format_performance[content_type]["total_conversions"] += item.get("conversions", 0)

            # Calculate averages
            for data in format_performance.values():
                if data["count"] > 0:
                    data["avg_views"] = data["total_views"] / data["count"]
                    data["avg_shares"] = data["total_shares"] / data["count"]
                    data["score"] = data["avg_views"] + data["avg_shares"] * 5

            # Sort by score and generate recommendations
            sorted_formats = sorted(
                format_performance.items(),
                key=lambda x: x[1].get("score", 0),
                reverse=True,
            )

            recommendations = []
            for i, (format_type, data) in enumerate(sorted_formats[:3]):
                try:
                    content_format = ContentFormat(format_type)
                except ValueError:
                    content_format = ContentFormat.BLOG

                recommendations.append(
                    FormatRecommendation(
                        recommendation_type=RecommendationType.FORMAT,
                        title=f"Create {format_type.capitalize()} content",
                        description=f"{format_type.capitalize()} content averages "
                        f"{data['avg_views']:.0f} views and {data['avg_shares']:.0f} shares.",
                        confidence=min(data["count"] / 20, 0.9),
                        priority=i + 1,
                        recommended_format=content_format,
                        transformation_suggestions=self._get_format_suggestions(content_format),
                    )
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get format recommendations: {e}")
            return self._get_default_format_recommendations()

    def _get_format_suggestions(self, content_format: ContentFormat) -> List[str]:
        """Get suggestions for a content format."""
        suggestions = {
            ContentFormat.BLOG: [
                "Include code examples and tutorials",
                "Add relevant images and diagrams",
                "Structure with clear headings",
            ],
            ContentFormat.SOCIAL: [
                "Keep posts concise and scannable",
                "Use hashtags strategically",
                "Include a clear call-to-action",
            ],
            ContentFormat.EMAIL: [
                "Write compelling subject lines",
                "Personalize the opening",
                "Include one primary CTA",
            ],
            ContentFormat.VIDEO: [
                "Hook viewers in the first 10 seconds",
                "Add captions for accessibility",
                "Include chapter markers",
            ],
            ContentFormat.PODCAST: [
                "Create detailed show notes",
                "Include timestamps for topics",
                "Cross-promote on other channels",
            ],
            ContentFormat.INFOGRAPHIC: [
                "Focus on one key insight",
                "Use data visualization",
                "Make it shareable",
            ],
        }
        return suggestions.get(content_format, [])

    def _get_default_format_recommendations(self) -> List[FormatRecommendation]:
        """Return default format recommendations."""
        return [
            FormatRecommendation(
                recommendation_type=RecommendationType.FORMAT,
                title="Create Blog content",
                description="Blog posts are foundational for SEO and thought leadership.",
                confidence=0.8,
                priority=1,
                recommended_format=ContentFormat.BLOG,
                transformation_suggestions=self._get_format_suggestions(ContentFormat.BLOG),
            ),
            FormatRecommendation(
                recommendation_type=RecommendationType.FORMAT,
                title="Repurpose to Social media",
                description="Social content extends reach and engagement.",
                confidence=0.75,
                priority=2,
                recommended_format=ContentFormat.SOCIAL,
                transformation_suggestions=self._get_format_suggestions(ContentFormat.SOCIAL),
            ),
        ]

    # =========================================================================
    # Keyword Recommendations
    # =========================================================================

    async def get_keyword_opportunities(
        self,
        organization_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[ContentRecommendation]:
        """
        Get keyword opportunity recommendations.

        Args:
            organization_id: Optional organization filter.
            limit: Maximum recommendations to return.

        Returns:
            List of ContentRecommendation objects.
        """
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            # Get rankings with improvement potential
            query = supabase.table("seo_rankings").select("*").gte("position", 11).lte("position", 30)

            if organization_id:
                query = query.eq("organization_id", organization_id)

            query = query.order("search_volume", desc=True).limit(limit)
            result = query.execute()

            recommendations = []
            seen_keywords = set()

            for record in (result.data or []):
                keyword = record.get("keyword")
                if not keyword or keyword in seen_keywords:
                    continue
                seen_keywords.add(keyword)

                position = record.get("position", 0)
                search_volume = record.get("search_volume", 0)

                # Calculate potential impact
                potential = self._calculate_keyword_potential(position, search_volume)

                recommendations.append(
                    ContentRecommendation(
                        recommendation_type=RecommendationType.KEYWORD,
                        title=f"Optimize for: {keyword}",
                        description=f"Currently ranking #{position}. "
                        f"Moving to page 1 could bring {potential:.0f} more visits/month.",
                        confidence=min(0.5 + (30 - position) / 40, 0.9),
                        priority=len(recommendations) + 1,
                        data={
                            "keyword": keyword,
                            "current_position": position,
                            "search_volume": search_volume,
                            "potential_traffic": potential,
                        },
                    )
                )

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get keyword opportunities: {e}")
            return []

    def _calculate_keyword_potential(self, position: int, search_volume: int) -> float:
        """Calculate potential traffic gain from ranking improvement."""
        if search_volume == 0:
            return 0.0

        # CTR estimates
        current_ctr = 0.01 if position > 10 else 0.10 / position
        target_ctr = 0.30  # Position 1 CTR

        return search_volume * (target_ctr - current_ctr)

    # =========================================================================
    # Aggregate Recommendations
    # =========================================================================

    async def get_all_recommendations(
        self,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit_per_type: int = 3,
    ) -> List[ContentRecommendation]:
        """
        Get all types of recommendations.

        Args:
            organization_id: Optional organization filter.
            user_id: Optional user filter.
            limit_per_type: Maximum recommendations per type.

        Returns:
            List of all ContentRecommendation objects.
        """
        all_recommendations = []

        # Get topic recommendations
        topic_recs = await self.get_topic_recommendations(
            organization_id=organization_id,
            user_id=user_id,
            limit=limit_per_type,
        )
        all_recommendations.extend(topic_recs)

        # Get timing recommendations
        timing_recs = await self.get_timing_recommendations(
            organization_id=organization_id,
            user_id=user_id,
        )
        all_recommendations.extend(timing_recs[:limit_per_type])

        # Get format recommendations
        format_recs = await self.get_format_recommendations(
            organization_id=organization_id,
        )
        all_recommendations.extend(format_recs[:limit_per_type])

        # Get keyword opportunities
        keyword_recs = await self.get_keyword_opportunities(
            organization_id=organization_id,
            limit=limit_per_type,
        )
        all_recommendations.extend(keyword_recs)

        # Sort by priority and confidence
        all_recommendations.sort(key=lambda r: (r.priority, -r.confidence))

        # Store recommendations
        await self._store_recommendations(all_recommendations, organization_id, user_id)

        return all_recommendations

    async def _store_recommendations(
        self,
        recommendations: List[ContentRecommendation],
        organization_id: Optional[str],
        user_id: Optional[str],
    ) -> None:
        """Store recommendations in the database."""
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            # Delete old recommendations for this org/user
            delete_query = supabase.table("content_recommendations").delete()
            if organization_id:
                delete_query = delete_query.eq("organization_id", organization_id)
            if user_id:
                delete_query = delete_query.eq("user_id", user_id)
            delete_query.execute()

            # Insert new recommendations
            for rec in recommendations:
                data = {
                    "recommendation_type": rec.recommendation_type.value,
                    "title": rec.title,
                    "description": rec.description,
                    "confidence": rec.confidence,
                    "priority": rec.priority,
                    "data": rec.data,
                    "based_on": rec.based_on,
                    "organization_id": organization_id,
                    "user_id": user_id,
                    "created_at": rec.created_at.isoformat(),
                    "expires_at": rec.expires_at.isoformat() if rec.expires_at else None,
                }
                supabase.table("content_recommendations").insert(data).execute()

        except Exception as e:
            logger.error(f"Failed to store recommendations: {e}")
