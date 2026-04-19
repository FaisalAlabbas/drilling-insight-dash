"""
SQLAlchemy 2.0 ORM models for Drilling Insight Dashboard.
These models correspond to the PostgreSQL schema defined in the migrations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index, func, JSON, UUID
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

# from .db import metadata

# Enum types (matching PostgreSQL enums)
class UserRole(str, Enum):
    operator = "operator"
    engineer = "engineer"
    admin = "admin"

class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class GateOutcome(str, Enum):
    accepted = "ACCEPTED"
    reduced = "REDUCED"
    rejected = "REJECTED"

class ExecutionStatus(str, Enum):
    sent = "SENT"
    pending = "PENDING"
    blocked = "BLOCKED"
    failed = "FAILED"

class AlertStatus(str, Enum):
    active = "ACTIVE"
    acknowledged = "ACKNOWLEDGED"
    resolved = "RESOLVED"

class Base(DeclarativeBase):
    """Base class for all models."""

    # Common columns
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Using string for UUID
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.operator)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    decisions: Mapped[List["Decision"]] = relationship("Decision", back_populates="user")
    alerts_created: Mapped[List["Alert"]] = relationship("Alert", foreign_keys="Alert.user_id", back_populates="user")
    alerts_acknowledged: Mapped[List["Alert"]] = relationship("Alert", foreign_keys="Alert.acknowledged_by", back_populates="acknowledged_user")
    alerts_resolved: Mapped[List["Alert"]] = relationship("Alert", foreign_keys="Alert.resolved_by", back_populates="resolved_user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")

class Well(Base):
    """Well model for drilling operations."""
    __tablename__ = "wells"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    operator: Mapped[Optional[str]] = mapped_column(String(100))
    spud_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False))  # Date only
    total_depth_ft: Mapped[Optional[float]] = mapped_column(Float)
    current_depth_ft: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Relationships
    telemetry_packets: Mapped[List["TelemetryPacket"]] = relationship("TelemetryPacket", back_populates="well")
    decisions: Mapped[List["Decision"]] = relationship("Decision", back_populates="well")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="well")

class TelemetryPacket(Base):
    """Telemetry packet model for time-series drilling data."""
    __tablename__ = "telemetry_packets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    well_id: Mapped[str] = mapped_column(String, ForeignKey("wells.id", ondelete="CASCADE"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    wob_klbf: Mapped[Optional[float]] = mapped_column(Float)
    rpm: Mapped[Optional[float]] = mapped_column(Float)
    rop_ft_hr: Mapped[Optional[float]] = mapped_column(Float)
    torque_kftlb: Mapped[Optional[float]] = mapped_column(Float)
    vibration_g: Mapped[Optional[float]] = mapped_column(Float)
    dls_deg_100ft: Mapped[Optional[float]] = mapped_column(Float)
    inclination_deg: Mapped[Optional[float]] = mapped_column(Float)
    azimuth_deg: Mapped[Optional[float]] = mapped_column(Float)
    depth_ft: Mapped[Optional[float]] = mapped_column(Float)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float)
    pressure_psi: Mapped[Optional[float]] = mapped_column(Float)
    mud_flow_gpm: Mapped[Optional[float]] = mapped_column(Float)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    well: Mapped["Well"] = relationship("Well", back_populates="telemetry_packets")

    # Indexes for time-series optimization
    __table_args__ = (
        Index('idx_telemetry_well_timestamp', 'well_id', 'timestamp'),
        Index('idx_telemetry_timestamp', 'timestamp'),
        Index('idx_telemetry_well', 'well_id'),
        Index('idx_telemetry_depth', 'well_id', 'depth_ft'),
        Index('idx_telemetry_raw_data', 'raw_data', postgresql_using='gin'),
    )

class Decision(Base):
    """Decision model for AI steering recommendations."""
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    well_id: Mapped[str] = mapped_column(String, ForeignKey("wells.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    steering_command: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    gate_outcome: Mapped[Optional[GateOutcome]] = mapped_column(SQLEnum(GateOutcome))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    execution_status: Mapped[ExecutionStatus] = mapped_column(SQLEnum(ExecutionStatus), nullable=False, default=ExecutionStatus.pending)
    feature_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    event_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    related_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    system_mode: Mapped[Optional[str]] = mapped_column(String(20), default="SIMULATION")
    actuator_outcome: Mapped[Optional[str]] = mapped_column(String(30))

    # Relationships
    well: Mapped["Well"] = relationship("Well", back_populates="decisions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="decisions")

    # Indexes for well_id + timestamp queries
    __table_args__ = (
        Index('idx_decisions_well_timestamp', 'well_id', 'timestamp'),
        Index('idx_decisions_user', 'user_id'),
        Index('idx_decisions_status', 'execution_status'),
        Index('idx_decisions_gate_outcome', 'gate_outcome'),
        Index('idx_decisions_feature_summary', 'feature_summary', postgresql_using='gin'),
        Index('idx_decisions_event_tags', 'event_tags', postgresql_using='gin'),
    )

class Alert(Base):
    """Alert model for system notifications."""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    well_id: Mapped[str] = mapped_column(String, ForeignKey("wells.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[AlertSeverity] = mapped_column(SQLEnum(AlertSeverity), nullable=False, default=AlertSeverity.medium)
    status: Mapped[AlertStatus] = mapped_column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.active)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    alert_type: Mapped[Optional[str]] = mapped_column(String(50))
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    actual_value: Mapped[Optional[float]] = mapped_column(Float)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"))
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Relationships
    well: Mapped["Well"] = relationship("Well", back_populates="alerts")
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], back_populates="alerts_created")
    acknowledged_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[acknowledged_by], back_populates="alerts_acknowledged")
    resolved_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by], back_populates="alerts_resolved")

    # Indexes for well_id + timestamp queries
    __table_args__ = (
        Index('idx_alerts_well_timestamp', 'well_id', 'timestamp'),
        Index('idx_alerts_status', 'status'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_type', 'alert_type'),
        Index('idx_alerts_acknowledged_by', 'acknowledged_by'),
        Index('idx_alerts_resolved_by', 'resolved_by'),
        Index('idx_alerts_extra_metadata', 'extra_metadata', postgresql_using='gin'),
    )

class ModelVersion(Base):
    """Model version model for ML model management."""
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[Optional[str]] = mapped_column(String(100))
    training_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    accuracy: Mapped[Optional[float]] = mapped_column(Float)
    precision: Mapped[Optional[float]] = mapped_column(Float)
    recall: Mapped[Optional[float]] = mapped_column(Float)
    f1_score: Mapped[Optional[float]] = mapped_column(Float)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Indexes
    __table_args__ = (
        Index('idx_model_versions_version', 'version'),
        Index('idx_model_versions_type', 'model_type'),
        Index('idx_model_versions_active', 'is_active'),
        Index('idx_model_versions_metrics', 'metrics', postgresql_using='gin'),
        Index('idx_model_versions_schema', 'schema', postgresql_using='gin'),
    )

class SystemConfig(Base):
    """System configuration model."""
    __tablename__ = "system_config"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Indexes
    __table_args__ = (
        Index('idx_system_config_key', 'key'),
        Index('idx_system_config_value', 'value', postgresql_using='gin'),
    )

class AuditLog(Base):
    """Audit log model for compliance and security."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String)
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String)  # Using String for INET
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_user', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_session', 'session_id'),
    )