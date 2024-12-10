"""Chat-based content assistant for iterative content creation.

Provides a conversational interface that supports generating, editing,
scoring, and refining content with optional brand voice and knowledge
base integration.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..text_generation.core import (
    GenerationOptions,
    LLMProvider,
    TextGenerationError,
    create_provider_from_env,
    generate_text_async,
)
from ..types.providers import ProviderType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class UserIntent(str, Enum):
    GENERATE = "generate"
    EDIT = "edit"
    REFINE = "refine"
    SCORE = "score"
    RESEARCH = "research"
    EXPLAIN = "explain"
    TRANSLATE = "translate"
    SHORTEN = "shorten"
    EXPAND = "expand"
    CHANGE_TONE = "change_tone"
    GENERAL = "general"


@dataclass
class ChatMessage:
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatContext:
    """Accumulated state for a single chat conversation."""

    messages: List[ChatMessage] = field(default_factory=list)
    brand_voice_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    working_content: Optional[str] = None
    content_type: Optional[str] = None  # blog, email, social, etc.

    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.messages.append(ChatMessage(role=role, content=content, metadata=metadata))

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class ChatResponse:
    message: str
    updated_content: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Intent detection patterns (fast path before LLM fallback)
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: Dict[UserIntent, List[re.Pattern]] = {
    UserIntent.GENERATE: [
        re.compile(r"\b(write|create|generate|draft|compose|produce)\b", re.IGNORECASE),
    ],
    UserIntent.EDIT: [
        re.compile(r"\b(edit|change|modify|replace|fix|correct|update)\b", re.IGNORECASE),
    ],
    UserIntent.REFINE: [
        re.compile(r"\b(refine|improve|polish|enhance|rewrite|rework|rephrase)\b", re.IGNORECASE),
    ],
    UserIntent.SCORE: [
        re.compile(r"\b(score|rate|evaluate|analyze|assess|grade|review|critique)\b", re.IGNORECASE),
    ],
    UserIntent.RESEARCH: [
        re.compile(r"\b(research|look up|find out|search|investigate)\b", re.IGNORECASE),
    ],
    UserIntent.EXPLAIN: [
        re.compile(r"\b(explain|what is|what are|how does|tell me about|describe)\b", re.IGNORECASE),
    ],
    UserIntent.TRANSLATE: [
        re.compile(r"\b(translate|in (spanish|french|german|chinese|japanese|korean|portuguese|italian))\b", re.IGNORECASE),
    ],
    UserIntent.SHORTEN: [
        re.compile(r"\b(shorten|shorter|condense|summarize|summarise|brief|concise|trim|cut down)\b", re.IGNORECASE),
    ],
    UserIntent.EXPAND: [
        re.compile(r"\b(expand|longer|elaborate|extend|more detail|flesh out|add more)\b", re.IGNORECASE),
    ],
    UserIntent.CHANGE_TONE: [
        re.compile(r"\b(tone|make it (more )?(formal|casual|friendly|professional|playful|serious|authoritative))\b", re.IGNORECASE),
    ],
}

# Maximum number of conversation history messages included in the prompt
MAX_HISTORY_MESSAGES = 20

# Maximum working content length included in system prompt (chars)
MAX_WORKING_CONTENT_IN_PROMPT = 8000


class ChatEngine:
    """Core engine for chat-based content creation.

    Responsible for building LLM prompts with appropriate context (brand
    voice, knowledge base, working content), detecting user intent, and
    dispatching to the correct handler.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_type: ProviderType = "openai",
        options: Optional[GenerationOptions] = None,
    ):
        self._provider = provider
        self._provider_type = provider_type
        self._options = options or GenerationOptions(
            temperature=0.7,
            max_tokens=4000,
            top_p=0.95,
        )

    # ------------------------------------------------------------------
    # Provider management
    # ------------------------------------------------------------------

    def _get_provider(self, provider_type: Optional[ProviderType] = None) -> LLMProvider:
        """Return the cached provider or create one from environment."""
        pt = provider_type or self._provider_type
        if self._provider and (not provider_type or provider_type == self._provider_type):
            return self._provider
        return create_provider_from_env(pt)

    # ------------------------------------------------------------------
    # System prompt construction
    # ------------------------------------------------------------------

    def build_system_prompt(
        self,
        context: ChatContext,
        brand_voice_summary: Optional[str] = None,
        knowledge_context: Optional[str] = None,
    ) -> str:
        """Build the system prompt incorporating brand voice, knowledge base,
        and working content when available."""

        parts: List[str] = [
            "You are a content creation assistant. You help users create, edit, "
            "and refine content iteratively through conversation.",
            "",
            "Guidelines:",
            "- When editing content, return the FULL updated content, not just the changed parts.",
            "- When asked to generate, produce high-quality content matching the requested format.",
            "- When asked to score or analyze, provide specific actionable feedback with a numeric score.",
            "- Be concise in your conversational responses but thorough in content output.",
            "- If the user refers to 'the content' or 'it', they mean the working content shown below.",
        ]

        if brand_voice_summary:
            parts.append("")
            parts.append("BRAND VOICE GUIDELINES:")
            parts.append(
                "Apply the following brand voice consistently to all content you produce:"
            )
            parts.append(brand_voice_summary)

        if knowledge_context:
            parts.append("")
            parts.append("KNOWLEDGE BASE CONTEXT:")
            parts.append(
                "Use the following information for factual grounding. "
                "Cite sources when appropriate:"
            )
            parts.append(knowledge_context)

        if context.working_content:
            truncated = context.working_content[:MAX_WORKING_CONTENT_IN_PROMPT]
            if len(context.working_content) > MAX_WORKING_CONTENT_IN_PROMPT:
                truncated += "\n\n[Content truncated for brevity]"
            parts.append("")
            parts.append("CURRENT WORKING CONTENT:")
            parts.append(truncated)

        if context.content_type:
            parts.append("")
            parts.append(f"Content type: {context.content_type}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def detect_intent(self, message: str) -> UserIntent:
        """Classify user intent using pattern matching.

        Matches are scored by the number of pattern hits; the intent with
        the most matches wins.  Falls back to GENERAL when nothing matches.
        """
        scores: Dict[UserIntent, int] = {}
        for intent, patterns in _INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(message):
                    scores[intent] = scores.get(intent, 0) + 1

        if not scores:
            return UserIntent.GENERAL

        return max(scores, key=lambda k: scores[k])

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process_message(
        self,
        user_message: str,
        context: ChatContext,
        provider_type: Optional[ProviderType] = None,
        options: Optional[GenerationOptions] = None,
        brand_voice_summary: Optional[str] = None,
        knowledge_context: Optional[str] = None,
    ) -> ChatResponse:
        """Process an incoming user message and return a response.

        This is the primary public API.  It detects intent, delegates to
        the appropriate handler, updates the context, and returns a
        ``ChatResponse``.
        """
        opts = options or self._options
        provider = self._get_provider(provider_type)

        # Record the user message in context history
        context.add_message(MessageRole.USER, user_message)

        intent = self.detect_intent(user_message)
        logger.info("Chat intent detected: %s for message length=%d", intent.value, len(user_message))

        try:
            if intent == UserIntent.SCORE:
                response = await self._handle_score_request(user_message, context, provider, opts)
            elif intent in (UserIntent.EDIT, UserIntent.REFINE, UserIntent.SHORTEN, UserIntent.EXPAND, UserIntent.CHANGE_TONE):
                response = await self._handle_edit_request(
                    user_message, context, provider, opts, brand_voice_summary, knowledge_context, intent,
                )
            elif intent == UserIntent.GENERATE:
                response = await self._handle_generate_request(
                    user_message, context, provider, opts, brand_voice_summary, knowledge_context,
                )
            elif intent == UserIntent.TRANSLATE:
                response = await self._handle_translate_request(
                    user_message, context, provider, opts,
                )
            else:
                response = await self._handle_general_request(
                    user_message, context, provider, opts, brand_voice_summary, knowledge_context,
                )

            # Record assistant message in context
            context.add_message(
                MessageRole.ASSISTANT,
                response.message,
                metadata={"intent": intent.value, **(response.metadata or {})},
            )

            # If the response updated content, persist it in context
            if response.updated_content is not None:
                context.working_content = response.updated_content

            response.metadata["intent"] = intent.value
            return response

        except TextGenerationError as exc:
            logger.error("LLM generation failed during chat: %s", exc)
            error_response = ChatResponse(
                message="I encountered an error generating a response. Please try again.",
                metadata={"error": True, "intent": intent.value},
            )
            context.add_message(
                MessageRole.ASSISTANT,
                error_response.message,
                metadata={"error": True},
            )
            return error_response

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------

    async def _handle_generate_request(
        self,
        message: str,
        context: ChatContext,
        provider: LLMProvider,
        options: GenerationOptions,
        brand_voice_summary: Optional[str] = None,
        knowledge_context: Optional[str] = None,
    ) -> ChatResponse:
        system_prompt = self.build_system_prompt(context, brand_voice_summary, knowledge_context)

        prompt = self._build_conversation_prompt(system_prompt, context)

        raw = await generate_text_async(prompt, provider, options)
        content = raw.strip()

        return ChatResponse(
            message=content,
            updated_content=content,
            suggestions=self._generate_suggestions("generate"),
            metadata={"action": "generated"},
        )

    async def _handle_edit_request(
        self,
        message: str,
        context: ChatContext,
        provider: LLMProvider,
        options: GenerationOptions,
        brand_voice_summary: Optional[str] = None,
        knowledge_context: Optional[str] = None,
        intent: UserIntent = UserIntent.EDIT,
    ) -> ChatResponse:
        if not context.working_content:
            return ChatResponse(
                message="There is no working content to edit. Please generate or provide content first.",
                suggestions=[
                    "Generate a blog post about [topic]",
                    "Paste your existing content so I can edit it",
                ],
                metadata={"action": "no_content"},
            )

        system_prompt = self.build_system_prompt(context, brand_voice_summary, knowledge_context)

        edit_instruction = (
            f"\n\nThe user wants to {intent.value} the working content. "
            f"Their instruction: {message}\n\n"
            "Return the FULL updated content. Do not include explanations "
            "before or after the content unless specifically asked."
        )

        prompt = self._build_conversation_prompt(system_prompt + edit_instruction, context)

        raw = await generate_text_async(prompt, provider, options)
        updated = raw.strip()

        return ChatResponse(
            message=updated,
            updated_content=updated,
            suggestions=self._generate_suggestions("edit"),
            metadata={"action": intent.value},
        )

    async def _handle_score_request(
        self,
        message: str,
        context: ChatContext,
        provider: LLMProvider,
        options: GenerationOptions,
    ) -> ChatResponse:
        if not context.working_content:
            return ChatResponse(
                message="There is no content to score. Please generate or provide content first.",
                suggestions=[
                    "Generate a blog post about [topic]",
                    "Paste your content so I can analyze it",
                ],
                metadata={"action": "no_content"},
            )

        score_prompt = f"""Analyze and score the following content. Provide:
1. An overall quality score from 1-10
2. Readability score (1-10)
3. SEO effectiveness (1-10) if applicable
4. Engagement potential (1-10)
5. Specific strengths (2-3 bullet points)
6. Specific improvements (2-3 bullet points)
7. A brief summary recommendation

CONTENT TO ANALYZE:
{context.working_content[:MAX_WORKING_CONTENT_IN_PROMPT]}

Respond with a structured analysis. Be specific and actionable in your feedback."""

        # Use lower temperature for scoring to get more consistent results
        score_options = GenerationOptions(
            temperature=0.3,
            max_tokens=options.max_tokens,
            top_p=options.top_p,
        )

        raw = await generate_text_async(score_prompt, provider, score_options)
        analysis = raw.strip()

        return ChatResponse(
            message=analysis,
            suggestions=self._generate_suggestions("score"),
            metadata={"action": "scored"},
        )

    async def _handle_translate_request(
        self,
        message: str,
        context: ChatContext,
        provider: LLMProvider,
        options: GenerationOptions,
    ) -> ChatResponse:
        if not context.working_content:
            return ChatResponse(
                message="There is no content to translate. Please generate or provide content first.",
                suggestions=["Generate content first, then ask me to translate it"],
                metadata={"action": "no_content"},
            )

        translate_prompt = (
            f"Translate the following content based on this instruction: {message}\n\n"
            f"CONTENT:\n{context.working_content[:MAX_WORKING_CONTENT_IN_PROMPT]}\n\n"
            "Return only the translated content without any additional commentary."
        )

        raw = await generate_text_async(translate_prompt, provider, options)
        translated = raw.strip()

        return ChatResponse(
            message=translated,
            updated_content=translated,
            suggestions=["Translate to another language", "Revert to the original"],
            metadata={"action": "translated"},
        )

    async def _handle_general_request(
        self,
        message: str,
        context: ChatContext,
        provider: LLMProvider,
        options: GenerationOptions,
        brand_voice_summary: Optional[str] = None,
        knowledge_context: Optional[str] = None,
    ) -> ChatResponse:
        system_prompt = self.build_system_prompt(context, brand_voice_summary, knowledge_context)
        prompt = self._build_conversation_prompt(system_prompt, context)

        raw = await generate_text_async(prompt, provider, options)

        return ChatResponse(
            message=raw.strip(),
            suggestions=self._generate_suggestions("general"),
            metadata={"action": "general"},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_conversation_prompt(self, system_prompt: str, context: ChatContext) -> str:
        """Build a single prompt string from the system prompt and
        recent conversation history.

        The format follows a ``System / User / Assistant`` transcript that
        works with both chat and completion endpoints.
        """
        parts: List[str] = [f"System:\n{system_prompt}\n"]

        # Include recent history (skip the very last user message since it
        # is already part of the conversation flow)
        recent = context.messages[-MAX_HISTORY_MESSAGES:]
        for msg in recent:
            role_label = msg.role.value.capitalize()
            parts.append(f"{role_label}:\n{msg.content}\n")

        parts.append("Assistant:\n")
        return "\n".join(parts)

    @staticmethod
    def _generate_suggestions(action_type: str) -> List[str]:
        """Return contextual follow-up suggestions based on the action."""
        suggestions_map: Dict[str, List[str]] = {
            "generate": [
                "Make it shorter",
                "Make it more formal",
                "Add more detail",
                "Score this content",
            ],
            "edit": [
                "Score the updated content",
                "Make it more concise",
                "Change the tone to casual",
                "Expand on the key points",
            ],
            "score": [
                "Improve based on the feedback",
                "Rewrite the weakest section",
                "Make it more engaging",
                "Optimize for SEO",
            ],
            "general": [
                "Write a blog post about [topic]",
                "Help me outline an article",
                "Score my content",
                "Rewrite in a different tone",
            ],
        }
        return suggestions_map.get(action_type, suggestions_map["general"])
