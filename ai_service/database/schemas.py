"""
Pydantic schemas for API requests and responses.
These schemas define the data validation and serialization for the API endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Enum types (matching database enums)
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

# Base schemas with common fields
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.operator
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)

class UserResponse(UserBase, BaseSchema):
    last_login_at: Optional[datetime] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Well schemas
class WellBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    operator: Optional[str] = Field(None, max_length=100)
    spud_date: Optional[datetime] = None
    total_depth_ft: Optional[float] = Field(None, gt=0)
    current_depth_ft: Optional[float] = Field(None, gt=0)
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = None

class WellCreate(WellBase):
    pass

class WellUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    operator: Optional[str] = Field(None, max_length=100)
    spud_date: Optional[datetime] = None
    total_depth_ft: Optional[float] = Field(None, gt=0)
    current_depth_ft: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WellResponse(WellBase, BaseSchema):
    pass

# Telemetry schemas
class TelemetryPacketBase(BaseModel):
    well_id: str
    timestamp: datetime
    wob_klbf: Optional[float] = None
    rpm: Optional[float] = None
    rop_ft_hr: Optional[float] = None
    torque_kftlb: Optional[float] = None
    vibration_g: Optional[float] = None
    dls_deg_100ft: Optional[float] = None
    inclination_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    depth_ft: Optional[float] = None
    temperature_c: Optional[float] = None
    pressure_psi: Optional[float] = None
    mud_flow_gpm: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)

class TelemetryPacketCreate(TelemetryPacketBase):
    pass

class TelemetryPacketResponse(TelemetryPacketBase, BaseSchema):
    pass

class TelemetryQuery(BaseModel):
    well_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)

# Decision schemas
class DecisionBase(BaseModel):
    well_id: str
    user_id: Optional[str] = None
    timestamp: datetime
    model_version: Optional[str] = Field(None, max_length=50)
    steering_command: str = Field(..., max_length=20)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    gate_outcome: Optional[GateOutcome] = None
    rejection_reason: Optional[str] = None
    execution_status: ExecutionStatus = ExecutionStatus.pending
    feature_summary: Optional[Dict[str, Any]] = None
    event_tags: Optional[List[str]] = None
    related_signals: Optional[Dict[str, Any]] = None
    system_mode: Optional[str] = "SIMULATION"
    actuator_outcome: Optional[str] = None

class DecisionCreate(DecisionBase):
    pass

class DecisionUpdate(BaseModel):
    execution_status: Optional[ExecutionStatus] = None
    rejection_reason: Optional[str] = None

class DecisionResponse(DecisionBase, BaseSchema):
    pass

class DecisionQuery(BaseModel):
    well_id: Optional[str] = None
    user_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_status: Optional[ExecutionStatus] = None
    gate_outcome: Optional[GateOutcome] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=200)

class PaginatedDecisionResponse(BaseModel):
    items: List[DecisionResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Alert schemas
class AlertBase(BaseModel):
    well_id: str
    user_id: Optional[str] = None
    timestamp: datetime
    severity: AlertSeverity = AlertSeverity.medium
    status: AlertStatus = AlertStatus.active
    title: str = Field(..., max_length=255)
    message: Optional[str] = None
    alert_type: Optional[str] = Field(None, max_length=50)
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    message: Optional[str] = None

class AlertResponse(AlertBase, BaseSchema):
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class AlertQuery(BaseModel):
    well_id: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    alert_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=200)

class PaginatedAlertResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Model Version schemas
class ModelVersionBase(BaseModel):
    version: str = Field(..., max_length=50)
    model_type: str = Field(..., max_length=50)
    algorithm: Optional[str] = Field(None, max_length=100)
    training_date: Optional[datetime] = None
    accuracy: Optional[float] = Field(None, ge=0, le=1)
    precision: Optional[float] = Field(None, ge=0, le=1)
    recall: Optional[float] = Field(None, ge=0, le=1)
    f1_score: Optional[float] = Field(None, ge=0, le=1)
    metrics: Optional[Dict[str, Any]] = None
    model_schema: Optional[Dict[str, Any]] = None
    is_active: bool = False

class ModelVersionCreate(ModelVersionBase):
    pass

class ModelVersionUpdate(BaseModel):
    accuracy: Optional[float] = Field(None, ge=0, le=1)
    precision: Optional[float] = Field(None, ge=0, le=1)
    recall: Optional[float] = Field(None, ge=0, le=1)
    f1_score: Optional[float] = Field(None, ge=0, le=1)
    metrics: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ModelVersionResponse(ModelVersionBase, BaseSchema):
    pass

# System Config schemas
class SystemConfigBase(BaseModel):
    key: str = Field(..., max_length=100)
    value: Dict[str, Any]
    description: Optional[str] = None
    is_encrypted: bool = False

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class SystemConfigResponse(SystemConfigBase, BaseSchema):
    pass

# Audit Log schemas
class AuditLogBase(BaseModel):
    timestamp: datetime
    user_id: Optional[str] = None
    action: str = Field(..., max_length=50)
    resource_type: str = Field(..., max_length=50)
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = Field(None, max_length=255)

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase, BaseSchema):
    pass

# Health check schemas
class HealthCheckResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]

# API Response schemas
class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int