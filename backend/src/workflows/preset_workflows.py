"""
Pre-built workflow templates for common content pipelines.

Each preset is a dict describing the workflow name, description, and
an ordered list of steps.  The ``build_preset_workflow`` helper converts
a preset dict into a fully-formed ``Workflow`` instance ready for
execution.
"""

from typing import Dict, Any, Optional

from .workflow_engine import StepType, Workflow, WorkflowStep


PRESET_WORKFLOWS: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------
    # 1. Full Blog Pipeline
    # ------------------------------------------------------------------
    "blog-full-pipeline": {
        "name": "Full Blog Pipeline",
        "description": (
            "End-to-end blog creation: Research the topic, create an outline, "
            "write the full post, proofread, humanize, run SEO scoring, "
            "generate a meta description, and remix into social posts."
        ),
        "steps": [
            {
                "id": "research",
                "type": "research",
                "name": "Research Topic",
                "config": {"max_sources": 8},
            },
            {
                "id": "outline",
                "type": "outline",
                "name": "Create Outline",
                "config": {"sections": 5},
                "depends_on": ["research"],
            },
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Blog Post",
                "config": {},
                "depends_on": ["outline"],
            },
            {
                "id": "proofread",
                "type": "proofread",
                "name": "Proofread",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "humanize",
                "type": "humanize",
                "name": "Humanize",
                "config": {},
                "depends_on": ["proofread"],
            },
            {
                "id": "seo",
                "type": "seo_optimize",
                "name": "SEO Score",
                "config": {},
                "depends_on": ["humanize"],
            },
            {
                "id": "meta",
                "type": "meta_description",
                "name": "Generate Meta Description",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "social",
                "type": "remix",
                "name": "Create Social Posts",
                "config": {"formats": ["twitter_thread", "linkedin_post"]},
                "depends_on": ["humanize"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 2. Social Media Blast
    # ------------------------------------------------------------------
    "social-media-blast": {
        "name": "Social Media Content Blast",
        "description": (
            "Generate a blog post and then remix it into posts for Twitter, "
            "LinkedIn, Instagram, and an email newsletter excerpt."
        ),
        "steps": [
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Blog Post",
                "config": {"sections": 4},
            },
            {
                "id": "humanize",
                "type": "humanize",
                "name": "Humanize",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "remix",
                "type": "remix",
                "name": "Remix to Social Formats",
                "config": {
                    "formats": [
                        "twitter_thread",
                        "linkedin_post",
                        "instagram_carousel",
                        "email_newsletter",
                    ],
                },
                "depends_on": ["humanize"],
            },
            {
                "id": "social_posts",
                "type": "social_post",
                "name": "Generate Platform Posts",
                "config": {"platforms": ["twitter", "linkedin", "instagram"]},
                "depends_on": ["humanize"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 3. SEO Content Brief & Draft
    # ------------------------------------------------------------------
    "seo-content-brief": {
        "name": "SEO Content Brief & Draft",
        "description": (
            "Research the topic, create a detailed outline, write a draft, "
            "generate meta description and structured data, then score for SEO."
        ),
        "steps": [
            {
                "id": "research",
                "type": "research",
                "name": "Topic Research & SERP Analysis",
                "config": {"max_sources": 10},
            },
            {
                "id": "outline",
                "type": "outline",
                "name": "SEO-Optimized Outline",
                "config": {"sections": 6},
                "depends_on": ["research"],
            },
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Draft",
                "config": {"sections": 6},
                "depends_on": ["outline"],
            },
            {
                "id": "meta",
                "type": "meta_description",
                "name": "Generate Meta Description",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "structured",
                "type": "structured_data",
                "name": "Generate Structured Data",
                "config": {"schema_type": "Article"},
                "depends_on": ["write"],
            },
            {
                "id": "seo_score",
                "type": "seo_optimize",
                "name": "SEO Score",
                "config": {},
                "depends_on": ["write"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 4. Book Chapter Pipeline
    # ------------------------------------------------------------------
    "book-chapter": {
        "name": "Book Chapter Pipeline",
        "description": (
            "Research the topic, generate a full book chapter, proofread "
            "and humanize the output."
        ),
        "steps": [
            {
                "id": "research",
                "type": "research",
                "name": "Chapter Research",
                "config": {"max_sources": 6},
            },
            {
                "id": "write",
                "type": "generate_book",
                "name": "Write Book Chapter",
                "config": {"chapters": 1, "sections_per_chapter": 4},
                "depends_on": ["research"],
            },
            {
                "id": "proofread",
                "type": "proofread",
                "name": "Proofread",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "humanize",
                "type": "humanize",
                "name": "Humanize",
                "config": {},
                "depends_on": ["proofread"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 5. Product Launch Content Pack
    # ------------------------------------------------------------------
    "product-launch": {
        "name": "Product Launch Content Pack",
        "description": (
            "Generate a full content pack for a product launch: blog post, "
            "social media posts, email newsletter, and press release."
        ),
        "steps": [
            {
                "id": "research",
                "type": "research",
                "name": "Market Research",
                "config": {"max_sources": 8},
            },
            {
                "id": "blog",
                "type": "generate_blog",
                "name": "Write Launch Blog Post",
                "config": {"sections": 5},
                "depends_on": ["research"],
            },
            {
                "id": "proofread",
                "type": "proofread",
                "name": "Proofread Blog",
                "config": {},
                "depends_on": ["blog"],
            },
            {
                "id": "press_release",
                "type": "custom_llm",
                "name": "Generate Press Release",
                "config": {
                    "prompt": (
                        "Write a professional press release announcing "
                        "the following product/topic: {{topic}}\n\n"
                        "Use these keywords: {{keywords}}\n\n"
                        "Base it on this content:\n{{content}}\n\n"
                        "Requirements:\n"
                        "- Follow AP style press release format\n"
                        "- Include a compelling headline\n"
                        "- Include a dateline\n"
                        "- Include quotes from a company spokesperson\n"
                        "- End with boilerplate and contact info placeholder\n"
                    ),
                },
                "depends_on": ["proofread"],
            },
            {
                "id": "social",
                "type": "remix",
                "name": "Social Media Posts",
                "config": {
                    "formats": ["twitter_thread", "linkedin_post"],
                },
                "depends_on": ["proofread"],
            },
            {
                "id": "email",
                "type": "custom_llm",
                "name": "Email Announcement",
                "config": {
                    "prompt": (
                        "Write an email newsletter announcement for "
                        "the following product/topic: {{topic}}\n\n"
                        "Base it on this content:\n{{content}}\n\n"
                        "Requirements:\n"
                        "- Compelling subject line\n"
                        "- Pre-header text\n"
                        "- Engaging opening\n"
                        "- Key benefits (3-5 bullet points)\n"
                        "- Clear call-to-action\n"
                        "- Appropriate sign-off\n"
                    ),
                },
                "depends_on": ["proofread"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 6. Quick Blog (no research)
    # ------------------------------------------------------------------
    "quick-blog": {
        "name": "Quick Blog Post",
        "description": (
            "Write a blog post without research, proofread it, and "
            "generate a meta description. Fast and lightweight."
        ),
        "steps": [
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Blog Post",
                "config": {"sections": 4},
            },
            {
                "id": "proofread",
                "type": "proofread",
                "name": "Proofread",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "meta",
                "type": "meta_description",
                "name": "Generate Meta Description",
                "config": {},
                "depends_on": ["write"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 7. Content Repurpose
    # ------------------------------------------------------------------
    "content-repurpose": {
        "name": "Content Repurpose Pipeline",
        "description": (
            "Take a custom prompt input and repurpose it into a blog post, "
            "social media posts, and an image prompt."
        ),
        "steps": [
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Blog Post",
                "config": {"sections": 4},
            },
            {
                "id": "humanize",
                "type": "humanize",
                "name": "Humanize",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "image",
                "type": "image_generate",
                "name": "Generate Featured Image Prompt",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "remix",
                "type": "remix",
                "name": "Remix to Multiple Formats",
                "config": {
                    "formats": [
                        "twitter_thread",
                        "linkedin_post",
                        "email_newsletter",
                    ],
                },
                "depends_on": ["humanize"],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 8. Publish & Distribute
    # ------------------------------------------------------------------
    "publish-distribute": {
        "name": "Publish & Distribute",
        "description": (
            "Write a blog post, proofread it, generate SEO assets, then "
            "publish to WordPress and create social media posts for distribution."
        ),
        "steps": [
            {
                "id": "write",
                "type": "generate_blog",
                "name": "Write Blog Post",
                "config": {"sections": 5},
            },
            {
                "id": "proofread",
                "type": "proofread",
                "name": "Proofread",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "meta",
                "type": "meta_description",
                "name": "Generate Meta Description",
                "config": {},
                "depends_on": ["write"],
            },
            {
                "id": "structured",
                "type": "structured_data",
                "name": "Generate Structured Data",
                "config": {"schema_type": "Article"},
                "depends_on": ["write"],
            },
            {
                "id": "publish_wp",
                "type": "publish_wordpress",
                "name": "Publish to WordPress",
                "config": {"status": "draft"},
                "depends_on": ["proofread"],
            },
            {
                "id": "social",
                "type": "social_post",
                "name": "Generate Social Posts",
                "config": {"platforms": ["twitter", "linkedin"]},
                "depends_on": ["proofread"],
            },
        ],
    },
}


def build_preset_workflow(
    preset_id: str,
    variables: Optional[Dict[str, Any]] = None,
) -> Workflow:
    """
    Construct a ``Workflow`` instance from a preset template.

    Args:
        preset_id: Key into ``PRESET_WORKFLOWS``.
        variables: Optional user-supplied variables to attach.

    Returns:
        A ready-to-execute ``Workflow``.

    Raises:
        ValueError: If the preset_id is not recognized.
    """
    preset = PRESET_WORKFLOWS.get(preset_id)
    if preset is None:
        available = ", ".join(sorted(PRESET_WORKFLOWS.keys()))
        raise ValueError(f"Unknown preset '{preset_id}'. Available: {available}")

    steps = []
    for step_def in preset["steps"]:
        steps.append(
            WorkflowStep(
                id=step_def.get("id", ""),
                type=StepType(step_def["type"]),
                name=step_def.get("name", ""),
                config=step_def.get("config", {}),
                depends_on=step_def.get("depends_on", []),
            )
        )

    return Workflow(
        name=preset["name"],
        description=preset["description"],
        steps=steps,
        variables=variables or {},
    )
