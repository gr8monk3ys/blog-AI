"""
Audit logging service for organization activities.

This module provides:
- Comprehensive audit logging for compliance
- Query capabilities for audit logs
- Secure, immutable audit trail

Security Notes:
- Audit logs are immutable (no update/delete operations)
- Sensitive data is filtered before logging
- All timestamps are in UTC
- IP addresses and user agents are captured for security
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from src.types.organization import (
    AuditAction,
    AuditLogCreate,
    AuditLogEntry,
    AuditLogQuery,
    ResourceType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================


# Fields that should never be logged (even in metadata)
SENSITIVE_FIELDS = frozenset({
    "password",
    "api_key",
    "secret",
    "token",
    "token_hash",
    "credit_card",
    "card_number",
    "cvv",
    "ssn",
    "social_security",
    "private_key",
})

# Maximum size for logged values (truncate if larger)
MAX_VALUE_SIZE = 10000

# Maximum age for audit log queries (for performance)
MAX_QUERY_DAYS = 365


# =============================================================================
# Audit Service
# =============================================================================


class AuditService:
    """
    Service for managing audit logs.

    Provides methods for logging actions and querying the audit trail.
    All operations are designed to be fail-safe - audit logging failures
    should not break the main application flow.
    """

    def __init__(self, db_client: Any):
        """
        Initialize the audit service.

        Args:
            db_client: Database client (Supabase client or similar).
        """
        self.db = db_client

    async def log(
        self,
        action: Union[AuditAction, str],
        resource_type: Union[ResourceType, str],
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an audit event.

        This method is designed to be fail-safe - exceptions are caught
        and logged but not raised to avoid breaking the main flow.

        Args:
            action: The action performed.
            resource_type: Type of resource affected.
            user_id: ID of the user who performed the action.
            organization_id: ID of the organization context.
            resource_id: ID of the specific resource.
            metadata: Additional contextual data.
            old_values: Previous state (for updates).
            new_values: New state (for creates/updates).
            request_context: Request context (IP, user agent, request ID).
            success: Whether the action succeeded.
            error_message: Error message if action failed.

        Returns:
            The audit log entry ID, or None if logging failed.
        """
        try:
            # Convert enums to strings if necessary
            action_str = action.value if isinstance(action, AuditAction) else str(action)
            resource_type_str = (
                resource_type.value
                if isinstance(resource_type, ResourceType)
                else str(resource_type)
            )

            # Sanitize data
            sanitized_metadata = self._sanitize_data(metadata) if metadata else {}
            sanitized_old = self._sanitize_data(old_values) if old_values else None
            sanitized_new = self._sanitize_data(new_values) if new_values else None

            # Extract request context
            ip_address = None
            user_agent = None
            request_id = None

            if request_context:
                ip_address = request_context.get("ip_address")
                user_agent = request_context.get("user_agent")
                if user_agent and len(user_agent) > 500:
                    user_agent = user_agent[:500]
                request_id = request_context.get("request_id")

            # Use database function for insertion
            result = await self.db.rpc(
                "log_audit_event",
                {
                    "p_organization_id": organization_id,
                    "p_user_id": user_id,
                    "p_action": action_str,
                    "p_resource_type": resource_type_str,
                    "p_resource_id": resource_id,
                    "p_metadata": sanitized_metadata,
                    "p_old_values": sanitized_old,
                    "p_new_values": sanitized_new,
                    "p_ip_address": ip_address,
                    "p_user_agent": user_agent,
                    "p_request_id": request_id,
                    "p_success": success,
                    "p_error_message": error_message,
                }
            ).execute()

            log_id = result.data if result.data else None

            if log_id:
                logger.debug(
                    f"Audit logged: {action_str} on {resource_type_str}",
                    extra={
                        "audit_id": log_id,
                        "action": action_str,
                        "resource_type": resource_type_str,
                        "organization_id": organization_id,
                    }
                )

            return log_id

        except Exception as e:
            # Log the failure but don't raise
            logger.error(
                f"Failed to log audit event: {e}",
                extra={
                    "action": str(action),
                    "resource_type": str(resource_type),
                    "error": str(e),
                }
            )
            return None

    async def log_security_event(
        self,
        action: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log a security-related event.

        Convenience method for security events like login attempts,
        permission denials, etc.

        Args:
            action: The security action (e.g., "login.failure").
            user_id: ID of the user involved.
            organization_id: ID of the organization context.
            metadata: Additional security context.
            request_context: Request context (IP, user agent).
            success: Whether the security check passed.
            error_message: Error message if check failed.

        Returns:
            The audit log entry ID, or None if logging failed.
        """
        return await self.log(
            action=action,
            resource_type=ResourceType.SESSION,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata,
            request_context=request_context,
            success=success,
            error_message=error_message,
        )

    async def query(
        self,
        query: AuditLogQuery,
    ) -> tuple[List[AuditLogEntry], int]:
        """
        Query audit logs with filtering.

        Args:
            query: Query parameters for filtering.

        Returns:
            Tuple of (log entries, total count).
        """
        # Build the query
        db_query = self.db.table("audit_logs").select("*", count="exact")

        # Apply filters
        if query.organization_id:
            db_query = db_query.eq("organization_id", query.organization_id)

        if query.user_id:
            db_query = db_query.eq("user_id", query.user_id)

        if query.action:
            db_query = db_query.eq("action", query.action)

        if query.resource_type:
            db_query = db_query.eq("resource_type", query.resource_type)

        if query.resource_id:
            db_query = db_query.eq("resource_id", query.resource_id)

        if query.success is not None:
            db_query = db_query.eq("success", query.success)

        # Date range filters
        if query.start_date:
            db_query = db_query.gte("created_at", query.start_date.isoformat())

        if query.end_date:
            db_query = db_query.lte("created_at", query.end_date.isoformat())
        else:
            # Default to max query age
            max_date = datetime.utcnow() - timedelta(days=MAX_QUERY_DAYS)
            db_query = db_query.gte("created_at", max_date.isoformat())

        # Ordering and pagination
        db_query = db_query.order("created_at", desc=True)
        db_query = db_query.range(query.offset, query.offset + query.limit - 1)

        result = await db_query.execute()

        entries = [self._map_entry(row) for row in (result.data or [])]
        total = result.count or len(entries)

        return entries, total

    async def get_organization_activity(
        self,
        organization_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """
        Get recent activity for an organization.

        Args:
            organization_id: The organization ID.
            days: Number of days to look back.
            limit: Maximum entries to return.

        Returns:
            List of recent audit log entries.
        """
        start_date = datetime.utcnow() - timedelta(days=min(days, MAX_QUERY_DAYS))

        entries, _ = await self.query(
            AuditLogQuery(
                organization_id=organization_id,
                start_date=start_date,
                limit=min(limit, 500),
            )
        )

        return entries

    async def get_user_activity(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[AuditLogEntry]:
        """
        Get recent activity for a user.

        Args:
            user_id: The user ID.
            organization_id: Optional organization context.
            days: Number of days to look back.
            limit: Maximum entries to return.

        Returns:
            List of recent audit log entries.
        """
        start_date = datetime.utcnow() - timedelta(days=min(days, MAX_QUERY_DAYS))

        entries, _ = await self.query(
            AuditLogQuery(
                user_id=user_id,
                organization_id=organization_id,
                start_date=start_date,
                limit=min(limit, 500),
            )
        )

        return entries

    async def get_security_events(
        self,
        organization_id: Optional[str] = None,
        days: int = 7,
        failures_only: bool = False,
    ) -> List[AuditLogEntry]:
        """
        Get security-related events.

        Args:
            organization_id: Optional organization context.
            days: Number of days to look back.
            failures_only: Only return failed security checks.

        Returns:
            List of security audit log entries.
        """
        start_date = datetime.utcnow() - timedelta(days=min(days, 90))

        # Query for security-related actions
        security_actions = [
            "login.success",
            "login.failure",
            "api_key.create",
            "api_key.revoke",
            "member.remove",
            "organization.delete",
        ]

        db_query = self.db.table("audit_logs").select("*")

        if organization_id:
            db_query = db_query.eq("organization_id", organization_id)

        db_query = db_query.in_("action", security_actions)
        db_query = db_query.gte("created_at", start_date.isoformat())

        if failures_only:
            db_query = db_query.eq("success", False)

        db_query = db_query.order("created_at", desc=True).limit(500)

        result = await db_query.execute()

        return [self._map_entry(row) for row in (result.data or [])]

    async def get_resource_history(
        self,
        resource_type: Union[ResourceType, str],
        resource_id: str,
        limit: int = 50,
    ) -> List[AuditLogEntry]:
        """
        Get the audit history for a specific resource.

        Args:
            resource_type: Type of resource.
            resource_id: ID of the resource.
            limit: Maximum entries to return.

        Returns:
            List of audit log entries for the resource.
        """
        resource_type_str = (
            resource_type.value
            if isinstance(resource_type, ResourceType)
            else str(resource_type)
        )

        entries, _ = await self.query(
            AuditLogQuery(
                resource_type=resource_type_str,
                resource_id=resource_id,
                limit=min(limit, 200),
            )
        )

        return entries

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _sanitize_data(
        self,
        data: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Sanitize data by removing sensitive fields and truncating large values.

        Args:
            data: The data to sanitize.

        Returns:
            Sanitized data dictionary.
        """
        if data is None:
            return None

        sanitized = {}

        for key, value in data.items():
            # Skip sensitive fields
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
                continue

            # Handle nested dicts
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            # Handle lists
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in value[:100]  # Limit list size
                ]
            # Handle strings
            elif isinstance(value, str):
                if len(value) > MAX_VALUE_SIZE:
                    sanitized[key] = value[:MAX_VALUE_SIZE] + "...[truncated]"
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value

        return sanitized

    def _map_entry(self, data: Dict[str, Any]) -> AuditLogEntry:
        """Map database row to AuditLogEntry model."""
        return AuditLogEntry(
            id=data["id"],
            organization_id=data.get("organization_id"),
            user_id=data.get("user_id"),
            action=data["action"],
            resource_type=data["resource_type"],
            resource_id=data.get("resource_id"),
            metadata=data.get("metadata") or {},
            old_values=data.get("old_values"),
            new_values=data.get("new_values"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            request_id=data.get("request_id"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
        )


# =============================================================================
# Audit Statistics
# =============================================================================


class AuditStatistics:
    """
    Utility class for computing audit statistics.

    Provides aggregated metrics for dashboards and reports.
    """

    def __init__(self, audit_service: AuditService):
        """
        Initialize audit statistics.

        Args:
            audit_service: The audit service instance.
        """
        self.audit = audit_service

    async def get_activity_summary(
        self,
        organization_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get activity summary for an organization.

        Args:
            organization_id: The organization ID.
            days: Number of days to analyze.

        Returns:
            Activity summary statistics.
        """
        entries = await self.audit.get_organization_activity(
            organization_id=organization_id,
            days=days,
            limit=500,
        )

        # Compute statistics
        action_counts: Dict[str, int] = {}
        user_counts: Dict[str, int] = {}
        resource_counts: Dict[str, int] = {}
        success_count = 0
        failure_count = 0

        for entry in entries:
            # Count by action
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1

            # Count by user
            if entry.user_id:
                user_counts[entry.user_id] = user_counts.get(entry.user_id, 0) + 1

            # Count by resource type
            resource_counts[entry.resource_type] = (
                resource_counts.get(entry.resource_type, 0) + 1
            )

            # Count successes and failures
            if entry.success:
                success_count += 1
            else:
                failure_count += 1

        return {
            "total_events": len(entries),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (
                success_count / len(entries) * 100 if entries else 100
            ),
            "action_breakdown": action_counts,
            "user_activity": user_counts,
            "resource_breakdown": resource_counts,
            "period_days": days,
        }

    async def get_security_summary(
        self,
        organization_id: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get security event summary.

        Args:
            organization_id: Optional organization context.
            days: Number of days to analyze.

        Returns:
            Security summary statistics.
        """
        events = await self.audit.get_security_events(
            organization_id=organization_id,
            days=days,
        )

        # Categorize events
        login_failures = 0
        permission_denials = 0
        suspicious_ips: Dict[str, int] = {}

        for event in events:
            if event.action == "login.failure":
                login_failures += 1
                if event.ip_address:
                    suspicious_ips[event.ip_address] = (
                        suspicious_ips.get(event.ip_address, 0) + 1
                    )
            elif not event.success:
                permission_denials += 1

        return {
            "total_security_events": len(events),
            "login_failures": login_failures,
            "permission_denials": permission_denials,
            "suspicious_ips": dict(
                sorted(suspicious_ips.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "period_days": days,
        }


# =============================================================================
# Service Singleton
# =============================================================================


_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """
    Get the audit service singleton.

    Returns:
        The audit service instance.

    Raises:
        RuntimeError: If service not initialized.
    """
    global _audit_service
    if _audit_service is None:
        raise RuntimeError(
            "AuditService not initialized. "
            "Call init_audit_service() first."
        )
    return _audit_service


def init_audit_service(db_client: Any) -> AuditService:
    """
    Initialize the audit service singleton.

    Args:
        db_client: Database client.

    Returns:
        The initialized audit service.
    """
    global _audit_service
    _audit_service = AuditService(db_client)
    logger.info("AuditService initialized")
    return _audit_service
