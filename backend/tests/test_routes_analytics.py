"""
Tests for analytics endpoints.

Tests the /analytics/overview, /analytics/tools, /analytics/timeline,
and /analytics/categories endpoints.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set environment before imports
os.environ["DEV_MODE"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient


class TestAnalyticsOverview(unittest.TestCase):
    """Tests for /analytics/overview endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_overview_returns_200(self):
        """Overview endpoint should return 200."""
        response = self.client.get("/analytics/overview")
        self.assertEqual(response.status_code, 200)

    def test_overview_contains_required_fields(self):
        """Overview should contain required statistics fields."""
        response = self.client.get("/analytics/overview")
        data = response.json()

        self.assertIn("total_generations", data)
        self.assertIn("total_tools_used", data)
        self.assertIn("active_today", data)
        self.assertIn("average_execution_time_ms", data)

    def test_overview_has_numeric_values(self):
        """Overview statistics should have numeric values."""
        response = self.client.get("/analytics/overview")
        data = response.json()

        self.assertIsInstance(data["total_generations"], int)
        self.assertIsInstance(data["total_tools_used"], int)
        self.assertIsInstance(data["active_today"], int)
        self.assertIsInstance(data["average_execution_time_ms"], (int, float))

    def test_overview_with_time_range_7d(self):
        """Overview should accept 7d time range parameter."""
        response = self.client.get("/analytics/overview?range=7d")
        self.assertEqual(response.status_code, 200)

    def test_overview_with_time_range_30d(self):
        """Overview should accept 30d time range parameter."""
        response = self.client.get("/analytics/overview?range=30d")
        self.assertEqual(response.status_code, 200)

    def test_overview_with_time_range_90d(self):
        """Overview should accept 90d time range parameter."""
        response = self.client.get("/analytics/overview?range=90d")
        self.assertEqual(response.status_code, 200)


class TestAnalyticsToolUsage(unittest.TestCase):
    """Tests for /analytics/tools endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_tools_returns_200(self):
        """Tools endpoint should return 200."""
        response = self.client.get("/analytics/tools")
        self.assertEqual(response.status_code, 200)

    def test_tools_returns_list(self):
        """Tools endpoint should return a list."""
        response = self.client.get("/analytics/tools")
        data = response.json()
        self.assertIsInstance(data, list)

    def test_tool_item_contains_required_fields(self):
        """Each tool item should contain required fields."""
        response = self.client.get("/analytics/tools")
        data = response.json()

        if len(data) > 0:
            tool = data[0]
            self.assertIn("tool_id", tool)
            self.assertIn("tool_name", tool)
            self.assertIn("category", tool)
            self.assertIn("count", tool)

    def test_tools_with_limit_parameter(self):
        """Tools endpoint should accept limit parameter."""
        response = self.client.get("/analytics/tools?limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 5)


class TestAnalyticsTimeline(unittest.TestCase):
    """Tests for /analytics/timeline endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_timeline_returns_200(self):
        """Timeline endpoint should return 200."""
        response = self.client.get("/analytics/timeline")
        self.assertEqual(response.status_code, 200)

    def test_timeline_returns_list(self):
        """Timeline endpoint should return a list of data points."""
        response = self.client.get("/analytics/timeline")
        data = response.json()
        self.assertIsInstance(data, list)

    def test_timeline_item_contains_date_and_count(self):
        """Each timeline item should contain date and count."""
        response = self.client.get("/analytics/timeline")
        data = response.json()

        if len(data) > 0:
            point = data[0]
            self.assertIn("date", point)
            self.assertIn("count", point)

    def test_timeline_with_range_parameter(self):
        """Timeline should accept range parameter."""
        response = self.client.get("/analytics/timeline?range=7d")
        self.assertEqual(response.status_code, 200)

    def test_timeline_with_granularity_day(self):
        """Timeline should accept daily granularity."""
        response = self.client.get("/analytics/timeline?granularity=day")
        self.assertEqual(response.status_code, 200)


class TestAnalyticsCategories(unittest.TestCase):
    """Tests for /analytics/categories endpoint."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_categories_returns_200(self):
        """Categories endpoint should return 200."""
        response = self.client.get("/analytics/categories")
        self.assertEqual(response.status_code, 200)

    def test_categories_returns_list(self):
        """Categories endpoint should return a list."""
        response = self.client.get("/analytics/categories")
        data = response.json()
        self.assertIsInstance(data, list)

    def test_category_item_contains_required_fields(self):
        """Each category item should contain required fields."""
        response = self.client.get("/analytics/categories")
        data = response.json()

        if len(data) > 0:
            category = data[0]
            self.assertIn("category", category)
            self.assertIn("count", category)
            self.assertIn("percentage", category)

    def test_category_percentages_sum_to_100(self):
        """Category percentages should sum approximately to 100."""
        response = self.client.get("/analytics/categories")
        data = response.json()

        if len(data) > 0:
            total_percentage = sum(c["percentage"] for c in data)
            # Allow for floating point imprecision
            self.assertAlmostEqual(total_percentage, 100, delta=1)


class TestAnalyticsMockData(unittest.TestCase):
    """Tests for analytics mock data in development mode."""

    def setUp(self):
        """Set up test client."""
        from server import app
        self.client = TestClient(app)

    def test_overview_returns_mock_data_without_supabase(self):
        """Overview should return mock data when Supabase not configured."""
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_KEY": ""}):
            response = self.client.get("/analytics/overview")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            # Should still return valid data structure
            self.assertIn("total_generations", data)

    def test_tools_returns_mock_data_without_supabase(self):
        """Tools should return mock data when Supabase not configured."""
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_KEY": ""}):
            response = self.client.get("/analytics/tools")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
