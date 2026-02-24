"""
Type definitions for fact-checking functionality.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """Classification of a factual claim."""
    STATISTIC = "statistic"
    QUOTE = "quote"
    HISTORICAL = "historical"
    SCIENTIFIC = "scientific"
    GENERAL = "general"


class VerificationStatus(str, Enum):
    """Verification result for a claim."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"


class Claim(BaseModel):
    """A factual claim extracted from content."""
    text: str = Field(..., description="The claim text as extracted from content")
    source_section: str = Field(default="", description="Section title where claim appears")
    claim_type: ClaimType = Field(default=ClaimType.GENERAL)


class ClaimVerification(BaseModel):
    """Verification result for a single claim."""
    claim: Claim
    confidence: float = Field(ge=0, le=1, description="Confidence in the verification (0-1)")
    status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    supporting_sources: list[str] = Field(
        default_factory=list,
        description="URLs or titles of sources that support/contradict the claim",
    )
    explanation: str = Field(default="", description="Brief explanation of the verification")


class FactCheckResult(BaseModel):
    """Aggregate fact-check result for an entire piece of content."""
    claims: list[ClaimVerification] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0, le=1, description="Average confidence across all claims")
    verified_count: int = Field(default=0)
    unverified_count: int = Field(default=0)
    contradicted_count: int = Field(default=0)
    summary: str = Field(default="")
