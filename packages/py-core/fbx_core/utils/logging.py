"""
Structured logging configuration for the application.
"""
import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pythonjsonlogger import jsonlogger
import os
from contextvars import ContextVar


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add environment
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        
        # Add service name
        log_record['service'] = os.getenv('SERVICE_NAME', 'federal-bills-explainer')
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_record['user_id'] = user_id
        
        # Add error details if this is an error log
        if record.exc_info:
            log_record['error_type'] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_record['error_message'] = str(record.exc_info[1]) if record.exc_info[1] else None
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        
        if hasattr(record, 'http_status'):
            log_record['http_status'] = record.http_status


class StructuredLogger:
    """Structured logger with context management."""
    
    def __init__(self, name: str, level: str = "INFO"):
        """Initialize the structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            json_indent=2 if os.getenv('LOG_PRETTY', 'false').lower() == 'true' else None
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for production
        if os.getenv('LOG_TO_FILE', 'false').lower() == 'true':
            file_handler = logging.FileHandler(
                os.getenv('LOG_FILE_PATH', '/var/log/federal-bills/app.log')
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def set_request_context(self, request_id: str, user_id: Optional[str] = None):
        """Set request context for logging."""
        request_id_var.set(request_id)
        if user_id:
            user_id_var.set(user_id)
    
    def clear_request_context(self):
        """Clear request context."""
        request_id_var.set(None)
        user_id_var.set(None)
    
    def log_api_request(self, method: str, path: str, **kwargs):
        """Log API request."""
        self.logger.info(
            "API request received",
            extra={
                "http_method": method,
                "http_path": path,
                "event_type": "api_request",
                **kwargs
            }
        )
    
    def log_api_response(self, status_code: int, duration_ms: float, **kwargs):
        """Log API response."""
        level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
        self.logger.log(
            level,
            "API response sent",
            extra={
                "http_status": status_code,
                "duration_ms": duration_ms,
                "event_type": "api_response",
                **kwargs
            }
        )
    
    def log_database_query(self, query: str, duration_ms: float, **kwargs):
        """Log database query."""
        self.logger.debug(
            "Database query executed",
            extra={
                "query": query[:500],  # Truncate long queries
                "duration_ms": duration_ms,
                "event_type": "db_query",
                **kwargs
            }
        )
    
    def log_external_api_call(self, service: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
        """Log external API call."""
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(
            level,
            f"External API call to {service}",
            extra={
                "service": service,
                "endpoint": endpoint,
                "http_status": status_code,
                "duration_ms": duration_ms,
                "event_type": "external_api_call",
                **kwargs
            }
        )
    
    def log_ai_generation(self, model: str, tokens: int, duration_ms: float, **kwargs):
        """Log AI content generation."""
        self.logger.info(
            "AI content generated",
            extra={
                "ai_model": model,
                "token_count": tokens,
                "duration_ms": duration_ms,
                "event_type": "ai_generation",
                **kwargs
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context."""
        self.logger.error(
            f"Error occurred: {str(error)}",
            exc_info=True,
            extra={
                "event_type": "error",
                "error_context": context or {},
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events."""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": "security",
                "security_event_type": event_type,
                "details": details
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms", **kwargs):
        """Log performance metrics."""
        self.logger.info(
            f"Performance metric: {metric_name}",
            extra={
                "event_type": "performance",
                "metric_name": metric_name,
                "metric_value": value,
                "metric_unit": unit,
                **kwargs
            }
        )


# Create default logger instance
logger = StructuredLogger(
    name="federal-bills-explainer",
    level=os.getenv("LOG_LEVEL", "INFO")
)