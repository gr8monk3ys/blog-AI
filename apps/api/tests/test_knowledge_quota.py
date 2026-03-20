"""
Tests for Knowledge Base tier-based quota enforcement.
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

os.environ["DEV_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-unit-tests-only"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.mark.asyncio
async def test_free_tier_allows_first_upload():
    """Free tier should allow upload when under limits."""
    with patch("src.knowledge.quota._get_user_tier", new_callable=AsyncMock, return_value="free"), \
         patch("src.knowledge.quota._get_kb_usage", new_callable=AsyncMock, return_value={
             "document_count": 0, "total_storage_bytes": 0
         }):
        from src.knowledge.quota import check_kb_quota
        # Should not raise
        await check_kb_quota("user_123", additional_bytes=1024)


@pytest.mark.asyncio
async def test_free_tier_blocks_at_doc_limit():
    """Free tier should block upload when at document limit."""
    with patch("src.knowledge.quota._get_user_tier", new_callable=AsyncMock, return_value="free"), \
         patch("src.knowledge.quota._get_kb_usage", new_callable=AsyncMock, return_value={
             "document_count": 2, "total_storage_bytes": 1024
         }):
        from src.knowledge.quota import check_kb_quota, KBQuotaExceededError
        with pytest.raises(KBQuotaExceededError) as exc_info:
            await check_kb_quota("user_123", additional_bytes=1024)
        assert exc_info.value.tier == "free"
        assert "limit reached" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_free_tier_blocks_at_storage_limit():
    """Free tier should block upload when exceeding storage limit."""
    with patch("src.knowledge.quota._get_user_tier", new_callable=AsyncMock, return_value="free"), \
         patch("src.knowledge.quota._get_kb_usage", new_callable=AsyncMock, return_value={
             "document_count": 1, "total_storage_bytes": 4 * 1024 * 1024
         }):
        from src.knowledge.quota import check_kb_quota, KBQuotaExceededError
        # 4MB + 2MB = 6MB > 5MB limit
        with pytest.raises(KBQuotaExceededError):
            await check_kb_quota("user_123", additional_bytes=2 * 1024 * 1024)


@pytest.mark.asyncio
async def test_starter_tier_higher_limits():
    """Starter tier should allow more documents than free."""
    with patch("src.knowledge.quota._get_user_tier", new_callable=AsyncMock, return_value="starter"), \
         patch("src.knowledge.quota._get_kb_usage", new_callable=AsyncMock, return_value={
             "document_count": 10, "total_storage_bytes": 10 * 1024 * 1024
         }):
        from src.knowledge.quota import check_kb_quota
        # 10 docs is under starter limit of 20
        await check_kb_quota("user_123", additional_bytes=1024)


@pytest.mark.asyncio
async def test_pro_tier_unlimited():
    """Pro tier should have no limits."""
    with patch("src.knowledge.quota._get_user_tier", new_callable=AsyncMock, return_value="pro"), \
         patch("src.knowledge.quota._get_kb_usage", new_callable=AsyncMock, return_value={
             "document_count": 1000, "total_storage_bytes": 500 * 1024 * 1024
         }):
        from src.knowledge.quota import check_kb_quota
        await check_kb_quota("user_123", additional_bytes=100 * 1024 * 1024)
