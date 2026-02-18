"""
Brand Voice Training Module.

Provides AI-powered voice analysis, training, and consistency scoring.
"""

from src.brand.analyzer import VoiceAnalyzer, analyze_sample
from src.brand.scorer import VoiceScorer, score_content
from src.brand.storage import (
    BaseBrandVoiceStorage,
    BrandVoiceStorage,
    InMemoryBrandVoiceStorage,
    PostgresBrandVoiceStorage,
    get_brand_voice_storage,
)
from src.brand.trainer import VoiceTrainer, train_voice_profile

__all__ = [
    "VoiceAnalyzer",
    "analyze_sample",
    "VoiceTrainer",
    "train_voice_profile",
    "VoiceScorer",
    "score_content",
    "BaseBrandVoiceStorage",
    "BrandVoiceStorage",
    "InMemoryBrandVoiceStorage",
    "PostgresBrandVoiceStorage",
    "get_brand_voice_storage",
]
