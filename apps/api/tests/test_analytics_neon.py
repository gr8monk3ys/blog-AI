"""Integration tests for the Neon/asyncpg analytics services.

Skipped unless a reachable Postgres with the analytics tables is configured
(TEST_DATABASE_URL or DATABASE_URL). Exercises the real asyncpg query path of
performance_service, seo_tracker, dashboard_service, and recommendation_engine.
"""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _reachable_db_url():
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        return None
    try:
        import asyncpg

        async def _check():
            conn = await asyncpg.connect(dsn=url, statement_cache_size=0)
            try:
                return await conn.fetchval(
                    "SELECT to_regclass('public.content_performance')"
                )
            finally:
                await conn.close()

        return url if asyncio.run(_check()) else None
    except Exception:
        return None


_DB_URL = _reachable_db_url()


@unittest.skipUnless(_DB_URL, "no reachable Postgres with analytics tables")
class AnalyticsNeonBase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._saved = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = _DB_URL
        self.cid = f"an-{os.getpid()}-{id(self)}"
        from src.db import get_pool

        self.pool = await get_pool()
        await self._cleanup()

    async def asyncTearDown(self):
        await self._cleanup()
        from src.db import close_pool

        await close_pool()
        if self._saved is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._saved

    async def _cleanup(self):
        # Only these tables key off content_id; content_recommendations uses a
        # based_on text[] instead, and the tests don't write it.
        async with self.pool.acquire() as conn:
            for tbl in (
                "performance_events",
                "performance_snapshots",
                "content_performance",
                "seo_rankings",
            ):
                await conn.execute(f"DELETE FROM {tbl} WHERE content_id = $1", self.cid)


class TestPerformanceServiceNeon(AnalyticsNeonBase):
    async def test_track_event_accumulates_and_reads_back(self):
        from src.analytics.performance_service import PerformanceService
        from src.types.performance import MetricType, PerformanceEvent

        svc = PerformanceService()
        self.assertTrue(
            await svc.track_event(
                PerformanceEvent(
                    content_id=self.cid, event_type=MetricType.VIEW, value=1
                )
            )
        )
        perf1 = await svc.get_content_performance(self.cid)
        self.assertIsNotNone(perf1)
        self.assertGreater(perf1.views, 0)
        await svc.track_event(
            PerformanceEvent(content_id=self.cid, event_type=MetricType.VIEW, value=1)
        )
        perf2 = await svc.get_content_performance(self.cid)
        self.assertGreater(perf2.views, perf1.views)  # accumulates

    async def test_snapshot_and_summary(self):
        from src.analytics.performance_service import PerformanceService
        from src.types.performance import (
            MetricType,
            PerformanceEvent,
            PerformanceTimeRange,
        )

        svc = PerformanceService()
        await svc.track_event(
            PerformanceEvent(content_id=self.cid, event_type=MetricType.VIEW, value=1)
        )
        snap = await svc.create_daily_snapshot(self.cid)
        self.assertIsNotNone(snap)
        summary = await svc.get_performance_summary(
            time_range=PerformanceTimeRange.WEEK, use_cache=False
        )
        self.assertGreaterEqual(summary.total_content_items, 1)


class TestSeoTrackerNeon(AnalyticsNeonBase):
    async def test_ranking_history_round_trip(self):
        from src.analytics.neon_query import NeonQueryClient
        from src.analytics.seo_tracker import SEOTracker

        # Insert a ranking row directly through the adapter (avoids the SERP API).
        client = NeonQueryClient()
        await client.table("seo_rankings").insert(
            {
                "keyword": "neon testing",
                "position": 4,
                "content_id": self.cid,
                "url": "https://example.com/x",
                "search_engine": "google",
                "location": "us",
            }
        ).execute()

        tracker = SEOTracker(api_key="x")  # api_key only needed for live SERP calls
        history = await tracker.get_ranking_history(keyword="neon testing", days=30)
        self.assertTrue(any(r.position == 4 for r in history))
        by_content = await tracker.get_content_rankings(self.cid, days=30)
        self.assertTrue(any(r.keyword == "neon testing" for r in by_content))


class TestDashboardAndRecommendationsNeon(AnalyticsNeonBase):
    async def test_dashboard_and_recommendation_reads(self):
        from src.analytics.dashboard_service import DashboardService
        from src.analytics.performance_service import PerformanceService
        from src.analytics.recommendation_engine import RecommendationEngine
        from src.types.performance import (
            MetricType,
            PerformanceEvent,
            PerformanceTimeRange,
        )

        ps = PerformanceService()
        await ps.track_event(
            PerformanceEvent(content_id=self.cid, event_type=MetricType.VIEW, value=1)
        )

        dashboard = await DashboardService().get_dashboard_data(
            time_range=PerformanceTimeRange.WEEK
        )
        self.assertIsNotNone(dashboard)  # builds without error against real DB

        recs = await RecommendationEngine().get_topic_recommendations(limit=5)
        self.assertIsInstance(recs, list)


if __name__ == "__main__":
    unittest.main()
