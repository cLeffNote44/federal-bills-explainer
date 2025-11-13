"""
Audit logging for sensitive operations.

Tracks security-relevant events like authentication, authorization,
data modifications, and admin actions.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Any, Dict
from pathlib import Path
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"

    # Authorization events
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHECK = "permission_check"

    # Data modification events
    BILL_CREATED = "bill_created"
    BILL_UPDATED = "bill_updated"
    BILL_DELETED = "bill_deleted"
    EXPLANATION_GENERATED = "explanation_generated"
    EXPLANATION_DELETED = "explanation_deleted"

    # Admin events
    ADMIN_ACTION = "admin_action"
    CONFIG_CHANGE = "config_change"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    ROLE_ASSIGNED = "role_assigned"

    # Export events
    DATA_EXPORT = "data_export"
    BULK_EXPORT = "bulk_export"

    # System events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    VALIDATION_ERROR = "validation_error"
    SECURITY_VIOLATION = "security_violation"


class AuditLogger:
    """
    Centralized audit logger for security-relevant events.

    Logs events to both structured log files and standard logging system.
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_file: str = "audit.log",
        enable_file_logging: bool = True,
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            log_file: Audit log filename
            enable_file_logging: Enable file-based logging
        """
        self.logger = logging.getLogger("audit")
        self.enable_file_logging = enable_file_logging

        if enable_file_logging:
            if log_dir is None:
                log_dir = Path("logs")

            log_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = log_dir / log_file

            # Create file handler if not exists
            if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
                file_handler = logging.FileHandler(self.log_path)
                file_handler.setLevel(logging.INFO)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                self.logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID performing the action
            user_email: User email
            ip_address: Client IP address
            resource: Resource being accessed
            action: Action being performed
            details: Additional event details
            success: Whether the action succeeded
            error_message: Error message if action failed
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "resource": resource,
            "action": action,
            "success": success,
            "error_message": error_message,
            "details": details or {},
        }

        # Log to structured log file
        if self.enable_file_logging:
            try:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(audit_entry) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write audit log: {e}")

        # Log to standard logger
        log_message = self._format_log_message(audit_entry)
        if success:
            self.logger.info(log_message, extra=audit_entry)
        else:
            self.logger.warning(log_message, extra=audit_entry)

    def _format_log_message(self, entry: Dict[str, Any]) -> str:
        """Format audit entry for human-readable logging."""
        parts = [
            f"[{entry['event_type']}]",
        ]

        if entry.get("user_email"):
            parts.append(f"user={entry['user_email']}")
        elif entry.get("user_id"):
            parts.append(f"user_id={entry['user_id']}")

        if entry.get("ip_address"):
            parts.append(f"ip={entry['ip_address']}")

        if entry.get("resource"):
            parts.append(f"resource={entry['resource']}")

        if entry.get("action"):
            parts.append(f"action={entry['action']}")

        status = "SUCCESS" if entry["success"] else "FAILURE"
        parts.append(f"status={status}")

        if entry.get("error_message"):
            parts.append(f"error='{entry['error_message']}'")

        return " ".join(parts)

    # Convenience methods for common events

    def log_login(
        self,
        user_email: str,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log login attempt."""
        self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            user_email=user_email,
            ip_address=ip_address,
            action="login",
            success=success,
            error_message=error_message,
        )

    def log_logout(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log logout."""
        self.log_event(
            event_type=AuditEventType.LOGOUT,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="logout",
        )

    def log_access_denied(
        self,
        user_id: Optional[str],
        resource: str,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log access denial."""
        self.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action="access",
            success=False,
            error_message=reason,
        )

    def log_data_export(
        self,
        user_id: Optional[str],
        export_format: str,
        record_count: int,
        filters: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log data export."""
        self.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user_id,
            ip_address=ip_address,
            resource="bills",
            action="export",
            details={
                "format": export_format,
                "record_count": record_count,
                "filters": filters or {},
            },
        )

    def log_admin_action(
        self,
        user_id: str,
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log admin action."""
        self.log_event(
            event_type=AuditEventType.ADMIN_ACTION,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            details=details,
        )

    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        limit: int,
    ) -> None:
        """Log rate limit exceeded."""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address=ip_address,
            resource=endpoint,
            action="request",
            success=False,
            details={"limit": limit},
        )

    def log_security_violation(
        self,
        ip_address: Optional[str],
        violation_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security violation."""
        self.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            ip_address=ip_address,
            action=violation_type,
            success=False,
            details=details,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def init_audit_logger(
    log_dir: Optional[Path] = None,
    log_file: str = "audit.log",
    enable_file_logging: bool = True,
) -> AuditLogger:
    """Initialize global audit logger."""
    global _audit_logger
    _audit_logger = AuditLogger(
        log_dir=log_dir,
        log_file=log_file,
        enable_file_logging=enable_file_logging,
    )
    return _audit_logger
