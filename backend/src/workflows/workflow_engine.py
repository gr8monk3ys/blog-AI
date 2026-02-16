"""
Workflow automation engine for chaining content generation steps.

The engine executes a directed acyclic graph (DAG) of steps in dependency
order.  Each step wraps an existing module (blog generation, proofreading,
remix, etc.) and passes its output into the shared execution context so
that downstream steps can reference it.

Design goals:
- Re-use every existing generation / post-processing function as-is.
- Support cancellation at step boundaries.
- Report progress via an optional async callback.
- Never mutate the original Workflow definition during execution.
"""

import asyncio
import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from ..text_generation.core import (
    GenerationOptions,
    LLMProvider,
    create_provider_from_env,
    generate_text,
)
from ..types.providers import ProviderType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StepType(str, Enum):
    """All supported pipeline step types."""

    RESEARCH = "research"
    OUTLINE = "outline"
    GENERATE_BLOG = "generate_blog"
    GENERATE_BOOK = "generate_book"
    PROOFREAD = "proofread"
    HUMANIZE = "humanize"
    SEO_OPTIMIZE = "seo_optimize"
    META_DESCRIPTION = "meta_description"
    STRUCTURED_DATA = "structured_data"
    REMIX = "remix"
    IMAGE_GENERATE = "image_generate"
    PUBLISH_WORDPRESS = "publish_wordpress"
    PUBLISH_MEDIUM = "publish_medium"
    PUBLISH_GITHUB = "publish_github"
    SOCIAL_POST = "social_post"
    CUSTOM_LLM = "custom_llm"


