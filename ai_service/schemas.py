"""
API Pydantic models for request/response contracts.
Separated from route handlers for clean imports and testability.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Literal


# ============================================================================
# Authentication Models
# ============================================================================

class UserCredentials(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    role: str
    disabled: Optional[bool] = None


# ============================================================================
# Prediction Models
# ============================================================================

class PredictRequest(BaseModel):
    WOB_klbf: float
    RPM_demo: float
    ROP_ft_hr: float
    PHIF: Optional[float] = None
    VSH: Optional[float] = None
    SW: Optional[float] = None
    KLOGH: Optional[float] = None
    Formation_Class: Optional[str] = None
    Torque_kftlb: float
    Vibration_g: float
    DLS_deg_per_100ft: float
    Inclination_deg: float
    Azimuth_deg: float
    Depth_ft: Optional[float] = None

class PeteParameterStatus(BaseModel):
    name: str
    value: float
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    margin: float
    status: Literal["OK", "NEAR_LIMIT", "OUTSIDE"]

class PeteStatus(BaseModel):
    overall_status: Literal["WITHIN_LIMITS", "NEAR_LIMIT", "OUTSIDE_LIMITS"]
    parameter_margins: List[PeteParameterStatus]
    violations: List[str]
    max_dls_change: float
    formation_sensitivity: Optional[str] = None

class DecisionRecord(BaseModel):
    timestamp: str
    model_version: str
    feature_summary: Dict[str, float]
    steering_command: str
    confidence_score: float
    gate_outcome: Literal["ACCEPTED", "REDUCED", "REJECTED"]
    rejection_reason: Optional[str]
    execution_status: str
    fallback_mode: Optional[str]
    event_tags: List[str]
    pete_status: Optional[dict] = None
    system_mode: str = "SIMULATION"
    actuator_outcome: Optional[str] = None

class PredictResponse(BaseModel):
    recommendation: str
    confidence: float
    gate_status: Literal["ACCEPTED", "REDUCED", "REJECTED"]
    alert_message: str
    decision_record: DecisionRecord
    pete_status: Optional[PeteStatus] = None
    system_mode: str = "SIMULATION"
    actuator_status: Optional[dict] = None


# ============================================================================
# Configuration Models
# ============================================================================

class Limits(BaseModel):
    confidence_reject_threshold: float
    confidence_reduce_threshold: float
    dls_reject_threshold: float
    dls_reduce_threshold: float
    vibration_reject_threshold: float
    vibration_reduce_threshold: float
    max_vibration_g: float
    max_dls_deg_100ft: float
    wob_range: List[float]
    torque_range: List[float]
    rpm_range: List[float]

class ConfigResponse(BaseModel):
    sampling_rate_hz: float
    limits: Limits
    units: Dict[str, str]
    system_mode: str = "SIMULATION"


# ============================================================================
# Telemetry Models
# ============================================================================

class TelemetryResponse(BaseModel):
    timestamp: str
    depth_ft: float
    wob_klbf: float
    torque_kftlb: float
    rpm: float
    vibration_g: float
    inclination_deg: float
    azimuth_deg: float
    rop_ft_hr: float
    dls_deg_100ft: float
    gamma_gapi: float = 0.0
    resistivity_ohm_m: float = 0.0
    phif: float = 0.0
    vsh: float = 0.0
    sw: float = 0.0
    klogh: float = 0.0
    formation_class: str = "Unknown"

class DataQualityResponse(BaseModel):
    total_rows: int
    missing_rate_by_column: Dict[str, float]
    gaps_detected: int
    outlier_counts: Dict[str, int]


# ============================================================================
# Actuator Models
# ============================================================================

class FaultRequest(BaseModel):
    reason: str


# ============================================================================
# Admin Models
# ============================================================================

class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str = "operator"

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UpdateConfigRequest(BaseModel):
    value: Dict
    description: Optional[str] = None
