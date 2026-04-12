"""
Database layer for Drilling Insight Dashboard.
Provides SQLAlchemy 2.0 ORM models, repositories, and database utilities.
"""

from .db import get_db, create_database, get_session
from .models import (
    User, Well, TelemetryPacket, Decision, Alert,
    ModelVersion, SystemConfig, AuditLog
)
from .repositories import (
    UserRepository, TelemetryRepository, DecisionRepository,
    AlertRepository, ConfigRepository
)

__all__ = [
    "get_db", "create_database", "get_session",
    "User", "Well", "TelemetryPacket", "Decision", "Alert",
    "ModelVersion", "SystemConfig", "AuditLog",
    "UserRepository", "TelemetryRepository", "DecisionRepository",
    "AlertRepository", "ConfigRepository"
]