# Tier 3 Moonshot Features - Technical Architecture

This document provides detailed technical architecture specifications for Blog AI's Tier 3 moonshot features. Each feature includes architecture diagrams, data models, API design, integration points, dependencies, complexity assessment, and performance considerations.

---

## Table of Contents

1. [F7: Voice Input to Content](#f7-voice-input-to-content)
2. [F8: Live SEO Mode](#f8-live-seo-mode)
3. [F9: Multi-LLM Ensemble Mode](#f9-multi-llm-ensemble-mode)
4. [F10: Agent-Based Deep Research](#f10-agent-based-deep-research)

---

## F7: Voice Input to Content

### Overview

Voice-first content creation enabling users to dictate blog posts, meeting notes, and content ideas through speech-to-text with intelligent parsing and structured output generation.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VOICE INPUT PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Frontend   │    │   WebSocket  │    │   FastAPI    │                   │
│  │   (Mobile/   │───▶│   Audio      │───▶│   Voice      │                   │
│  │   Desktop)   │    │   Stream     │    │   Router     │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              Audio Processing Layer                   │                   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │                   │
│  │  │  VAD       │  │  Noise     │  │  Audio         │  │                   │
│  │  │  (Voice    │  │  Reduction │  │  Chunking      │  │                   │
│  │  │  Activity) │  │  Filter    │  │  (30s windows) │  │                   │
│  │  └────────────┘  └────────────┘  └────────────────┘  │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              Transcription Layer                      │                   │
│  │  ┌─────────────────┐    ┌─────────────────────────┐  │                   │
│  │  │  OpenAI Whisper │    │  Real-time Streaming    │  │                   │
│  │  │  API (Primary)  │    │  Transcription Service  │  │                   │
│  │  │  - whisper-1    │    │  (Deepgram/AssemblyAI)  │  │                   │
│  │  └─────────────────┘    └─────────────────────────┘  │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              Command & Intent Parser                  │                   │
│  │  ┌────────────────┐  ┌───────────────────────────┐   │                   │
│  │  │  Voice Command │  │  Content Intent           │   │                   │
│  │  │  Detector      │  │  Classifier               │   │                   │
│  │  │  - "new section"│  │  - blog_dictation        │   │                   │
│  │  │  - "bullet point"│ │  - meeting_notes         │   │                   │
│  │  │  - "end paragraph"││  - editing_command       │   │                   │
│  │  └────────────────┘  └───────────────────────────┘   │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              Content Structuring Pipeline             │                   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │                   │
│  │  │  Transcript  │  │  Section     │  │  Content   │  │                   │
│  │  │  to Outline  │─▶│  Generator   │─▶│  Enricher  │  │                   │
│  │  │  Converter   │  │  (LLM)       │  │  (SEO/FAQs)│  │                   │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                              │                                               │
│                              ▼                                               │
│                  ┌────────────────────┐                                      │
│                  │  BlogPost / Book   │                                      │
│                  │  Output            │                                      │
│                  └────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# src/types/voice.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class TranscriptionMode(str, Enum):
    REALTIME = "realtime"      # Streaming transcription
    BATCH = "batch"            # File upload transcription


class VoiceCommandType(str, Enum):
    NEW_SECTION = "new_section"
    NEW_PARAGRAPH = "new_paragraph"
    BULLET_POINT = "bullet_point"
    END_DICTATION = "end_dictation"
    UNDO = "undo"
    READ_BACK = "read_back"
    INSERT_HEADING = "insert_heading"
    ADD_QUOTE = "add_quote"


class ContentIntent(str, Enum):
    BLOG_DICTATION = "blog_dictation"
    MEETING_NOTES = "meeting_notes"
    BRAINSTORM = "brainstorm"
    EDITING = "editing"


@dataclass
class AudioChunk:
    """Raw audio data chunk for processing."""
    data: bytes
    timestamp: float
    duration_ms: int
    sample_rate: int = 16000
    channels: int = 1
    format: str = "webm"  # or "wav", "mp3"


@dataclass
class TranscriptionSegment:
    """A transcribed segment with timing information."""
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    is_final: bool = True


@dataclass
class VoiceCommand:
    """Detected voice command from transcript."""
    type: VoiceCommandType
    timestamp: float
    raw_text: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceSession:
    """Active voice input session state."""
    session_id: str
    user_id: str
    mode: TranscriptionMode
    intent: ContentIntent
    started_at: datetime
    segments: List[TranscriptionSegment] = field(default_factory=list)
    commands: List[VoiceCommand] = field(default_factory=list)
    current_section: Optional[str] = None
    accumulated_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingTranscript:
    """Structured meeting notes from voice input."""
    title: str
    date: datetime
    duration_minutes: int
    participants: List[str]
    segments: List[TranscriptionSegment]
    key_points: List[str]
    action_items: List[Dict[str, str]]  # {assignee, task, due_date}
    summary: str


@dataclass
class VoiceGenerationRequest:
    """Request to generate content from voice input."""
    session_id: str
    transcript: str
    intent: ContentIntent
    target_format: Literal["blog", "book", "meeting_notes", "outline"]
    keywords: Optional[List[str]] = None
    tone: str = "informative"
    enhance_with_research: bool = False


@dataclass
class TranscriptionConfig:
    """Configuration for transcription service."""
    provider: Literal["openai", "deepgram", "assemblyai"] = "openai"
    model: str = "whisper-1"
    language: str = "en"
    enable_diarization: bool = False
    enable_punctuation: bool = True
    enable_profanity_filter: bool = False
    vocabulary_boost: Optional[List[str]] = None  # Domain-specific terms
```

### API Design

```python
# app/routes/voice.py

from fastapi import APIRouter, WebSocket, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/voice", tags=["voice"])


# WebSocket endpoint for real-time streaming transcription
@router.websocket("/ws/transcribe/{session_id}")
async def websocket_transcribe(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Depends(verify_api_key)
):
    """
    Real-time voice transcription via WebSocket.

    Client sends: Binary audio chunks (WebM/Opus format)
    Server sends: JSON with transcription segments and commands

    Message format (server -> client):
    {
        "type": "transcript" | "command" | "error" | "status",
        "data": {...}
    }
    """
    pass


# REST endpoint for batch transcription
@router.post("/transcribe")
async def batch_transcribe(
    file: UploadFile = File(...),
    config: TranscriptionConfig = Depends(),
    user_id: str = Depends(verify_api_key)
) -> TranscriptionResult:
    """
    Transcribe an uploaded audio file.

    Supported formats: mp3, wav, webm, m4a, ogg
    Max file size: 25MB
    Max duration: 30 minutes
    """
    pass


# Session management
@router.post("/sessions")
async def create_voice_session(
    intent: ContentIntent,
    mode: TranscriptionMode = TranscriptionMode.REALTIME,
    user_id: str = Depends(verify_api_key)
) -> VoiceSession:
    """Create a new voice input session."""
    pass


@router.get("/sessions/{session_id}")
async def get_voice_session(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> VoiceSession:
    """Get voice session state and accumulated transcript."""
    pass


@router.delete("/sessions/{session_id}")
async def end_voice_session(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """End session and return final transcript."""
    pass


# Content generation from voice
@router.post("/generate")
async def generate_from_voice(
    request: VoiceGenerationRequest,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Generate structured content from voice transcript.

    Returns BlogPost, Book outline, or MeetingTranscript based on intent.
    """
    pass


# Meeting-specific endpoints
@router.post("/meetings/process")
async def process_meeting_recording(
    file: UploadFile = File(...),
    enable_diarization: bool = True,
    user_id: str = Depends(verify_api_key)
) -> MeetingTranscript:
    """
    Process a meeting recording into structured notes.

    Features:
    - Speaker diarization
    - Action item extraction
    - Key point summarization
    - Timeline generation
    """
    pass


@router.post("/meetings/{meeting_id}/to-blog")
async def meeting_to_blog(
    meeting_id: str,
    focus_topics: Optional[List[str]] = None,
    user_id: str = Depends(verify_api_key)
) -> BlogPost:
    """Convert meeting notes to a blog post."""
    pass
```

### Integration Points

| Component | Integration Method | Purpose |
|-----------|-------------------|---------|
| `src/text_generation/core.py` | Direct import | Transcript-to-content LLM processing |
| `src/blog/make_blog.py` | Function call | Generate blog from processed transcript |
| `src/planning/content_outline.py` | Function call | Structure voice content into outline |
| `app/routes/websocket.py` | Extend patterns | Real-time audio streaming |
| `app/websocket.py` | ConnectionManager | Session management |
| Frontend ContentGenerator | New component | Voice recording UI |

### New Dependencies

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
openai = "^1.0.0"           # Whisper API (existing)
deepgram-sdk = "^3.0.0"     # Alternative real-time STT
assemblyai = "^0.20.0"      # Alternative with diarization
pydub = "^0.25.1"           # Audio format conversion
webrtcvad = "^2.0.10"       # Voice activity detection
soundfile = "^0.12.1"       # Audio file handling
numpy = "^1.24.0"           # Audio processing

# Frontend (package.json)
{
  "dependencies": {
    "recordrtc": "^5.6.2",
    "@anthropic-ai/sdk": "^0.10.0"
  }
}
```

### Complexity and Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Implementation Complexity | **High** | Real-time audio streaming, command parsing, mobile optimization |
| API Cost Risk | **Medium** | Whisper: $0.006/min; Deepgram: $0.0043/min (streaming) |
| Technical Risk | **Medium** | Browser audio API compatibility, WebSocket reliability |
| UX Risk | **Medium** | Transcription accuracy varies by accent, background noise |
| Security Risk | **Low** | Audio not stored permanently, encrypted in transit |

**Key Risks:**
1. Browser MediaRecorder API inconsistencies across devices
2. Latency for real-time feedback (target < 500ms)
3. Voice command recognition accuracy in continuous speech
4. Mobile battery consumption during extended sessions

### Performance Considerations

```yaml
performance_targets:
  transcription_latency:
    realtime: < 500ms
    batch: < 2s per minute of audio

  throughput:
    concurrent_streams: 100 per server
    audio_chunk_size: 250ms (4KB WebM)

  accuracy:
    word_error_rate: < 10%
    command_recognition: > 95%

caching_strategy:
  session_state: Redis (TTL: 1 hour)
  transcription_cache: None (ephemeral)

scaling:
  audio_processing: Horizontal (stateless workers)
  websocket_sessions: Sticky sessions required

resource_limits:
  max_audio_duration: 30 minutes
  max_file_size: 25MB
  max_concurrent_sessions_per_user: 3
```

---

## F8: Live SEO Mode

### Overview

Real-time SEO analysis and optimization during content creation, providing actionable recommendations, competitor SERP tracking, and content scoring with integration to professional SEO APIs.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LIVE SEO MODE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Frontend (Real-time UI)                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│  │  │  SEO Score   │  │  Keyword     │  │  Competitor               │   │   │
│  │  │  Dashboard   │  │  Density     │  │  Comparison Panel         │   │   │
│  │  │  (0-100)     │  │  Heatmap     │  │                          │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│  │  │  Readability │  │  Suggestion  │  │  SERP Preview            │   │   │
│  │  │  Metrics     │  │  Sidebar     │  │  (Google/Bing mock)      │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │ WebSocket                                     │
│                              ▼ (debounced updates)                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      SEO Analysis Router                              │   │
│  │                      POST /seo/analyze                                │   │
│  │                      WS /ws/seo/{session_id}                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                          │
│  ┌────────────┐      ┌────────────┐      ┌────────────────┐                 │
│  │  Internal  │      │  SEO API   │      │  SERP          │                 │
│  │  Analyzer  │      │  Gateway   │      │  Tracker       │                 │
│  └────────────┘      └────────────┘      └────────────────┘                 │
│         │                    │                    │                          │
│         ▼                    ▼                    ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Analysis Components                               │    │
│  │                                                                      │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │ Keyword     │ │ Readability │ │ On-Page     │ │ Competitor  │   │    │
│  │  │ Analyzer    │ │ Scorer      │ │ SEO Checker │ │ Analyzer    │   │    │
│  │  │             │ │             │ │             │ │             │   │    │
│  │  │ - Density   │ │ - Flesch    │ │ - Title     │ │ - SERP      │   │    │
│  │  │ - TF-IDF    │ │ - Grade     │ │ - Meta      │ │   Position  │   │    │
│  │  │ - LSI       │ │ - Sentence  │ │ - Headers   │ │ - Backlinks │   │    │
│  │  │ - Intent    │ │   Length    │ │ - Images    │ │ - Content   │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    External SEO API Layer                            │    │
│  │                    (with caching + rate limiting)                    │    │
│  │                                                                      │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │    │
│  │  │   SEMrush    │ │   Ahrefs     │ │   Moz        │ │  DataForSEO│ │    │
│  │  │   API        │ │   API        │ │   API        │ │   API      │ │    │
│  │  │              │ │              │ │              │ │            │ │    │
│  │  │ - Keywords   │ │ - Backlinks  │ │ - DA/PA      │ │ - SERP API │ │    │
│  │  │ - Difficulty │ │ - DR Rating  │ │ - Spam Score │ │ - Keywords │ │    │
│  │  │ - Volume     │ │ - Organic    │ │ - Link       │ │ - On-Page  │ │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Recommendation Engine                             │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  Priority Scoring Algorithm                                   │   │    │
│  │  │  score = (impact * 0.4) + (ease * 0.3) + (urgency * 0.3)     │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │    │
│  │  │ Quick Wins │ │ Structure  │ │ Content    │ │ Technical      │   │    │
│  │  │ (< 5 min)  │ │ Changes    │ │ Gaps       │ │ Fixes          │   │    │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│                   ┌────────────────────┐                                     │
│                   │  SEOAnalysisResult │                                     │
│                   │  + Recommendations │                                     │
│                   └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# src/types/seo_live.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class SEOAPIProvider(str, Enum):
    SEMRUSH = "semrush"
    AHREFS = "ahrefs"
    MOZ = "moz"
    DATAFORSEO = "dataforseo"
    INTERNAL = "internal"  # No external API


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"    # Must fix
    HIGH = "high"            # Should fix
    MEDIUM = "medium"        # Nice to have
    LOW = "low"              # Optional optimization


class RecommendationCategory(str, Enum):
    KEYWORD = "keyword"
    READABILITY = "readability"
    STRUCTURE = "structure"
    META = "meta"
    TECHNICAL = "technical"
    CONTENT_GAP = "content_gap"


@dataclass
class KeywordMetrics:
    """Keyword analysis metrics."""
    keyword: str
    density: float                    # Percentage in content
    count: int                        # Occurrences
    search_volume: Optional[int]      # Monthly searches (from API)
    difficulty: Optional[float]       # 0-100 scale
    cpc: Optional[float]              # Cost per click
    trend: Optional[str]              # "rising", "stable", "declining"
    intent: Optional[str]             # "informational", "transactional", etc.
    position_in_serp: Optional[int]   # Current ranking if tracked


@dataclass
class ReadabilityMetrics:
    """Content readability analysis."""
    flesch_reading_ease: float        # 0-100 (higher = easier)
    flesch_kincaid_grade: float       # US grade level
    gunning_fog_index: float          # Years of education needed
    smog_index: float                 # Simple Measure of Gobbledygook
    average_sentence_length: float
    average_word_length: float
    passive_voice_percentage: float
    complex_word_percentage: float


@dataclass
class OnPageSEOMetrics:
    """On-page SEO factor analysis."""
    title_length: int
    title_has_keyword: bool
    meta_description_length: int
    meta_has_keyword: bool
    h1_count: int
    h2_count: int
    h3_count: int
    heading_keyword_usage: float      # Percentage with keywords
    image_count: int
    images_with_alt: int
    internal_links: int
    external_links: int
    word_count: int
    paragraph_count: int


@dataclass
class CompetitorData:
    """Competitor content analysis."""
    url: str
    title: str
    word_count: int
    domain_authority: Optional[float]
    backlinks: Optional[int]
    serp_position: int
    keywords_overlap: List[str]
    content_gaps: List[str]           # Topics they cover that we don't
    unique_angles: List[str]          # Topics we cover that they don't


@dataclass
class SEORecommendation:
    """Single SEO improvement recommendation."""
    id: str
    category: RecommendationCategory
    priority: RecommendationPriority
    title: str
    description: str
    current_value: Optional[str]
    target_value: Optional[str]
    impact_score: float               # 0-10
    ease_score: float                 # 0-10 (higher = easier)
    auto_fixable: bool                # Can be applied automatically
    fix_action: Optional[Dict[str, Any]]  # Action to apply fix


@dataclass
class SEOScore:
    """Overall SEO score breakdown."""
    total: int                        # 0-100
    keyword_score: int
    readability_score: int
    structure_score: int
    meta_score: int
    technical_score: int
    competitor_score: int


@dataclass
class SEOAnalysisResult:
    """Complete SEO analysis result."""
    score: SEOScore
    keywords: List[KeywordMetrics]
    readability: ReadabilityMetrics
    on_page: OnPageSEOMetrics
    competitors: List[CompetitorData]
    recommendations: List[SEORecommendation]
    serp_preview: Dict[str, str]      # title, description, url preview
    analysis_timestamp: datetime
    api_calls_made: Dict[str, int]    # Track API usage


@dataclass
class SEOConfig:
    """Configuration for SEO analysis."""
    primary_keyword: str
    secondary_keywords: List[str] = field(default_factory=list)
    target_country: str = "us"
    target_language: str = "en"
    competitor_urls: List[str] = field(default_factory=list)
    api_provider: SEOAPIProvider = SEOAPIProvider.INTERNAL
    enable_competitor_analysis: bool = True
    enable_serp_tracking: bool = False
    min_word_count: int = 1500
    target_readability_grade: float = 8.0


@dataclass
class SEOSession:
    """Live SEO session state."""
    session_id: str
    conversation_id: str
    config: SEOConfig
    current_content: str
    current_title: str
    current_meta: str
    last_analysis: Optional[SEOAnalysisResult]
    analysis_history: List[SEOScore] = field(default_factory=list)
    applied_recommendations: List[str] = field(default_factory=list)
```

### API Design

```python
# app/routes/seo_live.py

from fastapi import APIRouter, WebSocket, Depends, HTTPException, BackgroundTasks

router = APIRouter(prefix="/seo", tags=["seo"])


# Real-time SEO analysis via WebSocket
@router.websocket("/ws/{session_id}")
async def websocket_seo_analysis(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Depends(verify_api_key)
):
    """
    Real-time SEO analysis as content is edited.

    Client sends: Content updates (debounced, 500ms)
    {
        "type": "content_update",
        "title": "...",
        "content": "...",
        "meta_description": "..."
    }

    Server sends: Analysis results
    {
        "type": "analysis" | "recommendation" | "score_update",
        "data": {...}
    }
    """
    pass


# Session management
@router.post("/sessions")
async def create_seo_session(
    config: SEOConfig,
    conversation_id: str,
    user_id: str = Depends(verify_api_key)
) -> SEOSession:
    """Create a new live SEO session."""
    pass


@router.get("/sessions/{session_id}")
async def get_seo_session(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> SEOSession:
    """Get current SEO session state."""
    pass


# One-time analysis
@router.post("/analyze")
async def analyze_content(
    content: str,
    title: str,
    meta_description: Optional[str] = None,
    config: SEOConfig = Depends(),
    user_id: str = Depends(verify_api_key)
) -> SEOAnalysisResult:
    """
    Perform complete SEO analysis on content.

    This is a synchronous endpoint for one-time analysis.
    For real-time analysis, use the WebSocket endpoint.
    """
    pass


# Keyword research
@router.post("/keywords/research")
async def research_keywords(
    seed_keyword: str,
    limit: int = 50,
    api_provider: SEOAPIProvider = SEOAPIProvider.INTERNAL,
    user_id: str = Depends(verify_api_key)
) -> List[KeywordMetrics]:
    """
    Research keywords related to seed keyword.

    Returns keyword suggestions with metrics from configured API.
    """
    pass


@router.get("/keywords/{keyword}/metrics")
async def get_keyword_metrics(
    keyword: str,
    country: str = "us",
    api_provider: SEOAPIProvider = SEOAPIProvider.INTERNAL,
    user_id: str = Depends(verify_api_key)
) -> KeywordMetrics:
    """Get detailed metrics for a specific keyword."""
    pass


# Competitor analysis
@router.post("/competitors/analyze")
async def analyze_competitors(
    keyword: str,
    urls: Optional[List[str]] = None,
    limit: int = 10,
    user_id: str = Depends(verify_api_key)
) -> List[CompetitorData]:
    """
    Analyze competitor content for a keyword.

    If URLs not provided, fetches top SERP results.
    """
    pass


# Recommendations
@router.post("/recommendations/apply/{recommendation_id}")
async def apply_recommendation(
    recommendation_id: str,
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Automatically apply an SEO recommendation.

    Returns the modified content or action taken.
    """
    pass


# SERP tracking
@router.post("/serp/track")
async def track_serp_position(
    keyword: str,
    url: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Start tracking SERP position for keyword/URL pair."""
    pass


@router.get("/serp/history/{keyword}")
async def get_serp_history(
    keyword: str,
    days: int = 30,
    user_id: str = Depends(verify_api_key)
) -> List[Dict[str, Any]]:
    """Get SERP position history for tracked keyword."""
    pass


# API usage and cost
@router.get("/usage")
async def get_seo_api_usage(
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get SEO API usage statistics and costs.

    Returns:
    - API calls by provider
    - Estimated costs
    - Remaining quota
    """
    pass
```

### Integration Points

| Component | Integration Method | Purpose |
|-----------|-------------------|---------|
| `src/seo/meta_description.py` | Extend | Enhanced meta with live scoring |
| `src/research/web_researcher.py` | Use patterns | SERP data fetching |
| `src/text_generation/core.py` | LLM for recommendations | Generate improvement text |
| `app/routes/blog.py` | Add SEO session | Attach SEO to content generation |
| Frontend ContentViewer | New SEO panel | Real-time SEO dashboard |

### New Dependencies

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
textstat = "^0.7.3"         # Readability metrics
nltk = "^3.8.1"             # NLP for keyword analysis
scikit-learn = "^1.3.0"     # TF-IDF calculations
beautifulsoup4 = "^4.12.0"  # Competitor page parsing
aiohttp = "^3.9.0"          # Async HTTP for API calls

# SEO API SDKs (optional, based on chosen provider)
semrush-api = "^1.0.0"      # SEMrush integration
python-ahrefs = "^0.1.0"    # Ahrefs integration
moz-api = "^0.1.0"          # Moz integration
dataforseo-client = "^1.0.0"# DataForSEO integration
```

### SEO API Cost Management

```python
# src/seo/api_manager.py

from dataclasses import dataclass
from typing import Dict
from enum import Enum


class SEOAPITier(str, Enum):
    FREE = "free"           # Internal analysis only
    BASIC = "basic"         # Limited API calls
    PRO = "pro"             # Full API access
    ENTERPRISE = "enterprise"


@dataclass
class SEOAPICosts:
    """Monthly API costs by provider (approximate)."""

    # SEMrush
    semrush_basic: float = 129.95      # 10,000 results/month
    semrush_guru: float = 249.95       # 30,000 results/month

    # Ahrefs
    ahrefs_lite: float = 99.00         # 500 credits/month
    ahrefs_standard: float = 199.00    # 1,500 credits/month

    # Moz
    moz_standard: float = 99.00        # 150 queries/month
    moz_medium: float = 179.00         # 5,000 queries/month

    # DataForSEO (pay-per-use)
    dataforseo_serp: float = 0.002     # Per SERP request
    dataforseo_keywords: float = 0.005 # Per keyword lookup


@dataclass
class APIBudget:
    """User's SEO API budget configuration."""
    monthly_limit_usd: float = 50.00
    current_spend: float = 0.00
    alerts_at: List[float] = field(default_factory=lambda: [0.5, 0.8, 0.95])


# Caching strategy to minimize API calls
CACHE_CONFIG = {
    "keyword_metrics": {
        "ttl": 86400 * 7,    # 7 days
        "storage": "redis"
    },
    "serp_results": {
        "ttl": 86400,        # 24 hours
        "storage": "redis"
    },
    "competitor_data": {
        "ttl": 86400 * 3,    # 3 days
        "storage": "redis"
    },
    "domain_authority": {
        "ttl": 86400 * 30,   # 30 days
        "storage": "redis"
    }
}
```

### Complexity and Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Implementation Complexity | **High** | Multiple API integrations, real-time scoring algorithm |
| API Cost Risk | **High** | SEO APIs are expensive; need careful budget management |
| Technical Risk | **Medium** | API rate limits, inconsistent data across providers |
| UX Risk | **Low** | Clear metrics and actionable recommendations |
| Data Freshness Risk | **Medium** | SEO data can be stale; SERP changes frequently |

**Key Risks:**
1. SEO API costs can escalate quickly without proper caching
2. Different providers return inconsistent data formats
3. Real-time analysis must not block content editing
4. Algorithm accuracy requires ongoing tuning

### Performance Considerations

```yaml
performance_targets:
  analysis_latency:
    internal_only: < 200ms
    with_cached_api: < 500ms
    with_live_api: < 3s

  update_frequency:
    content_debounce: 500ms
    full_reanalysis: 2s cooldown
    api_refresh: 1 hour minimum

caching_strategy:
  keyword_data: Redis (TTL: 7 days)
  serp_results: Redis (TTL: 24 hours)
  competitor_analysis: Redis (TTL: 3 days)

  # Intelligent cache warming
  warm_on_session_start: true
  background_refresh: true

api_optimization:
  batch_requests: true           # Combine multiple keywords
  parallel_providers: false      # Sequential to manage costs
  fallback_chain:
    - internal
    - dataforseo
    - semrush

rate_limiting:
  per_user_per_hour: 100 analyses
  api_calls_per_day: 1000 (configurable)
```

---

## F9: Multi-LLM Ensemble Mode

### Overview

Leverage multiple LLM providers simultaneously for content generation, combining the strengths of each model through parallel generation, voting algorithms, and intelligent blending to produce superior output.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-LLM ENSEMBLE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Ensemble Controller                              │   │
│  │                      POST /ensemble/generate                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Strategy Selector                                │   │
│  │                                                                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │  Parallel   │ │  Cascading  │ │  Specialist │ │  Consensus  │    │   │
│  │  │  Generation │ │  Refinement │ │  Routing    │ │  Voting     │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Parallel Generation Pool                          │    │
│  │                    (asyncio.gather with timeout)                     │    │
│  │                                                                      │    │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────┐│    │
│  │  │   Claude Worker   │  │   GPT-4 Worker    │  │  Gemini Worker   ││    │
│  │  │                   │  │                   │  │                  ││    │
│  │  │  Specialization:  │  │  Specialization:  │  │  Specialization: ││    │
│  │  │  - Creative       │  │  - SEO/Structure  │  │  - Research      ││    │
│  │  │  - Nuanced tone   │  │  - Technical      │  │  - Fact synthesis││    │
│  │  │  - Long-form      │  │  - Formatting     │  │  - Summarization ││    │
│  │  │                   │  │                   │  │                  ││    │
│  │  │  Models:          │  │  Models:          │  │  Models:         ││    │
│  │  │  - opus-4         │  │  - gpt-4-turbo    │  │  - gemini-1.5-pro││    │
│  │  │  - sonnet-4       │  │  - gpt-4o         │  │  - gemini-1.5-   ││    │
│  │  │                   │  │                   │  │    flash         ││    │
│  │  └───────────────────┘  └───────────────────┘  └──────────────────┘│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Output Aggregation Layer                           │   │
│  │                                                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Voting Engine                               │   │   │
│  │  │                                                                │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │   │   │
│  │  │  │  Majority    │  │  Weighted    │  │  Quality-Scored      │ │   │   │
│  │  │  │  Vote        │  │  Average     │  │  Selection           │ │   │   │
│  │  │  │              │  │              │  │                      │ │   │   │
│  │  │  │  Simple      │  │  Based on    │  │  LLM-as-judge        │ │   │   │
│  │  │  │  consensus   │  │  model       │  │  evaluates each      │ │   │   │
│  │  │  │              │  │  weights     │  │  output              │ │   │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Blending Engine                             │   │   │
│  │  │                                                                │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │   │   │
│  │  │  │  Section     │  │  Sentence    │  │  Semantic            │ │   │   │
│  │  │  │  Merge       │  │  Level       │  │  Deduplication       │ │   │   │
│  │  │  │              │  │  Interleave  │  │                      │ │   │   │
│  │  │  │  Best intro  │  │  Pick best   │  │  Remove redundant    │ │   │   │
│  │  │  │  from Claude │  │  sentences   │  │  ideas across        │ │   │   │
│  │  │  │  Best SEO    │  │  from each   │  │  outputs             │ │   │   │
│  │  │  │  from GPT    │  │              │  │                      │ │   │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Cost-Aware Router                                  │   │
│  │                                                                       │   │
│  │  Budget Check → Model Selection → Fallback Chain → Usage Tracking    │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  Cost per 1K tokens (approximate):                              │  │   │
│  │  │  - Claude Opus 4: $15/$75 (input/output)                        │  │   │
│  │  │  - Claude Sonnet 4: $3/$15                                      │  │   │
│  │  │  - GPT-4 Turbo: $10/$30                                         │  │   │
│  │  │  - GPT-4o: $5/$15                                               │  │   │
│  │  │  - Gemini 1.5 Pro: $3.50/$10.50                                 │  │   │
│  │  │  - Gemini 1.5 Flash: $0.075/$0.30                               │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Quality Comparison UI                              │   │
│  │                                                                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │   │
│  │  │  Side-by-  │  │  Diff      │  │  Score     │  │  User          │  │   │
│  │  │  Side View │  │  Highlight │  │  Breakdown │  │  Preference    │  │   │
│  │  │            │  │            │  │            │  │  Learning      │  │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│                   ┌────────────────────┐                                     │
│                   │  EnsembleResult    │                                     │
│                   │  + All Outputs     │                                     │
│                   │  + Selected Output │                                     │
│                   │  + Cost Breakdown  │                                     │
│                   └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# src/types/ensemble.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Union


class EnsembleStrategy(str, Enum):
    PARALLEL = "parallel"           # Generate with all models simultaneously
    CASCADING = "cascading"         # Refine output through model chain
    SPECIALIST = "specialist"       # Route to best model for task type
    CONSENSUS = "consensus"         # Require agreement between models
    BEST_OF_N = "best_of_n"        # Generate N, pick best


class AggregationMethod(str, Enum):
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    QUALITY_SCORED = "quality_scored"
    SECTION_MERGE = "section_merge"
    LLM_JUDGE = "llm_judge"
    USER_SELECTION = "user_selection"


class ModelSpecialization(str, Enum):
    CREATIVE = "creative"           # Claude strength
    TECHNICAL = "technical"         # GPT-4 strength
    RESEARCH = "research"           # Gemini strength
    SEO = "seo"                     # GPT-4 strength
    FORMATTING = "formatting"       # GPT-4 strength
    SUMMARIZATION = "summarization" # Gemini strength
    LONG_FORM = "long_form"         # Claude strength


@dataclass
class ModelConfig:
    """Configuration for a specific model in ensemble."""
    provider: Literal["openai", "anthropic", "gemini"]
    model: str
    weight: float = 1.0              # Weight in aggregation
    specializations: List[ModelSpecialization] = field(default_factory=list)
    max_tokens: int = 4000
    temperature: float = 0.7
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    timeout_seconds: int = 60
    enabled: bool = True


@dataclass
class EnsemblePreset:
    """Pre-configured ensemble settings."""
    name: str
    description: str
    strategy: EnsembleStrategy
    aggregation: AggregationMethod
    models: List[ModelConfig]
    budget_limit: Optional[float] = None


# Built-in presets
ENSEMBLE_PRESETS = {
    "quality_max": EnsemblePreset(
        name="Maximum Quality",
        description="All top-tier models for best possible output",
        strategy=EnsembleStrategy.PARALLEL,
        aggregation=AggregationMethod.LLM_JUDGE,
        models=[
            ModelConfig(
                provider="anthropic",
                model="claude-opus-4-20250514",
                weight=1.2,
                specializations=[ModelSpecialization.CREATIVE, ModelSpecialization.LONG_FORM],
                cost_per_1k_input=15.0,
                cost_per_1k_output=75.0
            ),
            ModelConfig(
                provider="openai",
                model="gpt-4-turbo",
                weight=1.0,
                specializations=[ModelSpecialization.SEO, ModelSpecialization.TECHNICAL],
                cost_per_1k_input=10.0,
                cost_per_1k_output=30.0
            ),
            ModelConfig(
                provider="gemini",
                model="gemini-1.5-pro",
                weight=0.9,
                specializations=[ModelSpecialization.RESEARCH, ModelSpecialization.SUMMARIZATION],
                cost_per_1k_input=3.5,
                cost_per_1k_output=10.5
            )
        ]
    ),
    "balanced": EnsemblePreset(
        name="Balanced",
        description="Good quality at moderate cost",
        strategy=EnsembleStrategy.SPECIALIST,
        aggregation=AggregationMethod.SECTION_MERGE,
        models=[
            ModelConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                weight=1.0,
                specializations=[ModelSpecialization.CREATIVE],
                cost_per_1k_input=3.0,
                cost_per_1k_output=15.0
            ),
            ModelConfig(
                provider="openai",
                model="gpt-4o",
                weight=1.0,
                specializations=[ModelSpecialization.SEO, ModelSpecialization.FORMATTING],
                cost_per_1k_input=5.0,
                cost_per_1k_output=15.0
            ),
            ModelConfig(
                provider="gemini",
                model="gemini-1.5-flash",
                weight=0.8,
                specializations=[ModelSpecialization.RESEARCH],
                cost_per_1k_input=0.075,
                cost_per_1k_output=0.30
            )
        ]
    ),
    "budget": EnsemblePreset(
        name="Budget",
        description="Cost-effective with 2 fast models",
        strategy=EnsembleStrategy.BEST_OF_N,
        aggregation=AggregationMethod.QUALITY_SCORED,
        models=[
            ModelConfig(
                provider="openai",
                model="gpt-4o-mini",
                weight=1.0,
                cost_per_1k_input=0.15,
                cost_per_1k_output=0.60
            ),
            ModelConfig(
                provider="gemini",
                model="gemini-1.5-flash",
                weight=1.0,
                cost_per_1k_input=0.075,
                cost_per_1k_output=0.30
            )
        ],
        budget_limit=1.00
    )
}


@dataclass
class ModelOutput:
    """Output from a single model."""
    model_config: ModelConfig
    content: str
    generation_time_ms: int
    token_count_input: int
    token_count_output: int
    cost: float
    quality_scores: Optional[Dict[str, float]] = None  # From evaluation
    error: Optional[str] = None


@dataclass
class QualityEvaluation:
    """Quality evaluation of model output."""
    coherence: float          # 0-10
    creativity: float         # 0-10
    accuracy: float           # 0-10
    seo_optimization: float   # 0-10
    readability: float        # 0-10
    overall: float            # Weighted average
    evaluator: str            # "llm_judge" or model name
    rationale: Optional[str]


@dataclass
class EnsembleRequest:
    """Request for ensemble generation."""
    prompt: str
    task_type: Literal["blog", "book_chapter", "outline", "meta", "faq"]
    preset: Optional[str] = "balanced"
    custom_config: Optional[Dict[str, Any]] = None
    require_all_models: bool = False      # Fail if any model fails
    return_all_outputs: bool = True       # Return individual outputs
    budget_limit: Optional[float] = None
    keywords: Optional[List[str]] = None
    tone: str = "informative"


@dataclass
class EnsembleResult:
    """Result from ensemble generation."""
    final_output: str
    aggregation_method_used: AggregationMethod
    individual_outputs: List[ModelOutput]
    quality_evaluations: List[QualityEvaluation]
    total_cost: float
    total_time_ms: int
    models_used: List[str]
    selection_rationale: Optional[str]


@dataclass
class CostTracker:
    """Track ensemble costs for user."""
    user_id: str
    daily_spend: float = 0.0
    monthly_spend: float = 0.0
    daily_limit: float = 10.0
    monthly_limit: float = 100.0
    last_reset_daily: datetime = field(default_factory=datetime.now)
    last_reset_monthly: datetime = field(default_factory=datetime.now)
```

### API Design

```python
# app/routes/ensemble.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

router = APIRouter(prefix="/ensemble", tags=["ensemble"])


@router.post("/generate")
async def ensemble_generate(
    request: EnsembleRequest,
    user_id: str = Depends(verify_api_key)
) -> EnsembleResult:
    """
    Generate content using multi-LLM ensemble.

    Returns the best output along with all individual outputs
    and quality evaluations.
    """
    pass


@router.get("/presets")
async def list_presets() -> List[EnsemblePreset]:
    """List available ensemble presets."""
    return list(ENSEMBLE_PRESETS.values())


@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str) -> EnsemblePreset:
    """Get details of a specific preset."""
    if preset_name not in ENSEMBLE_PRESETS:
        raise HTTPException(status_code=404, detail="Preset not found")
    return ENSEMBLE_PRESETS[preset_name]


@router.post("/presets")
async def create_custom_preset(
    preset: EnsemblePreset,
    user_id: str = Depends(verify_api_key)
) -> EnsemblePreset:
    """Create a custom ensemble preset for the user."""
    pass


@router.post("/compare")
async def compare_outputs(
    outputs: List[ModelOutput],
    evaluation_criteria: Optional[List[str]] = None,
    user_id: str = Depends(verify_api_key)
) -> List[QualityEvaluation]:
    """
    Compare multiple model outputs using LLM-as-judge.

    Returns quality evaluations for each output.
    """
    pass


@router.post("/blend")
async def blend_outputs(
    outputs: List[ModelOutput],
    method: AggregationMethod,
    user_id: str = Depends(verify_api_key)
) -> str:
    """
    Blend multiple outputs using specified method.

    Returns the blended/merged content.
    """
    pass


# Cost management
@router.get("/costs")
async def get_cost_summary(
    user_id: str = Depends(verify_api_key)
) -> CostTracker:
    """Get current cost tracking summary."""
    pass


@router.put("/costs/limits")
async def update_cost_limits(
    daily_limit: Optional[float] = None,
    monthly_limit: Optional[float] = None,
    user_id: str = Depends(verify_api_key)
) -> CostTracker:
    """Update user's cost limits."""
    pass


@router.get("/costs/estimate")
async def estimate_cost(
    request: EnsembleRequest,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, float]:
    """
    Estimate cost before running ensemble.

    Returns estimated cost breakdown by model.
    """
    pass


# Model health
@router.get("/models/status")
async def get_model_status() -> Dict[str, Any]:
    """
    Get current status of all ensemble models.

    Returns availability, latency, and error rates.
    """
    pass
```

### Integration Points

| Component | Integration Method | Purpose |
|-----------|-------------------|---------|
| `src/text_generation/core.py` | Extend LLMProvider | Add ensemble provider type |
| `src/types/providers.py` | New EnsembleConfig | Ensemble configuration |
| `src/blog/make_blog.py` | Optional ensemble mode | Use ensemble for generation |
| `app/routes/blog.py` | Add ensemble parameter | Enable ensemble via API |
| Frontend ContentGenerator | Model selector UI | Choose ensemble preset |

### New Dependencies

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
# All providers already in place
# Additional for ensemble:
tenacity = "^8.2.0"          # Retry logic for API calls
aiolimiter = "^1.1.0"        # Async rate limiting
sentence-transformers = "^2.2.0"  # For semantic dedup
rouge-score = "^0.1.2"       # For output comparison
```

### Complexity and Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Implementation Complexity | **Very High** | Parallel async, aggregation algorithms, cost tracking |
| API Cost Risk | **Very High** | Multiple models multiply costs; needs strict budgeting |
| Technical Risk | **High** | Cross-provider latency variance, failure handling |
| UX Risk | **Medium** | Users need to understand value vs. cost tradeoff |
| Quality Risk | **Low** | Ensemble generally improves quality |

**Key Risks:**
1. Cost explosion without proper budgeting
2. Slowest model determines overall latency
3. Aggregation quality depends on algorithm tuning
4. API rate limits across multiple providers

### Performance Considerations

```yaml
performance_targets:
  latency:
    parallel_mode: max(individual_latencies) + 500ms
    cascading_mode: sum(individual_latencies)
    target_p95: < 30s for full blog post

  throughput:
    concurrent_requests: 10 per user
    rate_limit: 5 ensemble requests/minute

cost_optimization:
  budget_enforcement: strict
  fallback_on_budget_exceeded: single_model
  cost_estimation_before_run: required

  model_fallback_chain:
    - primary: claude-opus-4
    - fallback_1: gpt-4-turbo
    - fallback_2: gemini-1.5-pro
    - fallback_3: gpt-4o-mini

parallelization:
  framework: asyncio.gather
  timeout_per_model: 60s
  fail_fast: false
  partial_results: true

caching:
  prompt_hash_cache: true
  cache_individual_outputs: false
  cache_final_ensemble: true
  ttl: 1 hour
```

---

## F10: Agent-Based Deep Research

### Overview

Autonomous AI agents that conduct multi-step research across web sources, academic papers, and databases to gather comprehensive information before content generation. Agents plan their research strategy, execute parallel searches, validate sources, and synthesize findings.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AGENT-BASED DEEP RESEARCH ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Research Orchestrator                            │   │
│  │                      POST /research/start                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Research Planner Agent                           │   │
│  │                                                                       │   │
│  │  Input: Topic + Keywords + Depth Level                                │   │
│  │                    │                                                  │   │
│  │                    ▼                                                  │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │              Research Plan Generation                           │  │   │
│  │  │                                                                 │  │   │
│  │  │  1. Decompose topic into sub-questions                          │  │   │
│  │  │  2. Identify required source types                              │  │   │
│  │  │  3. Plan search queries for each source                         │  │   │
│  │  │  4. Estimate time and resource requirements                     │  │   │
│  │  │  5. Define validation criteria                                  │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Execution Pool                             │   │
│  │                      (Parallel execution with Celery/asyncio)         │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐ │   │
│  │  │  Web Search     │ │  Academic       │ │  Specialized DB         │ │   │
│  │  │  Agent          │ │  Search Agent   │ │  Agent                  │ │   │
│  │  │                 │ │                 │ │                         │ │   │
│  │  │  - Google SERP  │ │  - Semantic     │ │  - SEC Filings          │ │   │
│  │  │  - Tavily AI    │ │    Scholar      │ │  - Wikipedia API        │ │   │
│  │  │  - Metaphor     │ │  - arXiv        │ │  - News APIs            │ │   │
│  │  │  - News API     │ │  - PubMed       │ │  - Wikidata             │ │   │
│  │  │  - Reddit       │ │  - CrossRef     │ │  - Crunchbase           │ │   │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────────────┘ │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐ │   │
│  │  │  Content        │ │  Fact Check     │ │  Expert Opinion         │ │   │
│  │  │  Crawler Agent  │ │  Agent          │ │  Agent                  │ │   │
│  │  │                 │ │                 │ │                         │ │   │
│  │  │  - URL fetch    │ │  - Cross-ref    │ │  - Twitter/X            │ │   │
│  │  │  - HTML parse   │ │    sources      │ │  - LinkedIn             │ │   │
│  │  │  - Content      │ │  - Date verify  │ │  - Industry blogs       │ │   │
│  │  │    extract      │ │  - Citation     │ │  - Podcast transcripts  │ │   │
│  │  │  - PDF parse    │ │    check        │ │                         │ │   │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Research State Manager                           │   │
│  │                      (Redis + PostgreSQL)                             │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  Session State                                                  │  │   │
│  │  │  - Research plan                                                │  │   │
│  │  │  - Agent statuses                                               │  │   │
│  │  │  - Collected sources                                            │  │   │
│  │  │  - Intermediate findings                                        │  │   │
│  │  │  - Error log                                                    │  │   │
│  │  │  - Progress metrics                                             │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Synthesis Agent                                  │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  Source Aggregation                                             │  │   │
│  │  │  - Deduplicate findings                                         │  │   │
│  │  │  - Resolve conflicts                                            │  │   │
│  │  │  - Rank by credibility                                          │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  Knowledge Synthesis (LLM)                                      │  │   │
│  │  │  - Generate structured summary                                  │  │   │
│  │  │  - Extract key facts with citations                             │  │   │
│  │  │  - Identify knowledge gaps                                      │  │   │
│  │  │  - Suggest follow-up research                                   │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Quality Validation                               │   │
│  │                                                                       │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐   │   │
│  │  │  Source      │ │  Recency     │ │  Bias        │ │  Coverage  │   │   │
│  │  │  Credibility │ │  Check       │ │  Detection   │ │  Analysis  │   │   │
│  │  │  Score       │ │              │ │              │ │            │   │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Research → Content Pipeline                      │   │
│  │                                                                       │   │
│  │  ResearchReport ──▶ content_outline.py ──▶ make_blog.py ──▶ BlogPost │   │
│  │                                                                       │   │
│  │  Features:                                                            │   │
│  │  - Auto-insert citations                                              │   │
│  │  - Generate fact-backed claims                                        │   │
│  │  - Include expert quotes                                              │   │
│  │  - Add statistics with sources                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│                   ┌────────────────────┐                                     │
│                   │  ResearchReport    │                                     │
│                   │  + Sources         │                                     │
│                   │  + Findings        │                                     │
│                   │  + Citations       │                                     │
│                   └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

```python
# src/types/research_agent.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional


class ResearchDepth(str, Enum):
    QUICK = "quick"           # 5-10 sources, < 2 minutes
    STANDARD = "standard"     # 20-30 sources, < 5 minutes
    DEEP = "deep"             # 50+ sources, < 15 minutes
    EXHAUSTIVE = "exhaustive" # 100+ sources, < 30 minutes


class AgentType(str, Enum):
    WEB_SEARCH = "web_search"
    ACADEMIC = "academic"
    DATABASE = "database"
    CRAWLER = "crawler"
    FACT_CHECK = "fact_check"
    EXPERT = "expert"
    PLANNER = "planner"
    SYNTHESIZER = "synthesizer"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    WEB_PAGE = "web_page"
    ACADEMIC_PAPER = "academic_paper"
    NEWS_ARTICLE = "news_article"
    GOVERNMENT_DOC = "government_doc"
    SOCIAL_MEDIA = "social_media"
    DATABASE_RECORD = "database_record"
    EXPERT_OPINION = "expert_opinion"
    BOOK = "book"


@dataclass
class ResearchQuery:
    """A single research query to execute."""
    id: str
    query: str
    source_types: List[SourceType]
    agent_type: AgentType
    priority: int                  # 1-10, higher = more important
    max_results: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchPlan:
    """Complete research plan generated by planner agent."""
    id: str
    topic: str
    sub_questions: List[str]
    queries: List[ResearchQuery]
    estimated_time_minutes: int
    estimated_sources: int
    depth: ResearchDepth
    created_at: datetime


@dataclass
class Source:
    """A discovered source from research."""
    id: str
    url: str
    title: str
    source_type: SourceType
    content: str                   # Extracted text
    author: Optional[str]
    publish_date: Optional[datetime]
    credibility_score: float       # 0-1
    relevance_score: float         # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """A specific finding/fact extracted from sources."""
    id: str
    claim: str
    supporting_sources: List[str]  # Source IDs
    confidence: float              # 0-1
    category: str                  # e.g., "statistic", "quote", "fact"
    contradicting_sources: List[str] = field(default_factory=list)
    needs_verification: bool = False


@dataclass
class Citation:
    """A formatted citation for content."""
    source_id: str
    format: Literal["apa", "mla", "chicago", "inline"]
    text: str
    url: str


@dataclass
class AgentState:
    """State of a single research agent."""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    query: Optional[ResearchQuery]
    sources_found: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ResearchSession:
    """Complete research session state."""
    session_id: str
    user_id: str
    topic: str
    keywords: List[str]
    depth: ResearchDepth
    plan: Optional[ResearchPlan]
    agents: List[AgentState]
    sources: List[Source]
    findings: List[Finding]
    status: Literal["planning", "researching", "synthesizing", "completed", "failed"]
    progress_percent: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ResearchReport:
    """Final research report output."""
    session_id: str
    topic: str
    executive_summary: str
    key_findings: List[Finding]
    sources_summary: Dict[str, int]  # source_type -> count
    timeline: List[Dict[str, Any]]   # Chronological findings
    expert_quotes: List[Dict[str, str]]
    statistics: List[Dict[str, Any]]
    knowledge_gaps: List[str]
    suggested_follow_up: List[str]
    citations: List[Citation]
    full_sources: List[Source]
    metadata: Dict[str, Any]


@dataclass
class ResearchRequest:
    """Request to start a research session."""
    topic: str
    keywords: Optional[List[str]] = None
    depth: ResearchDepth = ResearchDepth.STANDARD
    focus_areas: Optional[List[str]] = None
    exclude_sources: Optional[List[str]] = None
    required_source_types: Optional[List[SourceType]] = None
    max_sources: int = 50
    timeout_minutes: int = 15
    callback_url: Optional[str] = None  # Webhook for completion


@dataclass
class AgentConfig:
    """Configuration for agent execution."""
    max_concurrent_agents: int = 5
    timeout_per_agent_seconds: int = 120
    retry_count: int = 2
    enable_caching: bool = True
    cache_ttl_hours: int = 24
```

### API Design

```python
# app/routes/research_agent.py

from fastapi import APIRouter, WebSocket, Depends, HTTPException, BackgroundTasks

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/start")
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_api_key)
) -> ResearchSession:
    """
    Start an autonomous research session.

    This endpoint returns immediately with a session ID.
    Research runs in the background.
    Use /research/{session_id}/status or WebSocket for updates.
    """
    pass


@router.get("/{session_id}")
async def get_research_session(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> ResearchSession:
    """Get current state of a research session."""
    pass


@router.get("/{session_id}/report")
async def get_research_report(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> ResearchReport:
    """
    Get the final research report.

    Only available when session status is 'completed'.
    """
    pass


@router.websocket("/ws/{session_id}")
async def websocket_research_updates(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Depends(verify_api_key)
):
    """
    Real-time research progress updates.

    Server sends:
    - agent_status: Agent started/completed/failed
    - source_found: New source discovered
    - finding: New finding extracted
    - progress: Overall progress update
    - completed: Research finished
    - error: Error occurred
    """
    pass


@router.post("/{session_id}/cancel")
async def cancel_research(
    session_id: str,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, str]:
    """Cancel a running research session."""
    pass


@router.post("/{session_id}/extend")
async def extend_research(
    session_id: str,
    additional_queries: List[str],
    user_id: str = Depends(verify_api_key)
) -> ResearchSession:
    """
    Extend a completed research session with additional queries.

    Adds new queries to the existing findings.
    """
    pass


# Research to content pipeline
@router.post("/{session_id}/to-blog")
async def research_to_blog(
    session_id: str,
    title: Optional[str] = None,
    tone: str = "informative",
    include_citations: bool = True,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Generate a blog post from research findings.

    Automatically incorporates:
    - Key findings as content sections
    - Statistics with citations
    - Expert quotes
    - Source references
    """
    pass


@router.post("/{session_id}/to-outline")
async def research_to_outline(
    session_id: str,
    num_sections: int = 5,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Generate a content outline from research findings."""
    pass


# Source management
@router.get("/{session_id}/sources")
async def get_sources(
    session_id: str,
    source_type: Optional[SourceType] = None,
    min_credibility: float = 0.0,
    user_id: str = Depends(verify_api_key)
) -> List[Source]:
    """Get sources from a research session with optional filtering."""
    pass


@router.post("/{session_id}/sources/{source_id}/validate")
async def validate_source(
    session_id: str,
    source_id: str,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Run additional validation on a specific source.

    Checks:
    - URL still accessible
    - Content hasn't changed
    - Cross-references with other sources
    """
    pass


# Agent control
@router.get("/agents/types")
async def list_agent_types() -> List[Dict[str, Any]]:
    """List available agent types and their capabilities."""
    pass


@router.post("/agents/test/{agent_type}")
async def test_agent(
    agent_type: AgentType,
    test_query: str,
    user_id: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Test a specific agent with a sample query."""
    pass
```

### Agent Framework Options

```python
# src/research/agent_framework.py

"""
Agent Framework Comparison for Deep Research

Option 1: Custom Async Framework (Recommended)
- Full control over execution
- Lightweight, no heavy dependencies
- Easy to debug and extend
- Integrates directly with existing code

Option 2: LangChain Agents
- Pre-built agent patterns
- Tool abstraction layer
- Memory management built-in
- Heavier dependency, less control

Option 3: AutoGPT-style
- Fully autonomous
- Self-planning capabilities
- Higher complexity, harder to debug
- May generate unexpected queries
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio


class BaseResearchAgent(ABC):
    """Base class for all research agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.PENDING
        self.results: List[Source] = []

    @abstractmethod
    async def execute(self, query: ResearchQuery) -> List[Source]:
        """Execute the research query and return sources."""
        pass

    @abstractmethod
    async def validate_source(self, source: Source) -> float:
        """Validate a source and return credibility score."""
        pass

    async def run_with_retry(self, query: ResearchQuery) -> List[Source]:
        """Execute with retry logic."""
        for attempt in range(self.config.retry_count + 1):
            try:
                self.status = AgentStatus.RUNNING
                results = await asyncio.wait_for(
                    self.execute(query),
                    timeout=self.config.timeout_per_agent_seconds
                )
                self.status = AgentStatus.COMPLETED
                return results
            except asyncio.TimeoutError:
                if attempt == self.config.retry_count:
                    self.status = AgentStatus.FAILED
                    raise
            except Exception as e:
                if attempt == self.config.retry_count:
                    self.status = AgentStatus.FAILED
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return []


class ResearchOrchestrator:
    """Orchestrates multiple research agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agents: Dict[AgentType, BaseResearchAgent] = {}
        self.session: Optional[ResearchSession] = None

    async def execute_plan(self, plan: ResearchPlan) -> List[Source]:
        """Execute a research plan with parallel agents."""

        # Group queries by agent type for parallel execution
        query_groups = self._group_queries_by_agent(plan.queries)

        all_sources = []

        # Execute in waves of max_concurrent_agents
        for wave in self._create_execution_waves(query_groups):
            tasks = [
                self._execute_query(query)
                for query in wave
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_sources.extend(result)

        return all_sources

    def _create_execution_waves(
        self,
        query_groups: Dict[AgentType, List[ResearchQuery]]
    ) -> List[List[ResearchQuery]]:
        """Create execution waves respecting concurrency limits."""
        # Implementation details...
        pass
```

### Integration Points

| Component | Integration Method | Purpose |
|-----------|-------------------|---------|
| `src/research/web_researcher.py` | Extend as agent | Web search agent base |
| `src/text_generation/core.py` | Planner/Synthesizer | LLM for planning and synthesis |
| `src/blog/make_blog.py` | Add research injection | Use research in content |
| `src/planning/content_outline.py` | Research-aware outline | Structure from findings |
| `app/routes/blog.py` | Deep research option | Enable agent research |
| Redis | State management | Session and agent state |
| Celery (optional) | Background tasks | Long-running research jobs |

### New Dependencies

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
# Web scraping and parsing
trafilatura = "^1.6.0"      # Web content extraction
newspaper3k = "^0.2.8"      # Article parsing
pdfplumber = "^0.10.0"      # PDF text extraction
arxiv = "^2.0.0"            # arXiv paper search

# Academic/database APIs
scholarly = "^1.7.0"        # Google Scholar
semanticscholar = "^0.5.0"  # Semantic Scholar API
crossref-commons = "^0.0.7" # CrossRef API

# Background processing
celery = "^5.3.0"           # Task queue (optional)
redis = "^5.0.0"            # State management

# Fact checking
duckduckgo-search = "^4.0.0"  # Alternative search
```

### Complexity and Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Implementation Complexity | **Very High** | Agent orchestration, state management, source validation |
| API Cost Risk | **High** | Multiple API calls per research session |
| Technical Risk | **High** | Unpredictable agent behavior, source availability |
| UX Risk | **Medium** | Long-running jobs need clear progress feedback |
| Legal Risk | **Medium** | Web scraping, content extraction, citation requirements |

**Key Risks:**
1. Agent execution time unpredictability
2. Source websites blocking crawlers
3. Academic API rate limits
4. Content extraction quality varies by site
5. Legal concerns with scraping copyrighted content

### Performance Considerations

```yaml
performance_targets:
  research_time:
    quick: < 2 minutes
    standard: < 5 minutes
    deep: < 15 minutes
    exhaustive: < 30 minutes

  concurrent_sessions:
    per_user: 3
    system_total: 100

state_management:
  backend: redis
  session_ttl: 24 hours
  source_cache_ttl: 7 days

  persistence:
    completed_sessions: postgresql
    retention: 30 days

agent_execution:
  max_concurrent_agents: 5
  timeout_per_agent: 120 seconds
  retry_count: 2
  backoff_strategy: exponential

resource_limits:
  max_sources_per_session: 200
  max_content_size_per_source: 100KB
  max_pdf_pages: 50

scaling:
  research_workers: horizontal (celery)
  crawler_pool: dedicated instances
  rate_limit_sharing: per-worker buckets
```

---

## Cross-Feature Integration Matrix

| Feature | F7 Voice | F8 SEO | F9 Ensemble | F10 Research |
|---------|----------|--------|-------------|--------------|
| F7 Voice | - | Voice triggers SEO check | Voice selects ensemble | Voice starts research |
| F8 SEO | SEO scores voice content | - | Ensemble optimizes for SEO | Research informs SEO targets |
| F9 Ensemble | Ensemble transcribes voice | SEO-specialized model | - | Ensemble synthesizes research |
| F10 Research | Research enhances voice notes | Research supports SEO claims | Research feeds ensemble | - |

---

## Shared Infrastructure Requirements

### Redis Cache Layer

```yaml
redis_configuration:
  voice_sessions:
    key_pattern: "voice:{session_id}"
    ttl: 3600

  seo_cache:
    key_pattern: "seo:{keyword_hash}"
    ttl: 604800

  ensemble_cost:
    key_pattern: "ensemble:cost:{user_id}"
    ttl: 86400

  research_state:
    key_pattern: "research:{session_id}"
    ttl: 86400
```

### Database Additions

```sql
-- migrations/tier3_features.sql

-- Voice sessions table
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    mode VARCHAR(20),
    intent VARCHAR(30),
    transcript TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- SEO analysis history
CREATE TABLE seo_analyses (
    id UUID PRIMARY KEY,
    conversation_id UUID,
    content_hash VARCHAR(64),
    score_total INT,
    analysis_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ensemble usage tracking
CREATE TABLE ensemble_usage (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    models_used TEXT[],
    total_cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Research sessions
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    topic TEXT,
    depth VARCHAR(20),
    status VARCHAR(20),
    sources_count INT,
    report_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Research sources
CREATE TABLE research_sources (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES research_sessions(id),
    url TEXT,
    title TEXT,
    source_type VARCHAR(30),
    credibility_score DECIMAL(3, 2),
    content_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Environment Variables

```bash
# .env additions for Tier 3 features

# F7: Voice Input
WHISPER_API_KEY=${OPENAI_API_KEY}  # Uses OpenAI
DEEPGRAM_API_KEY=                   # Optional alternative
ASSEMBLYAI_API_KEY=                 # Optional alternative

# F8: Live SEO
SEMRUSH_API_KEY=
AHREFS_API_KEY=
MOZ_API_KEY=
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
SEO_API_BUDGET_MONTHLY=50.00

# F9: Ensemble
ENSEMBLE_ENABLED=true
ENSEMBLE_DAILY_BUDGET=10.00
ENSEMBLE_MONTHLY_BUDGET=100.00

# F10: Research Agents
RESEARCH_ENABLED=true
SEMANTIC_SCHOLAR_API_KEY=
CROSSREF_API_KEY=
CELERY_BROKER_URL=redis://localhost:6379/0
RESEARCH_MAX_CONCURRENT=5
```

---

## Implementation Priority and Dependencies

```
Phase 1 (Foundation):
├── F9: Multi-LLM Ensemble (extends existing core.py)
│   └── Enables quality improvements across all features
│
Phase 2 (Enhancement):
├── F8: Live SEO Mode
│   └── Depends on: Ensemble (optional SEO-optimized model)
│
Phase 3 (Advanced):
├── F10: Agent-Based Research
│   └── Depends on: Ensemble (synthesis), SEO (keyword targets)
│
Phase 4 (Innovation):
└── F7: Voice Input
    └── Depends on: Research (voice-to-research), Ensemble (transcription)
```

---

## Summary

These Tier 3 features represent significant architectural expansions to Blog AI:

1. **F7 Voice Input**: Adds real-time audio streaming, speech-to-text, and voice command parsing
2. **F8 Live SEO**: Integrates expensive SEO APIs with careful caching and budget management
3. **F9 Multi-LLM Ensemble**: Parallel generation across providers with voting/blending algorithms
4. **F10 Agent Research**: Autonomous multi-step research with source validation and synthesis

Each feature maintains integration with the existing modular pipeline architecture while adding new capabilities through well-defined interfaces and data models.
