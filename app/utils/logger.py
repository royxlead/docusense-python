"""
Logging and monitoring utilities.

This module provides centralized logging configuration and utilities
for tracking events, errors, and audit trails throughout the application.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import settings


def setup_logging(
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Path to log file (if None, logs to console only)
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    log_dir = settings.BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # File handler (if specified or default)
    if log_file is None:
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)
    
    # JSON handler for structured logging
    json_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"app_structured_{datetime.now().strftime('%Y%m%d')}.json",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    json_handler.setFormatter(JSONFormatter())
    logging.getLogger().addHandler(json_handler)
    
    logging.info("Logging system initialized")


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                             'pathname', 'filename', 'module', 'lineno', 
                             'funcName', 'created', 'msecs', 'relativeCreated',
                             'thread', 'threadName', 'processName', 'process',
                             'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_entry[key] = value
        
        return json.dumps(log_entry)


def log_event(
    event_type: str,
    details: Dict[str, Any],
    logger_name: str = "app.events",
    level: str = "INFO"
) -> None:
    """
    Log a structured event with details.
    
    Args:
        event_type: Type of event (e.g., 'document_processed', 'user_login')
        details: Dictionary containing event details
        logger_name: Name of the logger to use
        level: Log level for the event
    """
    logger = logging.getLogger(logger_name)
    log_level = getattr(logging, level.upper())
    
    # Create structured log entry
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        **details
    }
    
    # Log with extra data
    logger.log(log_level, f"Event: {event_type}", extra=log_data)


def log_api_call(
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_status: Optional[int] = None,
    processing_time: Optional[float] = None
) -> None:
    """
    Log API call details for monitoring and audit.
    
    Args:
        endpoint: API endpoint that was called
        method: HTTP method (GET, POST, etc.)
        user_id: ID of the user making the request
        request_data: Request data (sanitized)
        response_status: HTTP response status code
        processing_time: Time taken to process the request
    """
    details = {
        "endpoint": endpoint,
        "method": method,
        "user_id": user_id,
        "response_status": response_status,
        "processing_time_seconds": processing_time
    }
    
    # Add sanitized request data (remove sensitive info)
    if request_data:
        sanitized_data = _sanitize_request_data(request_data)
        details["request_data"] = sanitized_data
    
    log_event("api_call", details, "app.api")


def log_document_processing(
    document_id: str,
    file_path: str,
    processing_stage: str,
    status: str,
    processing_time: Optional[float] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log document processing events.
    
    Args:
        document_id: Unique identifier for the document
        file_path: Path to the document file
        processing_stage: Stage of processing (ocr, summarization, etc.)
        status: Processing status (started, completed, failed)
        processing_time: Time taken for this stage
        error_message: Error message if processing failed
        metadata: Additional metadata about the processing
    """
    details = {
        "document_id": document_id,
        "file_path": str(file_path),
        "processing_stage": processing_stage,
        "status": status,
        "processing_time_seconds": processing_time
    }
    
    if error_message:
        details["error_message"] = error_message
    
    if metadata:
        details["metadata"] = metadata
    
    log_level = "ERROR" if status == "failed" else "INFO"
    log_event("document_processing", details, "app.processing", log_level)


def log_search_query(
    query: str,
    user_id: Optional[str] = None,
    results_count: Optional[int] = None,
    processing_time: Optional[float] = None,
    filters: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log search query events for analytics.
    
    Args:
        query: Search query string
        user_id: ID of the user performing the search
        results_count: Number of results returned
        processing_time: Time taken to process the search
        filters: Search filters applied
    """
    details = {
        "query": query,
        "user_id": user_id,
        "results_count": results_count,
        "processing_time_seconds": processing_time,
        "filters": filters
    }
    
    log_event("search_query", details, "app.search")


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = "app.errors"
) -> None:
    """
    Log error with context information.
    
    Args:
        error: Exception that occurred
        context: Additional context about when/where the error occurred
        logger_name: Name of the logger to use
    """
    logger = logging.getLogger(logger_name)
    
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    
    logger.error(f"Error occurred: {error}", extra=error_details, exc_info=True)


def _sanitize_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from request data before logging.
    
    Args:
        data: Request data to sanitize
        
    Returns:
        Dict[str, Any]: Sanitized data
    """
    sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']
    sanitized = {}
    
    for key, value in data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_request_data(value)
        else:
            sanitized[key] = value
    
    return sanitized


def get_log_statistics(log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about logged events.
    
    Args:
        log_file: Path to log file to analyze
        
    Returns:
        Dict[str, Any]: Log statistics
    """
    try:
        if log_file is None:
            log_dir = settings.BASE_DIR / "logs"
            log_file = log_dir / f"app_structured_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not os.path.exists(log_file):
            return {"error": "Log file not found"}
        
        stats = {
            "total_events": 0,
            "event_types": {},
            "log_levels": {},
            "file_size_mb": os.path.getsize(log_file) / (1024 * 1024)
        }
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    stats["total_events"] += 1
                    
                    # Count event types
                    event_type = entry.get("event_type", "unknown")
                    stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
                    
                    # Count log levels
                    level = entry.get("level", "unknown")
                    stats["log_levels"][level] = stats["log_levels"].get(level, 0) + 1
                    
                except json.JSONDecodeError:
                    continue
        
        return stats
        
    except Exception as e:
        return {"error": f"Failed to analyze logs: {str(e)}"}


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()