class WorkflowStatus(str, Enum):
    """Lifecycle states shared by workflows, executions, and steps."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class WorkflowStep:
    """A single step inside a workflow."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: StepType = StepType.GENERATE_BLOG
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Workflow:
    """A reusable workflow definition (template)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Tracks a single run of a workflow."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowExecutionError(Exception):
    """Raised when a workflow execution fails."""

    def __init__(self, message: str, step_id: Optional[str] = None):
        super().__init__(message)
        self.step_id = step_id


# ---------------------------------------------------------------------------
# Progress callback type
# ---------------------------------------------------------------------------

ProgressCallback = Callable[
    [str, WorkflowStatus, Optional[str]],
    Coroutine[Any, Any, None],
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class WorkflowEngine:
    """Executes workflow DAGs by dispatching each step to the correct handler."""

    def __init__(self) -> None:
        self._cancelled: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Request cancellation.  Takes effect before the next step starts."""
        self._cancelled = True

    async def execute_workflow(
        self,
        workflow: Workflow,
        variables: Dict[str, Any],
        provider_type: ProviderType = "openai",
        options: Optional[GenerationOptions] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> WorkflowExecution:
        """
        Execute all steps of *workflow* in topological (dependency) order.

        Args:
            workflow: The workflow definition to execute.
            variables: User-supplied runtime variables (topic, keywords, etc.).
            provider_type: Which LLM provider to use for generation steps.
            options: Shared GenerationOptions forwarded to every LLM call.
            progress_callback: Optional ``async`` callback invoked after each
                step finishes.  Signature: ``(step_id, status, message)``.

        Returns:
            A ``WorkflowExecution`` with per-step results.

        Raises:
            WorkflowExecutionError: If a step fails and no recovery is possible.
        """
        self._cancelled = False
        options = options or GenerationOptions()
        provider = await asyncio.to_thread(create_provider_from_env, provider_type)

        # Deep-copy steps so the template is not mutated.
        steps = [copy.deepcopy(s) for s in workflow.steps]

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        # Build a context dict that accumulates step outputs.
        context: Dict[str, Any] = {
            "variables": variables,
            "provider_type": provider_type,
        }

        ordered_steps = self._topological_sort(steps)

        for step in ordered_steps:
            if self._cancelled:
                step.status = WorkflowStatus.CANCELLED
                execution.status = WorkflowStatus.CANCELLED
                execution.completed_at = datetime.now(timezone.utc)
                logger.info("Workflow %s cancelled before step %s", workflow.id, step.id)
                if progress_callback:
                    await progress_callback(step.id, WorkflowStatus.CANCELLED, "Cancelled by user")
                break

            execution.current_step = step.id
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now(timezone.utc)

            if progress_callback:
                await progress_callback(step.id, WorkflowStatus.RUNNING, f"Starting: {step.name}")

            try:
                output = await self.execute_step(step, context, provider, options)
                step.output = output
                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                execution.results[step.id] = output
                context[step.id] = output

                logger.info(
                    "Step %s (%s) completed for workflow %s",
                    step.id,
                    step.name,
                    workflow.id,
                )

                if progress_callback:
                    await progress_callback(step.id, WorkflowStatus.COMPLETED, f"Completed: {step.name}")

            except Exception as exc:
                step.status = WorkflowStatus.FAILED
                step.error = str(exc)
                step.completed_at = datetime.now(timezone.utc)
                execution.status = WorkflowStatus.FAILED
                execution.error = f"Step '{step.name}' ({step.id}) failed: {exc}"
                execution.completed_at = datetime.now(timezone.utc)
                execution.results[step.id] = {"error": str(exc)}

                logger.error(
                    "Step %s (%s) failed in workflow %s: %s",
                    step.id,
                    step.name,
                    workflow.id,
                    exc,
                    exc_info=True,
                )

                if progress_callback:
                    await progress_callback(step.id, WorkflowStatus.FAILED, str(exc))

                raise WorkflowExecutionError(str(exc), step_id=step.id) from exc

        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)

        return execution

    async def execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        provider: LLMProvider,
        options: GenerationOptions,
    ) -> Any:
        """
        Dispatch a single step to the appropriate handler.

        The handler receives the step configuration merged with accumulated
        context from prior steps and the user-supplied variables.
        """
        handler = _STEP_HANDLERS.get(step.type)
        if handler is None:
            raise WorkflowExecutionError(
                f"No handler registered for step type: {step.type}",
                step_id=step.id,
            )
        return await handler(step.config, context, provider, options)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _topological_sort(steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """
        Return *steps* in an order that respects ``depends_on`` constraints.

        Falls back to the original insertion order when there are no
        explicit dependencies.
        """
        step_map = {s.id: s for s in steps}
        visited: set = set()
        result: List[WorkflowStep] = []

        def _visit(step: WorkflowStep) -> None:
            if step.id in visited:
                return
            visited.add(step.id)
            for dep_id in step.depends_on:
                dep = step_map.get(dep_id)
                if dep is not None:
                    _visit(dep)
            result.append(step)

        for s in steps:
            _visit(s)

        return result


# ---------------------------------------------------------------------------
# Step handlers
#
# Each handler is an ``async`` function with the signature:
#   (config, context, provider, options) -> Any
#
# ``config`` is the per-step configuration dict.
# ``context`` accumulates outputs from prior steps keyed by step id,
# plus ``context["variables"]`` which holds user-supplied input.
# ---------------------------------------------------------------------------

def _resolve_content(context: Dict[str, Any]) -> str:
    """Extract the best available content string from context.

    Looks through previous step outputs for blog post content, outline
    text, or raw generated text and returns a single string suitable for
    post-processing steps.
    """
    variables = context.get("variables", {})

    # Walk backwards through context looking for usable content.
    for key, value in reversed(list(context.items())):
        if key == "variables":
            continue
        if isinstance(value, dict):
            # Blog post dict
            if "sections" in value:
                parts = []
                for section in value["sections"]:
                    parts.append(section.get("title", ""))
                    for sub in section.get("subtopics", []):
                        parts.append(sub.get("content", ""))
                return "\n\n".join(p for p in parts if p)
            # Outline dict
            if "outline" in value:
                return value["outline"]
            if "content" in value:
                return value["content"]
            if "text" in value:
                return value["text"]
        if isinstance(value, str) and len(value) > 50:
            return value

    return variables.get("topic", "")


def _resolve_title(context: Dict[str, Any]) -> str:
    """Best-effort title extraction from context."""
    variables = context.get("variables", {})
    for key, value in reversed(list(context.items())):
        if key == "variables":
            continue
        if isinstance(value, dict) and "title" in value:
            return value["title"]
    return variables.get("topic", "Untitled")


def _resolve_keywords(context: Dict[str, Any]) -> List[str]:
    """Best-effort keyword extraction from context."""
    variables = context.get("variables", {})
    kw = variables.get("keywords", [])
    if isinstance(kw, str):
        return [k.strip() for k in kw.split(",") if k.strip()]
    return list(kw) if kw else []


async def _execute_research(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Conduct web research on the topic."""
    from ..research.web_researcher import (
        conduct_web_research,
        extract_research_sources,
        format_research_results_for_prompt,
    )

    variables = context.get("variables", {})
    topic = variables.get("topic", "")
    keywords = _resolve_keywords(context)

    search_terms = [topic] + keywords if topic else keywords
    max_sources = config.get("max_sources", 8)

    results = await asyncio.to_thread(conduct_web_research, search_terms)
    sources = await asyncio.to_thread(extract_research_sources, results, max_sources)
    research_context = await asyncio.to_thread(
        format_research_results_for_prompt, results, max_sources, 2200
    )

    return {
        "research_results": results,
        "sources": sources,
        "research_context": research_context,
    }


async def _execute_outline(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate a content outline."""
    from ..planning.content_outline import (
        generate_content_outline,
        generate_content_outline_with_research,
    )

    variables = context.get("variables", {})
    title = variables.get("topic", "")
    keywords = _resolve_keywords(context)
    num_sections = config.get("sections", 5)

    # Use research-enhanced outline if research output is available.
    has_research = any(
        isinstance(v, dict) and "research_context" in v
        for v in context.values()
    )

    if has_research:
        outline = await asyncio.to_thread(
            generate_content_outline_with_research,
            title,
            keywords,
            num_sections,
            provider,
            options,
        )
    else:
        outline = await asyncio.to_thread(
            generate_content_outline,
            title,
            keywords,
            num_sections,
            provider,
            options,
        )

    return {
        "title": title,
        "sections": outline.sections,
        "outline": "\n".join(outline.sections),
    }


async def _execute_generate_blog(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate a full blog post."""
    from ..blog.make_blog import generate_blog_post, generate_blog_post_with_research

    variables = context.get("variables", {})
    title = variables.get("topic", "")
    keywords = _resolve_keywords(context)
    tone = variables.get("tone", config.get("tone", "informative"))
    brand_voice = variables.get("brand_voice")
    provider_type = context.get("provider_type", "openai")
    num_sections = config.get("sections", 5)

    has_research = any(
        isinstance(v, dict) and "research_context" in v
        for v in context.values()
    )

    if has_research:
        blog_post = await asyncio.to_thread(
            generate_blog_post_with_research,
            title=title,
            keywords=keywords,
            num_sections=num_sections,
            tone=tone,
            brand_voice=brand_voice,
            provider_type=provider_type,
            options=options,
        )
    else:
        blog_post = await asyncio.to_thread(
            generate_blog_post,
            title=title,
            keywords=keywords,
            num_sections=num_sections,
            tone=tone,
            brand_voice=brand_voice,
            provider_type=provider_type,
            options=options,
        )

    # Serialize to dict for downstream steps.
    sections_data = []
    for section in blog_post.sections:
        subtopics_data = [
            {"title": st.title, "content": st.content}
            for st in section.subtopics
        ]
        sections_data.append({"title": section.title, "subtopics": subtopics_data})

    return {
        "title": blog_post.title,
        "description": blog_post.description,
        "date": blog_post.date,
        "tags": blog_post.tags,
        "sections": sections_data,
        "sources": [
            {
                "id": int(getattr(s, "id", 0) or 0),
                "title": str(getattr(s, "title", "") or ""),
                "url": str(getattr(s, "url", "") or ""),
            }
            for s in getattr(blog_post, "sources", []) or []
        ],
    }


async def _execute_generate_book(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate a book or book chapter."""
    from ..book.make_book import generate_book, generate_book_with_research

    variables = context.get("variables", {})
    title = variables.get("topic", "")
    keywords = _resolve_keywords(context)
    tone = variables.get("tone", config.get("tone", "informative"))
    brand_voice = variables.get("brand_voice")
    provider_type = context.get("provider_type", "openai")
    num_chapters = config.get("chapters", 5)
    sections_per_chapter = config.get("sections_per_chapter", 3)

    has_research = any(
        isinstance(v, dict) and "research_context" in v
        for v in context.values()
    )

    if has_research:
        book = await asyncio.to_thread(
            generate_book_with_research,
            title=title,
            num_chapters=num_chapters,
            sections_per_chapter=sections_per_chapter,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider_type=provider_type,
            options=options,
        )
    else:
        book = await asyncio.to_thread(
            generate_book,
            title=title,
            num_chapters=num_chapters,
            sections_per_chapter=sections_per_chapter,
            keywords=keywords,
            tone=tone,
            brand_voice=brand_voice,
            provider_type=provider_type,
            options=options,
        )

    # Serialize book to dict.
    chapters_data = []
    for chapter in book.chapters:
        sections_data = []
        for section in chapter.sections:
            subtopics_data = [
                {"title": st.title, "content": st.content}
                for st in section.subtopics
            ]
            sections_data.append({"title": section.title, "subtopics": subtopics_data})
        chapters_data.append({"title": chapter.title, "sections": sections_data})

    return {
        "title": book.title,
        "chapters": chapters_data,
    }


async def _execute_proofread(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Proofread content from a prior step."""
    from ..post_processing.proofreader import proofread_content

    content = _resolve_content(context)
    if not content:
        return {"corrected_text": "", "issues": []}

    result = await asyncio.to_thread(
        proofread_content,
        content,
        provider=provider,
        generation_options=options,
    )

    corrected = result.corrected_text or content
    issues = [
        {"type": i.type, "text": i.text, "suggestion": i.suggestion}
        for i in result.issues
    ]

    return {"corrected_text": corrected, "issues": issues, "content": corrected}


async def _execute_humanize(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Humanize content to make it sound more natural."""
    from ..post_processing.humanizer import humanize_content

    content = _resolve_content(context)
    if not content:
        return {"content": "", "text": ""}

    humanized = await asyncio.to_thread(
        humanize_content,
        content,
        provider=provider,
        generation_options=options,
    )

    return {"content": humanized, "text": humanized}


async def _execute_seo_optimize(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Run content scoring for SEO, readability, and engagement."""
    from ..scoring.content_scorer import score_content

    content = _resolve_content(context)
    keywords = _resolve_keywords(context)

    if not content:
        return {"score": 0, "details": {}}

    result = await asyncio.to_thread(
        score_content,
        text=content,
        keywords=keywords,
    )

    return {
        "overall_score": getattr(result, "overall_score", 0),
        "readability": getattr(result, "readability", None),
        "seo": getattr(result, "seo", None),
        "engagement": getattr(result, "engagement", None),
    }


async def _execute_meta_description(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate a meta description for SEO."""
    from ..seo.meta_description import generate_meta_description

    title = _resolve_title(context)
    keywords = _resolve_keywords(context)
    content = _resolve_content(context)

    meta = await asyncio.to_thread(
        generate_meta_description,
        title=title,
        keywords=keywords,
        content=content[:500] if content else None,
        provider=provider,
        options=options,
    )

    return {"meta_description": meta.content}


async def _execute_structured_data(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate JSON-LD structured data."""
    from ..seo.structured_data import generate_structured_data

    schema_type = config.get("schema_type", "Article")
    content = _resolve_content(context)

    if not content:
        return {"structured_data": ""}

    result = await asyncio.to_thread(
        generate_structured_data,
        type=schema_type,
        content=content,
        provider=provider,
        options=options,
    )

    return {"structured_data": result.content}


async def _execute_remix(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Remix content into different formats (Twitter, LinkedIn, etc.)."""
    from ..remix.service import RemixService
    from ..types.remix import ContentFormat, RemixRequest

    provider_type = context.get("provider_type", "openai")
    formats_raw = config.get("formats", ["twitter_thread", "linkedin_post"])
    target_formats = []
    for fmt in formats_raw:
        try:
            target_formats.append(ContentFormat(fmt))
        except ValueError:
            logger.warning("Unknown remix format '%s', skipping", fmt)

    if not target_formats:
        return {"remixed": []}

    title = _resolve_title(context)
    content = _resolve_content(context)

    source_content = {"title": title, "body": content}

    service = RemixService(provider_type)
    request = RemixRequest(
        source_content=source_content,
        target_formats=target_formats,
        conversation_id=str(uuid.uuid4()),
    )

    result = await service.remix(request)

    remixed_items = []
    for item in result.remixed_content:
        remixed_items.append({
            "format": item.format.value if hasattr(item.format, "value") else str(item.format),
            "content": item.content,
        })

    return {"remixed": remixed_items}


async def _execute_image_generate(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate an image prompt for the content."""
    from ..images.prompt_generator import PromptGenerator

    title = _resolve_title(context)
    content = _resolve_content(context)
    keywords = _resolve_keywords(context)

    generator = PromptGenerator()
    image_prompt = await asyncio.to_thread(
        generator.generate_featured_prompt,
        content=content[:5000] if content else title,
        title=title,
        keywords=keywords or None,
    )

    return {"image_prompt": image_prompt, "title": title}


async def _execute_publish_wordpress(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Publish content to WordPress."""
    from ..integrations.wordpress import upload_post
    from ..types.integrations import WordPressCredentials, WordPressPostOptions

    variables = context.get("variables", {})
    wp_config = variables.get("wordpress", {})

    if not wp_config.get("url") or not wp_config.get("username"):
        return {"published": False, "error": "WordPress credentials not provided in variables"}

    title = _resolve_title(context)
    content = _resolve_content(context)

    credentials = WordPressCredentials(
        url=wp_config["url"],
        username=wp_config["username"],
        password=wp_config.get("password", ""),
    )
    post_options = WordPressPostOptions(
        title=title,
        content=content,
        status=config.get("status", "draft"),
    )

    result = await asyncio.to_thread(upload_post, credentials, post_options)

    return {
        "published": result.success,
        "message": result.message,
        "data": result.data,
    }


async def _execute_publish_medium(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Publish content to Medium."""
    from ..integrations.medium import upload_post
    from ..types.integrations import MediumCredentials, MediumPostOptions

    variables = context.get("variables", {})
    medium_config = variables.get("medium", {})

    if not medium_config.get("token"):
        return {"published": False, "error": "Medium token not provided in variables"}

    title = _resolve_title(context)
    content = _resolve_content(context)
    keywords = _resolve_keywords(context)

    credentials = MediumCredentials(token=medium_config["token"])
    post_options = MediumPostOptions(
        title=title,
        content=content,
        content_format=config.get("content_format", "html"),
        tags=keywords[:5] if keywords else [],
        publish_status=config.get("status", "draft"),
    )

    result = await asyncio.to_thread(upload_post, credentials, post_options)

    return {
        "published": result.success,
        "message": result.message,
        "data": result.data,
    }


async def _execute_publish_github(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Publish content as a file to GitHub."""
    from ..integrations.github import upload_file
    from ..types.integrations import GitHubCredentials, GitHubFileOptions, GitHubRepository

    variables = context.get("variables", {})
    gh_config = variables.get("github", {})

    if not gh_config.get("token") or not gh_config.get("repo"):
        return {"published": False, "error": "GitHub credentials not provided in variables"}

    title = _resolve_title(context)
    content = _resolve_content(context)

    credentials = GitHubCredentials(token=gh_config["token"])
    repository = GitHubRepository(
        owner=gh_config.get("owner", ""),
        name=gh_config["repo"],
    )
    file_options = GitHubFileOptions(
        path=config.get("path", f"content/{title.lower().replace(' ', '-')}.md"),
        content=content,
        message=config.get("commit_message", f"Add content: {title}"),
    )

    result = await asyncio.to_thread(upload_file, credentials, repository, file_options)

    return {
        "published": result.success,
        "message": result.message,
        "data": result.data,
    }


async def _execute_social_post(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Generate social media posts from content using the LLM."""
    content = _resolve_content(context)
    title = _resolve_title(context)
    platforms = config.get("platforms", ["twitter", "linkedin"])

    results: Dict[str, str] = {}

    for platform in platforms:
        prompt = (
            f"Write a {platform} post promoting this content.\n\n"
            f"Title: {title}\n\n"
            f"Content summary: {content[:500] if content else 'N/A'}\n\n"
            f"Requirements:\n"
            f"- Appropriate length and tone for {platform}\n"
            f"- Include a hook and call-to-action\n"
            f"- Use relevant hashtags if appropriate\n\n"
            f"Return only the post text."
        )

        post_text = await asyncio.to_thread(generate_text, prompt, provider, options)
        results[platform] = post_text.strip()

    return {"social_posts": results}


async def _execute_custom_llm(
    config: Dict[str, Any],
    context: Dict[str, Any],
    provider: LLMProvider,
    options: GenerationOptions,
) -> Dict[str, Any]:
    """Execute a custom LLM prompt with template variable substitution."""
    prompt_template = config.get("prompt", "")
    if not prompt_template:
        return {"content": "", "text": ""}

    variables = context.get("variables", {})

    # Substitute {{variable}} placeholders.
    prompt = prompt_template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        if placeholder in prompt:
            prompt = prompt.replace(placeholder, str(value))

    # Also substitute {{step_id.field}} references.
    for key, value in context.items():
        if key == "variables":
            continue
        if isinstance(value, dict):
            for field_key, field_value in value.items():
                placeholder = "{{" + f"{key}.{field_key}" + "}}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(field_value))

    # Inject content from prior steps if {{content}} is referenced.
    if "{{content}}" in prompt:
        prompt = prompt.replace("{{content}}", _resolve_content(context))

    result = await asyncio.to_thread(generate_text, prompt, provider, options)

    return {"content": result.strip(), "text": result.strip()}


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------

_STEP_HANDLERS: Dict[StepType, Callable] = {
    StepType.RESEARCH: _execute_research,
    StepType.OUTLINE: _execute_outline,
    StepType.GENERATE_BLOG: _execute_generate_blog,
    StepType.GENERATE_BOOK: _execute_generate_book,
    StepType.PROOFREAD: _execute_proofread,
    StepType.HUMANIZE: _execute_humanize,
    StepType.SEO_OPTIMIZE: _execute_seo_optimize,
    StepType.META_DESCRIPTION: _execute_meta_description,
    StepType.STRUCTURED_DATA: _execute_structured_data,
    StepType.REMIX: _execute_remix,
    StepType.IMAGE_GENERATE: _execute_image_generate,
    StepType.PUBLISH_WORDPRESS: _execute_publish_wordpress,
    StepType.PUBLISH_MEDIUM: _execute_publish_medium,
    StepType.PUBLISH_GITHUB: _execute_publish_github,
    StepType.SOCIAL_POST: _execute_social_post,
    StepType.CUSTOM_LLM: _execute_custom_llm,
}
