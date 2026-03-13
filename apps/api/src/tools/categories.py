"""
Tool category definitions and metadata.

This module defines all available tool categories with their
display information and configuration.
"""

from typing import Dict, List

from ..types.tools import CategoryInfo, ToolCategory


# Category display information
CATEGORY_INFO: Dict[ToolCategory, CategoryInfo] = {
    ToolCategory.BLOG: CategoryInfo(
        id="blog",
        name="Blog",
        description="Create engaging blog posts, articles, and long-form content",
        icon="article",
        color="#3b82f6"
    ),
    ToolCategory.EMAIL: CategoryInfo(
        id="email",
        name="Email",
        description="Craft compelling emails for marketing, sales, and communication",
        icon="email",
        color="#10b981"
    ),
    ToolCategory.SOCIAL: CategoryInfo(
        id="social",
        name="Social Media",
        description="Generate posts and content for social media platforms",
        icon="share",
        color="#8b5cf6"
    ),
    ToolCategory.BUSINESS: CategoryInfo(
        id="business",
        name="Business",
        description="Professional business documents, proposals, and communications",
        icon="business",
        color="#f59e0b"
    ),
    ToolCategory.NAMING: CategoryInfo(
        id="naming",
        name="Naming & Branding",
        description="Generate creative names for products, businesses, and brands",
        icon="label",
        color="#ec4899"
    ),
    ToolCategory.VIDEO: CategoryInfo(
        id="video",
        name="Video & Audio",
        description="Scripts, descriptions, and content for video and audio",
        icon="videocam",
        color="#ef4444"
    ),
    ToolCategory.SEO: CategoryInfo(
        id="seo",
        name="SEO",
        description="Search engine optimization content and metadata",
        icon="search",
        color="#06b6d4"
    ),
    ToolCategory.REWRITING: CategoryInfo(
        id="rewriting",
        name="Rewriting & Editing",
        description="Improve, rewrite, and polish existing content",
        icon="edit",
        color="#84cc16"
    ),
    ToolCategory.ADS: CategoryInfo(
        id="ads",
        name="Ads & Marketing",
        description="Advertising copy and marketing materials",
        icon="campaign",
        color="#f97316"
    ),
    ToolCategory.ECOMMERCE: CategoryInfo(
        id="ecommerce",
        name="E-commerce",
        description="Product descriptions, listings, and sales content",
        icon="shopping_cart",
        color="#14b8a6"
    ),
    ToolCategory.PERSONAL: CategoryInfo(
        id="personal",
        name="Personal",
        description="Personal communications, bios, and self-expression",
        icon="person",
        color="#a855f7"
    ),
    ToolCategory.CREATIVE: CategoryInfo(
        id="creative",
        name="Creative Writing",
        description="Stories, poetry, and creative content",
        icon="auto_stories",
        color="#f43f5e"
    ),
}


def get_category_info(category: ToolCategory) -> CategoryInfo:
    """
    Get display information for a category.

    Args:
        category: The category to get info for.

    Returns:
        CategoryInfo with display data.
    """
    return CATEGORY_INFO.get(category, CategoryInfo(
        id=category.value,
        name=category.value.title(),
        description=f"Tools for {category.value}",
        icon="build"
    ))


def get_all_categories() -> List[CategoryInfo]:
    """
    Get all category information.

    Returns:
        List of all CategoryInfo objects.
    """
    return list(CATEGORY_INFO.values())


def get_categories_with_counts(tool_counts: Dict[str, int]) -> List[CategoryInfo]:
    """
    Get all categories with their tool counts.

    Args:
        tool_counts: Dictionary mapping category IDs to tool counts.

    Returns:
        List of CategoryInfo objects with updated counts.
    """
    result = []
    for category, info in CATEGORY_INFO.items():
        updated_info = CategoryInfo(
            id=info.id,
            name=info.name,
            description=info.description,
            icon=info.icon,
            color=info.color,
            tool_count=tool_counts.get(category.value, 0)
        )
        result.append(updated_info)
    return result


# Category groupings for UI organization
CATEGORY_GROUPS = {
    "Content Creation": [
        ToolCategory.BLOG,
        ToolCategory.CREATIVE,
        ToolCategory.VIDEO,
    ],
    "Marketing": [
        ToolCategory.EMAIL,
        ToolCategory.SOCIAL,
        ToolCategory.ADS,
        ToolCategory.SEO,
    ],
    "Business": [
        ToolCategory.BUSINESS,
        ToolCategory.ECOMMERCE,
        ToolCategory.NAMING,
    ],
    "Editing": [
        ToolCategory.REWRITING,
        ToolCategory.PERSONAL,
    ],
}


def get_category_groups() -> Dict[str, List[CategoryInfo]]:
    """
    Get categories organized into logical groups.

    Returns:
        Dictionary mapping group names to lists of CategoryInfo.
    """
    result = {}
    for group_name, categories in CATEGORY_GROUPS.items():
        result[group_name] = [
            get_category_info(cat) for cat in categories
        ]
    return result
