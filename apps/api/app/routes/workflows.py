"""
Workflow automation API routes.

Provides endpoints for listing preset workflows, creating custom workflows,
executing workflows, querying execution status, and cancelling running
executions.

Authorization:
- Workflow execution requires content.create permission in the organization.
- Read-only endpoints (presets, status) require content.view permission.
- Pass the organization ID via X-Organization-ID header for org-scoped access.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.config import get_settings
from src.organizations import AuthorizationContext
from src.text_generation.core import GenerationOptions
from src.workflows.preset_workflows import PRESET_WORKFLOWS, build_preset_workflow
from src.workflows import workflow_store
from src.workflows.workflow_engine import (
    StepType,
    Workflow,
    WorkflowEngine,
    WorkflowExecution,
    WorkflowExecutionError,
    WorkflowStatus,
    WorkflowStep,
)

from ..auth import verify_api_key
from ..dependencies import require_content_access, require_content_creation
from ..error_handlers import sanitize_error_message
from ..middleware import increment_usage_for_operation, require_pro_tier, require_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])

_running_engines: Dict[str, WorkflowEngine] = {}

_ALLOWED_PROVIDERS = {"openai", "anthropic", "gemini"}


def _validate_provider(provider: str) -> str:
    """Normalize and validate a provider string."""
    v = (provider or "").strip().lower() or "openai"
    if v not in _ALLOWED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{v}'. Allowed: {', '.join(sorted(_ALLOWED_PROVIDERS))}",
        )
    configured = get_settings().llm.available_providers
    if configured and v not in configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{v}' is not configured for this deployment",
        )
    return v


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class WorkflowStepInput(BaseModel):
    """A single step in a custom workflow definition."""

    id: str = Field(default="", description="Step identifier (auto-generated if empty)")
    type: str = Field(..., description="Step type (e.g. 'research', 'generate_blog')")
    name: str = Field(default="", description="Human-readable step name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step-specific configuration")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps this depends on")


class CreateWorkflowRequest(BaseModel):
    """Request body for creating a custom workflow."""

    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: str = Field(default="", max_length=1000, description="Workflow description")
    steps: List[WorkflowStepInput] = Field(..., min_length=1, max_length=20, description="Pipeline steps")


class ExecuteWorkflowRequest(BaseModel):
    """Request body for executing a workflow."""

    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime variables (topic, keywords, tone, etc.)",
    )
    provider: str = Field(default="openai", description="LLM provider to use")
    preset_id: Optional[str] = Field(
        default=None,
        description="If set, execute a preset workflow instead of a custom one",
    )


class CancelWorkflowRequest(BaseModel):
    """Request body for cancelling a workflow (empty for now, extensible)."""
    pass


class WorkflowSummary(BaseModel):
    """Condensed workflow info for list endpoints."""

    id: str
    name: str
    description: str
    step_count: int
    step_types: List[str]


class ExecutionSummary(BaseModel):
    """Condensed execution info."""

    execution_id: str
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    results: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/presets",
    summary="List preset workflows",
    description="Returns all pre-built workflow templates with their step definitions.",
    response_model=List[WorkflowSummary],
)
async def list_presets() -> List[Dict[str, Any]]:
    """Return all preset workflow templates."""
    presets = []
    for preset_id, preset in PRESET_WORKFLOWS.items():
        presets.append({
            "id": preset_id,
            "name": preset["name"],
            "description": preset["description"],
            "step_count": len(preset["steps"]),
            "step_types": [s["type"] for s in preset["steps"]],
        })
    return presets


@router.get(
    "/presets/{preset_id}",
    summary="Get preset workflow details",
    description="Returns the full definition of a single preset workflow.",
)
async def get_preset(preset_id: str) -> Dict[str, Any]:
    """Return full details of a specific preset."""
    preset = PRESET_WORKFLOWS.get(preset_id)
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_id}' not found",
        )
    return {
        "id": preset_id,
        "name": preset["name"],
        "description": preset["description"],
        "steps": preset["steps"],
    }


@router.get(
    "",
    summary="List custom workflows",
    description="Returns all custom workflows created by the current user.",
    response_model=List[WorkflowSummary],
)
async def list_workflows(
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> List[Dict[str, Any]]:
    """Return all custom workflows for the authenticated user."""
    workflows = await workflow_store.list_workflows(auth_ctx.user_id)
    return [
        {
            "id": wf["id"],
            "name": wf["name"],
            "description": wf.get("description", ""),
            "step_count": len(wf.get("steps", [])),
            "step_types": [s.get("type", "") for s in wf.get("steps", [])],
        }
        for wf in workflows
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom workflow",
    description="Define a custom workflow with user-specified steps and dependencies.",
    response_model=WorkflowSummary,
)
async def create_workflow(
    request: CreateWorkflowRequest,
    _tier: str = Depends(require_pro_tier),
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> Dict[str, Any]:
    """Create and store a custom workflow definition."""
    user_id = auth_ctx.user_id

    # Validate step types.
    valid_types = {t.value for t in StepType}
    for step in request.steps:
        if step.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step type '{step.type}'. Valid types: {', '.join(sorted(valid_types))}",
            )

    # Validate dependency references.
    step_ids = set()
    for i, step in enumerate(request.steps):
        sid = step.id or str(uuid.uuid4())[:8]
        step.id = sid
        step_ids.add(sid)

    for step in request.steps:
        for dep in step.depends_on:
            if dep not in step_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Step '{step.id}' depends on unknown step '{dep}'",
                )

    workflow_id = str(uuid.uuid4())
    workflow_data = {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "steps": [s.model_dump() for s in request.steps],
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await workflow_store.save_workflow(workflow_data)

    logger.info("Custom workflow '%s' created by user %s", request.name, user_id[:8])

    return {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "step_count": len(request.steps),
        "step_types": [s.type for s in request.steps],
    }


@router.post(
    "/{workflow_id}/execute",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute a workflow",
    description=(
        "Start executing a workflow (custom or preset). "
        "Returns immediately with an execution ID; poll the status endpoint for progress. "
        "Set ``preset_id`` in the body to run a preset workflow (the path ``workflow_id`` "
        "is then used only for the execution record key)."
    ),
)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    _tier: str = Depends(require_pro_tier),
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> Dict[str, Any]:
    """Execute a workflow and return an execution handle."""
    user_id = auth_ctx.user_id

    await require_quota(user_id)

    provider_type = _validate_provider(request.provider)

    # Build the Workflow object.
    if request.preset_id:
        try:
            workflow = build_preset_workflow(request.preset_id, request.variables)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
    else:
        wf_data = await workflow_store.get_workflow(workflow_id, user_id=user_id)
        if wf_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_id}' not found",
            )
        steps = []
        for s in wf_data["steps"]:
            steps.append(
                WorkflowStep(
                    id=s["id"],
                    type=StepType(s["type"]),
                    name=s.get("name", ""),
                    config=s.get("config", {}),
                    depends_on=s.get("depends_on", []),
                )
            )
        workflow = Workflow(
            id=wf_data["id"],
            name=wf_data["name"],
            description=wf_data["description"],
            steps=steps,
            variables=request.variables,
        )

    execution_id = str(uuid.uuid4())
    await workflow_store.create_execution(
        {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "status": WorkflowStatus.PENDING.value,
            "current_step": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
            "results": {},
            "user_id": user_id,
        },
        variables=request.variables,
        provider=provider_type,
    )

    engine = WorkflowEngine()
    _running_engines[execution_id] = engine

    options = GenerationOptions(
        temperature=0.7,
        max_tokens=4000,
        top_p=0.9,
    )

    async def _progress(step_id: str, step_status: WorkflowStatus, message: Optional[str]) -> None:
        """Update the execution record as each step completes."""
        next_status = step_status.value if step_status == WorkflowStatus.FAILED else WorkflowStatus.RUNNING.value
        await workflow_store.update_execution(
            execution_id,
            current_step=step_id,
            status=next_status,
        )

    async def _run() -> None:
        await workflow_store.update_execution(
            execution_id,
            status=WorkflowStatus.RUNNING.value,
        )
        try:
            execution = await engine.execute_workflow(
                workflow=workflow,
                variables=request.variables,
                provider_type=provider_type,
                options=options,
                progress_callback=_progress,
            )
            await workflow_store.update_execution(
                execution_id,
                status=execution.status.value,
                results=execution.results,
                completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                error=execution.error,
            )

            # Track usage on success.
            if execution.status == WorkflowStatus.COMPLETED:
                step_count = len(workflow.steps)
                await increment_usage_for_operation(
                    user_id=user_id,
                    operation_type="workflow",
                    tokens_used=4000 * step_count,
                    metadata={
                        "workflow_name": workflow.name,
                        "step_count": step_count,
                        "provider": provider_type,
                    },
                )

        except WorkflowExecutionError as exc:
            await workflow_store.update_execution(
                execution_id,
                status=WorkflowStatus.FAILED.value,
                error=str(exc),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.error("Workflow execution %s failed: %s", execution_id, exc)
        except Exception as exc:
            await workflow_store.update_execution(
                execution_id,
                status=WorkflowStatus.FAILED.value,
                error="Unexpected error during workflow execution",
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.error("Unexpected workflow error %s: %s", execution_id, exc, exc_info=True)
        finally:
            _running_engines.pop(execution_id, None)

    # Fire and forget -- the caller polls /status.
    asyncio.create_task(_run())

    logger.info(
        "Workflow execution %s started for user %s (workflow: %s)",
        execution_id,
        user_id[:8],
        workflow.name,
    )

    return {
        "success": True,
        "execution_id": execution_id,
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "status": "pending",
        "message": "Workflow execution started. Poll the status endpoint for progress.",
    }


@router.get(
    "/{workflow_id}/status",
    summary="Get workflow execution status",
    description=(
        "Retrieve the current status and per-step results of a workflow execution. "
        "The ``workflow_id`` parameter is actually the ``execution_id`` returned by "
        "the execute endpoint."
    ),
    response_model=ExecutionSummary,
)
async def get_execution_status(
    workflow_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_access),
) -> Dict[str, Any]:
    """
    Return execution status.

    Despite the path parameter name, this accepts either an execution_id
    or a workflow_id and returns the most recent execution for that workflow.
    """
    record = await workflow_store.get_execution(workflow_id, user_id=auth_ctx.user_id)
    if record is None:
        record = await workflow_store.get_latest_execution_for_workflow(
            workflow_id,
            user_id=auth_ctx.user_id,
        )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No execution found for '{workflow_id}'",
        )

    return {
        "execution_id": record["execution_id"],
        "workflow_id": record["workflow_id"],
        "status": record["status"],
        "current_step": record.get("current_step"),
        "started_at": record.get("started_at"),
        "completed_at": record.get("completed_at"),
        "error": record.get("error"),
        "results": record.get("results", {}),
    }


@router.post(
    "/{workflow_id}/cancel",
    summary="Cancel a running workflow",
    description="Request cancellation of a running workflow execution.",
)
async def cancel_workflow(
    workflow_id: str,
    auth_ctx: AuthorizationContext = Depends(require_content_creation),
) -> Dict[str, Any]:
    """Cancel a running workflow execution."""
    user_id = auth_ctx.user_id

    # Try as execution_id.
    engine = _running_engines.get(workflow_id)
    record = await workflow_store.get_execution(workflow_id, user_id=user_id)

    # Fall back to workflow_id search.
    if engine is None:
        for eid, eng in list(_running_engines.items()):
            rec = await workflow_store.get_execution(eid, user_id=user_id)
            if rec and rec.get("workflow_id") == workflow_id:
                engine = eng
                record = rec
                break

    if engine is None:
        if record and record.get("status") in (
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.CANCELLED.value,
        ):
            return {
                "success": False,
                "message": f"Workflow is already {record['status']}",
            }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running execution found for this workflow",
        )

    engine.cancel()

    if record:
        await workflow_store.update_execution(
            record["execution_id"],
            status=WorkflowStatus.CANCELLED.value,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    logger.info("Workflow execution cancelled for %s by user %s", workflow_id, auth_ctx.user_id[:8])

    return {
        "success": True,
        "message": "Cancellation requested. The workflow will stop before the next step.",
    }


@router.get(
    "/step-types",
    summary="List available step types",
    description="Returns all step types that can be used when building workflows.",
)
async def list_step_types() -> List[Dict[str, str]]:
    """Return the list of supported step types with descriptions."""
    descriptions = {
        StepType.RESEARCH: "Conduct web research on the topic",
        StepType.OUTLINE: "Generate a content outline",
        StepType.GENERATE_BLOG: "Generate a full blog post",
        StepType.GENERATE_BOOK: "Generate a book or book chapter",
        StepType.PROOFREAD: "Proofread content for grammar and style",
        StepType.HUMANIZE: "Make content sound more natural and human-written",
        StepType.SEO_OPTIMIZE: "Score content for SEO, readability, and engagement",
        StepType.META_DESCRIPTION: "Generate an SEO meta description",
        StepType.STRUCTURED_DATA: "Generate JSON-LD structured data",
        StepType.REMIX: "Transform content into social media formats",
        StepType.IMAGE_GENERATE: "Generate an AI image prompt for the content",
        StepType.PUBLISH_WORDPRESS: "Publish content to WordPress",
        StepType.PUBLISH_MEDIUM: "Publish content to Medium",
        StepType.PUBLISH_GITHUB: "Publish content as a file to GitHub",
        StepType.SOCIAL_POST: "Generate social media posts for specific platforms",
        StepType.CUSTOM_LLM: "Run a custom LLM prompt with variable substitution",
    }
    return [
        {"type": step_type.value, "description": descriptions.get(step_type, "")}
        for step_type in StepType
    ]
