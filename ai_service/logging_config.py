"""
Structured logging configuration for the AI service backend.
Provides consistent logging setup with JSON formatting support.
"""

import logging
import json
from datetime import datetime
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup structured logging for the application.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Only add handler if one doesn't already exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class LogContext:
    """Context manager for adding extra data to logs"""

    def __init__(self, logger: logging.Logger, **extra_data):
        self.logger = logger
        self.extra_data = extra_data
        self._original_factory = None

    def __enter__(self):
        # Temporarily replace the logger's makeRecord to add extra_data
        self._original_factory = self.logger.makeRecord

        def makeRecord(*args, **kwargs):
            record = self._original_factory(*args, **kwargs)
            record.extra_data = self.extra_data
            return record

        self.logger.makeRecord = makeRecord
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._original_factory:
            self.logger.makeRecord = self._original_factory


def log_prediction(
    logger: logging.Logger,
    timestamp: str,
    recommendation: str,
    confidence: float,
    gate_status: str,
    model_or_rules: str,
    user_id: Optional[str] = None,
    system_mode: Optional[str] = None,
) -> None:
    """
    Log a prediction result with structured data.

    Args:
        logger: Logger instance
        timestamp: Prediction timestamp
        recommendation: Steering command recommendation
        confidence: Confidence score (0-1)
        gate_status: Safety gate outcome (ACCEPTED, REDUCED, REJECTED)
        model_or_rules: Source of recommendation (MODEL or RULES)
        user_id: Optional user ID
        system_mode: Operating mode (SIMULATION or PROTOTYPE)
    """
    extra_data = {
        "event": "prediction",
        "timestamp": timestamp,
        "recommendation": recommendation,
        "confidence": round(confidence, 3),
        "gate_status": gate_status,
        "source": model_or_rules,
    }
    if user_id:
        extra_data["user_id"] = user_id
    if system_mode:
        extra_data["system_mode"] = system_mode

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Prediction generated",
        args=(),
        exc_info=None,
    )
    record.extra_data = extra_data
    logger.handle(record)


def log_model_load(logger: logging.Logger, success: bool, path: str, error: Optional[str] = None) -> None:
    """
    Log model loading event.

    Args:
        logger: Logger instance
        success: Whether model loaded successfully
        path: Path to model file
        error: Optional error message
    """
    extra_data = {
        "event": "model_load",
        "success": success,
        "model_path": path,
    }
    if error:
        extra_data["error"] = error

    level = logging.INFO if success else logging.WARNING
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname="",
        lineno=0,
        msg="Model loading" if success else "Model load failed",
        args=(),
        exc_info=None,
    )
    record.extra_data = extra_data
    logger.handle(record)


def log_actuator_event(
    logger: logging.Logger,
    command: str,
    outcome: str,
    state: str,
    is_simulated: bool,
    message: str,
    system_mode: Optional[str] = None,
) -> None:
    """
    Log a virtual actuator event with structured data.

    Args:
        logger: Logger instance
        command: Steering command that was sent
        outcome: Actuator outcome (ACK_EXECUTED, ACK_REDUCED, etc.)
        state: Current actuator state after execution
        is_simulated: Whether this was a simulated execution
        message: Human-readable description
        system_mode: Operating mode (SIMULATION or PROTOTYPE)
    """
    extra_data: dict[str, Any] = {
        "event": "actuator",
        "command": command,
        "outcome": outcome,
        "actuator_state": state,
        "is_simulated": is_simulated,
        "message": message,
    }
    if system_mode:
        extra_data["system_mode"] = system_mode

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Actuator {outcome}: {command}",
        args=(),
        exc_info=None,
    )
    record.extra_data = extra_data
    logger.handle(record)
