"""
Route-level tests for the batch generation endpoints (app/routes/batch.py).

These are the characterization net required before the planned lifecycle/export
router split (docs/REMEDIATION_PLAN.md Phase 3.2 / P2.3): they pin status
codes, ownership scoping, state-gating, and response shapes for the endpoints
the split must not change. Storage is mocked at the module-level _job_store;
auth dependencies are overridden.
"""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DEV_API_KEY", "test-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-unit-tests-only")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.types.batch import EnhancedBatchStatus, JobStatus

AUTH_CTX = SimpleNamespace(user_id="user-1", organization_id=None)


def make_job(**overrides) -> EnhancedBatchStatus:
    defaults = dict(
        job_id="job-1",
        status=JobStatus.PROCESSING,
        total_items=3,
        completed_items=1,
        failed_items=0,
        can_cancel=True,
    )
    defaults.update(overrides)
    return EnhancedBatchStatus(**defaults)


class BatchRouteTestCase(unittest.TestCase):
    """Shared client with auth dependencies overridden."""

    def setUp(self):
        from app.dependencies import require_content_access, require_content_creation
        from app.middleware import require_pro_tier
        from server import app

        self.app = app
        self._deps = [
            require_content_access,
            require_content_creation,
            require_pro_tier,
        ]
        app.dependency_overrides[require_content_access] = lambda: AUTH_CTX
        app.dependency_overrides[require_content_creation] = lambda: AUTH_CTX
        app.dependency_overrides[require_pro_tier] = lambda: "user-1"
        self.client = TestClient(app)
        self.client.headers.update({"X-API-Key": "test-key"})

    def tearDown(self):
        for dep in self._deps:
            self.app.dependency_overrides.pop(dep, None)


class TestCsvTemplate(BatchRouteTestCase):
    def test_template_downloads_as_csv(self):
        resp = self.client.get("/batch/template/csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "attachment" in resp.headers["content-disposition"]
        # header row of the documented import format
        assert resp.text.splitlines()[0] == (
            "topic,keywords,tone,content_type,custom_instructions"
        )


class TestEstimate(BatchRouteTestCase):
    ITEMS = [
        {"topic": "AI in Healthcare", "keywords": ["ai"], "tone": "professional"},
        {"topic": "Remote Work", "keywords": [], "tone": "casual"},
    ]

    def test_estimate_returns_cost_shape(self):
        resp = self.client.post("/batch/estimate", json=self.ITEMS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estimated_cost_usd"] > 0
        assert data["estimated_input_tokens"] > 0
        assert data["estimated_output_tokens"] > 0
        assert 0.0 <= data["confidence"] <= 1.0

    def test_estimate_rejects_over_100_items(self):
        # Topics must pass BatchItemInput validation (min 3 chars) so the
        # request reaches the handler's own >100 cap check.
        items = [
            {"topic": f"Topic number {i}", "keywords": [], "tone": "casual"}
            for i in range(101)
        ]
        resp = self.client.post("/batch/estimate", json=items)
        assert resp.status_code == 400

    def test_estimate_rejects_unknown_provider(self):
        resp = self.client.post(
            "/batch/estimate?preferred_provider=not-a-provider", json=self.ITEMS
        )
        assert resp.status_code == 400


class TestJobStatus(BatchRouteTestCase):
    def test_status_returns_owned_job(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(return_value=make_job())
        with patch("app.routes.batch._job_store", store):
            resp = self.client.get("/batch/job-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "job-1"
        assert data["status"] == "processing"
        # ownership scoping: called with the auth context's scope id
        store.get_job_if_owned.assert_awaited_once_with("job-1", "user-1")

    def test_status_404_when_not_owned_or_missing(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(return_value=None)
        with patch("app.routes.batch._job_store", store):
            resp = self.client.get("/batch/nope")
        assert resp.status_code == 404


class TestJobResults(BatchRouteTestCase):
    def test_results_400_while_processing(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            return_value=make_job(status=JobStatus.PROCESSING)
        )
        with patch("app.routes.batch._job_store", store):
            resp = self.client.get("/batch/job-1/results")
        assert resp.status_code == 400

    def test_results_returned_for_completed_job(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            return_value=make_job(
                status=JobStatus.COMPLETED, completed_items=3, can_cancel=False
            )
        )
        store.get_results = AsyncMock(return_value=[])
        with patch("app.routes.batch._job_store", store):
            resp = self.client.get("/batch/job-1/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["status"] == "completed"
        assert data["results"] == []


class TestCancel(BatchRouteTestCase):
    def test_cancel_sets_flag_and_updates_status(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(return_value=make_job(can_cancel=True))
        store.set_cancel_flag = AsyncMock()
        store.update_job = AsyncMock()
        with patch("app.routes.batch._job_store", store):
            resp = self.client.post("/batch/job-1/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        store.set_cancel_flag.assert_awaited_once_with("job-1", True)
        store.update_job.assert_awaited_once_with(
            "job-1", status=JobStatus.CANCELLED.value, can_cancel=False
        )

    def test_cancel_400_when_not_cancellable(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            return_value=make_job(status=JobStatus.COMPLETED, can_cancel=False)
        )
        with patch("app.routes.batch._job_store", store):
            resp = self.client.post("/batch/job-1/cancel")
        assert resp.status_code == 400

    def test_cancel_404_when_missing(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(return_value=None)
        with patch("app.routes.batch._job_store", store):
            resp = self.client.post("/batch/nope/cancel")
        assert resp.status_code == 404


class TestListJobs(BatchRouteTestCase):
    def test_list_returns_pagination_shape(self):
        jobs = [make_job(job_id=f"job-{i}") for i in range(3)]
        store = MagicMock()
        # A single fetch returns the full owned set; the route paginates it
        # in-process (no second count scan).
        store.list_jobs = AsyncMock(return_value=jobs)
        with patch("app.routes.batch._job_store", store):
            resp = self.client.get("/batch/jobs?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["jobs"]) == 2
        assert data["total"] == 3
        assert data["has_more"] is True
        # Exactly one store scan, not two.
        assert store.list_jobs.await_count == 1


if __name__ == "__main__":
    unittest.main()


class TestExport(BatchRouteTestCase):
    def test_export_json_for_completed_job(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            return_value=make_job(status=JobStatus.COMPLETED, can_cancel=False)
        )
        store.get_results = AsyncMock(return_value=[])
        with patch("app.routes.batch_export._job_store", store):
            resp = self.client.get("/batch/export/job-1?format=json")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")

    def test_export_400_while_processing(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(
            return_value=make_job(status=JobStatus.PROCESSING)
        )
        with patch("app.routes.batch_export._job_store", store):
            resp = self.client.get("/batch/export/job-1?format=json")
        assert resp.status_code == 400

    def test_export_404_when_missing(self):
        store = MagicMock()
        store.get_job_if_owned = AsyncMock(return_value=None)
        with patch("app.routes.batch_export._job_store", store):
            resp = self.client.get("/batch/export/nope?format=json")
        assert resp.status_code == 404
