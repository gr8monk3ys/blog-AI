"""
Tool Registry for managing and discovering content generation tools.

This module provides the central registry for all tools in the system,
supporting tool discovery, filtering, and execution routing.
"""

import importlib
import logging
import os
import pkgutil
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type

from ..types.providers import GenerationOptions, LLMProvider, ProviderType
from ..types.tools import (
    CategoryInfo,
    ToolCategory,
    ToolDefinition,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolListResponse,
    ToolMetadata,
)
from .base import BaseTool
from .categories import get_categories_with_counts, get_category_info

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found in the registry."""

    def __init__(self, tool_id: str):
        self.tool_id = tool_id
        super().__init__(f"Tool not found: {tool_id}")


class ToolRegistry:
    """
    Central registry for all content generation tools.

    The registry supports:
    - Tool registration (manual or auto-discovery)
    - Tool discovery (list, filter, search)
    - Tool execution routing
    - Category management

    Usage:
        registry = ToolRegistry()
        registry.auto_discover()  # Load all tools from src/tools/library/

        # List all tools
        tools = registry.list_tools()

        # Get a specific tool
        tool = registry.get_tool("blog-title-generator")

        # Execute a tool
        result = registry.execute(ToolExecutionRequest(
            tool_id="blog-title-generator",
            inputs={"topic": "AI in Healthcare"}
        ))
    """

    _instance: Optional["ToolRegistry"] = None
    _lock: threading.Lock = threading.Lock()
    _tools: Dict[str, BaseTool]
    _definitions_cache: Dict[str, ToolDefinition]
    _category_index: Dict[ToolCategory, List[str]]
    _tag_index: Dict[str, List[str]]

    def __new__(cls) -> "ToolRegistry":
        """Thread-safe singleton pattern - only one registry instance."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern for thread safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tools = {}
                    cls._instance._definitions_cache = {}
                    cls._instance._category_index = defaultdict(list)
                    cls._instance._tag_index = defaultdict(list)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (useful for testing)."""
        cls._instance = None

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: The tool instance to register.

        Raises:
            ValueError: If a tool with the same ID is already registered.
        """
        tool_id = tool.id

        if tool_id in self._tools:
            logger.warning(f"Tool '{tool_id}' already registered, overwriting")

        self._tools[tool_id] = tool

        # Cache the definition
        definition = tool.get_definition()
        self._definitions_cache[tool_id] = definition

        # Update category index
        category = tool.category
        if tool_id not in self._category_index[category]:
            self._category_index[category].append(tool_id)

        # Update tag index
        for tag in tool.tags:
            tag_lower = tag.lower()
            if tool_id not in self._tag_index[tag_lower]:
                self._tag_index[tag_lower].append(tool_id)

        logger.info(f"Registered tool: {tool_id} (category: {category.value})")

    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class (instantiates it automatically).

        Args:
            tool_class: The tool class to register.
        """
        tool = tool_class()
        self.register(tool)

    def unregister(self, tool_id: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            tool_id: The ID of the tool to unregister.

        Returns:
            True if the tool was unregistered, False if not found.
        """
        if tool_id not in self._tools:
            return False

        tool = self._tools[tool_id]

        # Remove from category index
        category = tool.category
        if tool_id in self._category_index[category]:
            self._category_index[category].remove(tool_id)

        # Remove from tag index
        for tag in tool.tags:
            tag_lower = tag.lower()
            if tool_id in self._tag_index[tag_lower]:
                self._tag_index[tag_lower].remove(tool_id)

        # Remove from main storage
        del self._tools[tool_id]
        del self._definitions_cache[tool_id]

        logger.info(f"Unregistered tool: {tool_id}")
        return True

    def get_tool(self, tool_id: str) -> BaseTool:
        """
        Get a tool by ID.

        Args:
            tool_id: The tool identifier.

        Returns:
            The tool instance.

        Raises:
            ToolNotFoundError: If the tool is not found.
        """
        if tool_id not in self._tools:
            raise ToolNotFoundError(tool_id)
        return self._tools[tool_id]

    def get_definition(self, tool_id: str) -> ToolDefinition:
        """
        Get a tool definition by ID.

        Args:
            tool_id: The tool identifier.

        Returns:
            The tool definition.

        Raises:
            ToolNotFoundError: If the tool is not found.
        """
        if tool_id not in self._definitions_cache:
            raise ToolNotFoundError(tool_id)
        return self._definitions_cache[tool_id]

    def has_tool(self, tool_id: str) -> bool:
        """Check if a tool is registered."""
        return tool_id in self._tools

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        include_premium: bool = True,
        include_beta: bool = True,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> ToolListResponse:
        """
        List tools with optional filtering.

        Args:
            category: Filter by category.
            tags: Filter by tags (OR logic).
            search: Search in name, description, and tags.
            include_premium: Include premium tools.
            include_beta: Include beta tools.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            ToolListResponse with matching tools.
        """
        tool_ids = set(self._tools.keys())

        # Filter by category
        if category is not None:
            category_tools = set(self._category_index.get(category, []))
            tool_ids = tool_ids.intersection(category_tools)

        # Filter by tags
        if tags:
            tag_tools = set()
            for tag in tags:
                tag_lower = tag.lower()
                tag_tools.update(self._tag_index.get(tag_lower, []))
            tool_ids = tool_ids.intersection(tag_tools)

        # Get definitions and apply remaining filters
        results = []
        for tool_id in tool_ids:
            definition = self._definitions_cache[tool_id]
            metadata = definition.metadata

            # Filter premium/beta
            if not include_premium and metadata.is_premium:
                continue
            if not include_beta and metadata.is_beta:
                continue

            # Search filter
            if search:
                search_lower = search.lower()
                searchable = f"{metadata.name} {metadata.description} {' '.join(metadata.tags)}".lower()
                if search_lower not in searchable:
                    continue

            results.append(metadata)

        # Sort by popularity (descending) then name
        results.sort(key=lambda m: (-m.popularity_score, m.name))

        total = len(results)

        # Apply pagination
        if offset > 0:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]

        # Get unique categories (handle both enum and string values)
        categories = list(set(
            m.category.value if hasattr(m.category, 'value') else m.category
            for m in results
        ))

        return ToolListResponse(
            tools=results,
            total=total,
            categories=categories,
        )

    def list_categories(self) -> List[CategoryInfo]:
        """
        List all categories with their tool counts.

        Returns:
            List of CategoryInfo objects.
        """
        counts = {
            category.value: len(tool_ids)
            for category, tool_ids in self._category_index.items()
        }
        return get_categories_with_counts(counts)

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """
        Get all tools in a category.

        Args:
            category: The category to filter by.

        Returns:
            List of ToolMetadata for tools in the category.
        """
        tool_ids = self._category_index.get(category, [])
        return [
            self._definitions_cache[tid].metadata
            for tid in tool_ids
        ]

    def execute(
        self,
        request: ToolExecutionRequest,
        provider: Optional[LLMProvider] = None,
    ) -> ToolExecutionResult:
        """
        Execute a tool with the given request.

        Args:
            request: The tool execution request.
            provider: Optional pre-configured LLM provider.

        Returns:
            ToolExecutionResult with the generated content.
        """
        try:
            tool = self.get_tool(request.tool_id)
        except ToolNotFoundError as e:
            return ToolExecutionResult(
                success=False,
                tool_id=request.tool_id,
                error=str(e),
                execution_time_ms=0,
            )

        # Build generation options from request
        options = None
        if request.options:
            options = GenerationOptions(
                temperature=request.options.get("temperature", 0.7),
                max_tokens=request.options.get("max_tokens", 2000),
                top_p=request.options.get("top_p", 0.9),
                frequency_penalty=request.options.get("frequency_penalty", 0.0),
                presence_penalty=request.options.get("presence_penalty", 0.0),
            )

        return tool.execute(
            inputs=request.inputs,
            provider=provider,
            provider_type=request.provider_type,
            options=options,
        )

    def auto_discover(self, package_path: Optional[str] = None) -> int:
        """
        Auto-discover and register tools from the library package.

        Args:
            package_path: Path to the tools library package.
                         Defaults to src/tools/library.

        Returns:
            Number of tools registered.
        """
        if package_path is None:
            # Default to the library subdirectory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            package_path = os.path.join(current_dir, "library")

        if not os.path.exists(package_path):
            logger.warning(f"Tools library path does not exist: {package_path}")
            return 0

        registered_count = 0

        # Walk through all Python files in the library
        for root, dirs, files in os.walk(package_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            for file in files:
                if not file.endswith(".py") or file.startswith("_"):
                    continue

                file_path = os.path.join(root, file)
                module_name = self._path_to_module(file_path, package_path)

                try:
                    registered_count += self._load_tools_from_module(module_name)
                except Exception as e:
                    logger.error(f"Failed to load tools from {module_name}: {e}")

        logger.info(f"Auto-discovered {registered_count} tools")
        return registered_count

    def _path_to_module(self, file_path: str, base_path: str) -> str:
        """Convert a file path to a module name."""
        rel_path = os.path.relpath(file_path, os.path.dirname(base_path))
        module_path = rel_path.replace(os.sep, ".").replace(".py", "")
        return f"src.tools.{module_path}"

    def _load_tools_from_module(self, module_name: str) -> int:
        """Load all BaseTool subclasses from a module."""
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            logger.warning(f"Could not import {module_name}: {e}")
            return 0

        registered = 0
        for name in dir(module):
            obj = getattr(module, name)

            # Check if it's a BaseTool subclass (but not BaseTool itself)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseTool)
                and obj is not BaseTool
                and not getattr(obj, "__abstractmethods__", None)
            ):
                try:
                    self.register_class(obj)
                    registered += 1
                except Exception as e:
                    logger.error(f"Failed to register {name}: {e}")

        return registered

    def get_stats(self) -> Dict:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats.
        """
        category_counts = {
            cat.value: len(ids)
            for cat, ids in self._category_index.items()
        }

        return {
            "total_tools": len(self._tools),
            "categories": category_counts,
            "premium_tools": sum(
                1 for d in self._definitions_cache.values()
                if d.metadata.is_premium
            ),
            "beta_tools": sum(
                1 for d in self._definitions_cache.values()
                if d.metadata.is_beta
            ),
        }


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        The singleton ToolRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: BaseTool) -> None:
    """
    Register a tool with the global registry.

    Args:
        tool: The tool to register.
    """
    get_registry().register(tool)


def tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """
    Decorator to auto-register a tool class.

    Usage:
        @tool
        class MyTool(BaseTool):
            ...
    """
    get_registry().register_class(cls)
    return cls
