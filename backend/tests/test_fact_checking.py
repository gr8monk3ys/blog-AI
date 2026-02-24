"""Tests for fact-checking module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.types.fact_check import (
    Claim,
    ClaimType,
    ClaimVerification,
    FactCheckResult,
    VerificationStatus,
)


class TestClaimExtractor:
    @patch("src.fact_checking.claim_extractor.generate_text")
    @patch("src.fact_checking.claim_extractor.create_provider_from_env")
    def test_extract_claims(self, mock_provider, mock_generate):
        from src.fact_checking.claim_extractor import extract_claims

        mock_provider.return_value = MagicMock()
        mock_generate.return_value = json.dumps([
            {"text": "The Earth is 4.5 billion years old", "source_section": "Intro", "claim_type": "scientific"},
            {"text": "Water covers 71% of Earth", "source_section": "Geography", "claim_type": "statistic"},
        ])

        claims = extract_claims("The Earth is 4.5 billion years old. Water covers 71% of Earth.")

        assert len(claims) == 2
        assert claims[0].text == "The Earth is 4.5 billion years old"
        assert claims[0].claim_type == ClaimType.SCIENTIFIC
        assert claims[1].claim_type == ClaimType.STATISTIC

    @patch("src.fact_checking.claim_extractor.generate_text")
    @patch("src.fact_checking.claim_extractor.create_provider_from_env")
    def test_extract_claims_invalid_json(self, mock_provider, mock_generate):
        from src.fact_checking.claim_extractor import extract_claims

        mock_provider.return_value = MagicMock()
        mock_generate.return_value = "This is not JSON"

        claims = extract_claims("Some content")
        assert claims == []

    @patch("src.fact_checking.claim_extractor.generate_text")
    @patch("src.fact_checking.claim_extractor.create_provider_from_env")
    def test_extract_claims_with_code_fence(self, mock_provider, mock_generate):
        from src.fact_checking.claim_extractor import extract_claims

        mock_provider.return_value = MagicMock()
        mock_generate.return_value = '```json\n[{"text": "Claim 1", "source_section": "", "claim_type": "general"}]\n```'

        claims = extract_claims("Some content")
        assert len(claims) == 1


class TestClaimValidator:
    @patch("src.fact_checking.claim_validator.generate_text")
    @patch("src.fact_checking.claim_validator.create_provider_from_env")
    def test_validate_verified(self, mock_provider, mock_generate):
        from src.fact_checking.claim_validator import validate_claim

        mock_provider.return_value = MagicMock()
        mock_generate.return_value = json.dumps({
            "status": "verified",
            "confidence": 0.9,
            "supporting_sources": ["Nature.com"],
            "explanation": "Confirmed by scientific sources",
        })

        claim = Claim(text="Earth is 4.5 billion years old", claim_type=ClaimType.SCIENTIFIC)
        sources = [{"title": "Earth Age Study", "url": "https://nature.com/study", "snippet": "Earth is approximately 4.5 billion years old"}]

        result = validate_claim(claim, sources)
        assert result.status == VerificationStatus.VERIFIED
        assert result.confidence == 0.9

    @patch("src.fact_checking.claim_validator.generate_text")
    @patch("src.fact_checking.claim_validator.create_provider_from_env")
    def test_validate_no_sources(self, mock_provider, mock_generate):
        from src.fact_checking.claim_validator import validate_claim

        claim = Claim(text="Some claim")
        result = validate_claim(claim, [])

        assert result.status == VerificationStatus.UNVERIFIED
        assert result.confidence == 0.0


class TestFactChecker:
    @patch("src.fact_checking.fact_checker.validate_claims")
    @patch("src.fact_checking.fact_checker.extract_claims")
    def test_check_facts(self, mock_extract, mock_validate):
        from src.fact_checking.fact_checker import check_facts

        claim1 = Claim(text="Claim 1", claim_type=ClaimType.GENERAL)
        claim2 = Claim(text="Claim 2", claim_type=ClaimType.STATISTIC)
        mock_extract.return_value = [claim1, claim2]

        mock_validate.return_value = [
            ClaimVerification(claim=claim1, confidence=0.9, status=VerificationStatus.VERIFIED, explanation="Confirmed"),
            ClaimVerification(claim=claim2, confidence=0.3, status=VerificationStatus.CONTRADICTED, explanation="Wrong"),
        ]

        result = check_facts("Content with claims", sources=[{"title": "Src", "url": "http://example.com", "snippet": "Info"}])

        assert isinstance(result, FactCheckResult)
        assert result.verified_count == 1
        assert result.contradicted_count == 1
        assert result.overall_confidence == pytest.approx(0.6, abs=0.01)

    @patch("src.fact_checking.fact_checker.extract_claims")
    def test_no_claims(self, mock_extract):
        from src.fact_checking.fact_checker import check_facts

        mock_extract.return_value = []

        result = check_facts("An opinion piece with no facts")

        assert result.overall_confidence == 1.0
        assert len(result.claims) == 0
