import sys
import os
# Add the current directory to Python path for consistent imports
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, WebSocket, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime, timedelta
import logging
import pandas as pd
import joblib
import json
import asyncio
import jwt
import os

# Database imports
from database.db import get_db, check_database_connection
from database.repositories import (
    UserRepository, TelemetryRepository, DecisionRepository,
    AlertRepository, ConfigRepository
)
from database.schemas import (
    UserRole, TelemetryPacketCreate, DecisionCreate,
    AlertCreate, AlertSeverity, AlertStatus
)

# Authentication setup
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

# Authentication models
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
    role: str  # "operator", "engineer", "admin"
    disabled: Optional[bool] = None

# Authentication models
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
    role: str  # "operator", "engineer", "admin"
    disabled: Optional[bool] = None

def verify_password(plain_password, stored_password):
    """Verify a password (simplified for demo)"""
    return plain_password == stored_password

def get_user(username: str, db = Depends(get_db)):
    """Get user from database"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(username)
        if user and user.is_active:
            return User(
                username=user.username,
                role=user.role.value,  # Convert enum to string
                disabled=not user.is_active
            )
        return None
    except Exception as e:
        logger.error(f"Database error getting user {username}: {e}")
        return None

def authenticate_user(username: str, password: str, db = Depends(get_db)):
    """Authenticate a user"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.authenticate_user(username, password)
        if user:
            return User(
                username=user.username,
                role=user.role.value,
                disabled=not user.is_active
            )
        return None
    except Exception as e:
        logger.error(f"Authentication error for {username}: {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db = Depends(get_db)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Dependency to require specific role"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        role_hierarchy = {"operator": 1, "engineer": 2, "admin": 3}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}, Current: {current_user.role}"
            )
        return current_user
    return role_checker
from dataset import load_controls, get_next_telemetry, get_data_quality
from logging_config import setup_logging, log_prediction, log_model_load
from settings import settings

# Setup structured logging
logger = setup_logging(__name__, settings.LOG_LEVEL)

# Global model variables
ml_model = None
model_schema = None
model_metrics = None
model_available = False

def load_ml_model():
    """Load ML model and artifacts on startup"""
    global ml_model, model_schema, model_metrics, model_available

    try:
        if os.path.exists(settings.MODEL_PATH) and os.path.exists(settings.SCHEMA_PATH):
            ml_model = joblib.load(settings.MODEL_PATH)
            model_schema = joblib.load(settings.SCHEMA_PATH)

            if os.path.exists(settings.METRICS_PATH):
                with open(settings.METRICS_PATH, 'r') as f:
                    model_metrics = json.load(f)

            model_available = True
            log_model_load(logger, True, settings.MODEL_PATH)
            logger.info(f"Model version: {model_metrics.get('model_version', 'unknown')}")
        else:
            logger.warning("ML model files not found, falling back to rule-based logic")
            log_model_load(logger, False, settings.MODEL_PATH, "Model files not found")
            model_available = False
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        log_model_load(logger, False, settings.MODEL_PATH, str(e))
        model_available = False

# Load model on startup
load_ml_model()

app = FastAPI(
    title="Drilling Insight AI Service",
    description="AI-powered steering recommendations for drill operations",
    version="1.0.0"
)

# Enable CORS with configurable origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

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

class PredictResponse(BaseModel):
    recommendation: str
    confidence: float
    gate_status: Literal["ACCEPTED", "REDUCED", "REJECTED"]
    alert_message: str
    decision_record: DecisionRecord

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
    gamma_gapi: float
    resistivity_ohm_m: float
    phif: float
    vsh: float
    sw: float
    klogh: float
    formation_class: str

class DataQualityResponse(BaseModel):
    total_rows: int
    missing_rate_by_column: Dict[str, float]
    gaps_detected: int
    outlier_counts: Dict[str, int]

# Authentication models
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
    role: str  # "operator", "engineer", "admin"
    disabled: Optional[bool] = None

@app.get("/health")
async def health_check(db = Depends(get_db)):
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Check database connectivity
    try:
        if check_database_connection():
            # Test basic database operations
            telemetry_repo = TelemetryRepository(db)
            latest_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=1)
            health_status["checks"]["database"] = {
                "status": "healthy",
                "details": f"Database connected, telemetry available: {len(latest_telemetry) > 0}"
            }
        else:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "details": "Database connection failed"
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "details": f"Database error: {str(e)}"
        }
        health_status["status"] = "unhealthy"

    # Check model loading
    try:
        if model_available and ml_model is not None:
            health_status["checks"]["model"] = {
                "status": "healthy",
                "details": f"Model loaded, version: {model_metrics.get('model_version', 'unknown')}"
            }
        else:
            health_status["checks"]["model"] = {
                "status": "unhealthy",
                "details": "Model not loaded"
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["model"] = {
            "status": "unhealthy",
            "details": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check schema availability
    try:
        if model_schema is not None:
            health_status["checks"]["schema"] = {
                "status": "healthy",
                "details": "Model schema available"
            }
        else:
            health_status["checks"]["schema"] = {
                "status": "unhealthy",
                "details": "Model schema not available"
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["schema"] = {
            "status": "unhealthy",
            "details": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check telemetry data availability
    try:
        telemetry_repo = TelemetryRepository(db)
        recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=10)
        if recent_telemetry:
            health_status["checks"]["telemetry"] = {
                "status": "healthy",
                "details": f"Recent telemetry available: {len(recent_telemetry)} records"
            }
        else:
            health_status["checks"]["telemetry"] = {
                "status": "degraded",
                "details": "No recent telemetry data available"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["telemetry"] = {
            "status": "unhealthy",
            "details": f"Telemetry check failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"

    return health_status

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserCredentials, db = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = authenticate_user(credentials.username, credentials.password, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.get("/config", response_model=ConfigResponse)
async def get_config(db = Depends(get_db)):
    """Get configuration and limits"""
    try:
        config_repo = ConfigRepository(db)
        config_data = config_repo.get_current_config()

        # Convert database config to response format
        limits = Limits(
            confidence_reject_threshold=float(config_data.get("alert_threshold_critical", 0.3)),
            confidence_reduce_threshold=float(config_data.get("alert_threshold_high", 0.5)),
            dls_reject_threshold=float(config_data.get("dls_reject_threshold", 3.0)),
            dls_reduce_threshold=float(config_data.get("dls_reduce_threshold", 2.0)),
            vibration_reject_threshold=float(config_data.get("vibration_reject_threshold", 0.5)),
            vibration_reduce_threshold=float(config_data.get("vibration_reduce_threshold", 0.3)),
            max_vibration_g=float(config_data.get("max_vibration_g", 0.5)),
            max_dls_deg_100ft=float(config_data.get("max_dls_deg_100ft", 3.0)),
            wob_range=[float(config_data.get("wob_min", 20)), float(config_data.get("wob_max", 60))],
            torque_range=[float(config_data.get("torque_min", 0)), float(config_data.get("torque_max", 50))],
            rpm_range=[float(config_data.get("rpm_min", 50)), float(config_data.get("rpm_max", 300))],
        )

        return ConfigResponse(
            sampling_rate_hz=float(config_data.get("telemetry_collection_interval", 1.0)),
            limits=limits,
            units={
                "wob": "klbf",
                "torque": "kft-lb",
                "rop": "ft/hr",
                "dls": "deg/100ft",
                "vibration": "g"
            }
        )
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")

@app.get("/telemetry/next", response_model=TelemetryResponse)
async def get_next_telemetry_endpoint(db = Depends(get_db)):
    """Get next telemetry record from database"""
    try:
        telemetry_repo = TelemetryRepository(db)
        # Get latest telemetry from the first active well
        # In a real implementation, you might want to cycle through wells or use a specific well
        telemetry_data = telemetry_repo.get_latest_by_well("well_001", limit=1)

        if not telemetry_data:
            raise HTTPException(status_code=404, detail="No telemetry data available")

        latest_packet = telemetry_data[0]

        return TelemetryResponse(
            timestamp=latest_packet.timestamp.isoformat(),
            depth_ft=latest_packet.depth,
            wob_klbf=latest_packet.wob,
            torque_kftlb=latest_packet.torque,
            rpm=latest_packet.rpm,
            vibration_g=latest_packet.vibration,
            inclination_deg=latest_packet.inclination,
            azimuth_deg=latest_packet.azimuth,
            rop_ft_hr=latest_packet.rop,
            dls_deg_100ft=latest_packet.dls,
            gamma_gapi=latest_packet.gamma_ray,
            resistivity_ohm_m=latest_packet.resistivity,
            phif=latest_packet.porosity,
            vsh=latest_packet.volume_shale,
            sw=latest_packet.water_saturation,
            klogh=latest_packet.permeability,
            formation_class=latest_packet.formation_type or "Unknown"
        )
    except Exception as e:
        logger.error(f"Telemetry retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve telemetry: {str(e)}")

@app.get("/telemetry/quality", response_model=DataQualityResponse)
async def get_data_quality_endpoint(db = Depends(get_db)):
    """Get data quality metrics from database"""
    try:
        telemetry_repo = TelemetryRepository(db)
        # Get recent telemetry data for quality analysis
        recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=1000)

        if not recent_telemetry:
            return DataQualityResponse(
                total_rows=0,
                missing_rate_by_column={},
                gaps_detected=0,
                outlier_counts={"vibration": 0, "dls": 0, "wob": 0}
            )

        total_rows = len(recent_telemetry)

        # Calculate missing rates (simplified - in real implementation you'd check each field)
        missing_rates = {}

        # Simple gap detection based on timestamp differences
        timestamps = [packet.timestamp for packet in recent_telemetry]
        timestamps.sort()
        gaps = 0
        expected_interval = 30  # seconds, based on collection interval

        for i in range(1, len(timestamps)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            if time_diff > expected_interval * 2:  # Allow some tolerance
                gaps += 1

        # Outlier detection using simple statistics
        outlier_counts = {"vibration": 0, "dls": 0, "wob": 0}

        # Vibration outliers
        vibration_values = [packet.vibration for packet in recent_telemetry if packet.vibration is not None]
        if vibration_values:
            mean_vib = sum(vibration_values) / len(vibration_values)
            std_vib = (sum((x - mean_vib) ** 2 for x in vibration_values) / len(vibration_values)) ** 0.5
            outlier_counts["vibration"] = sum(1 for x in vibration_values if abs(x - mean_vib) > 3 * std_vib)

        # DLS outliers
        dls_values = [packet.dls for packet in recent_telemetry if packet.dls is not None]
        if dls_values:
            mean_dls = sum(dls_values) / len(dls_values)
            std_dls = (sum((x - mean_dls) ** 2 for x in dls_values) / len(dls_values)) ** 0.5
            outlier_counts["dls"] = sum(1 for x in dls_values if abs(x - mean_dls) > 3 * std_dls)

        # WOB outliers
        wob_values = [packet.wob for packet in recent_telemetry if packet.wob is not None]
        if wob_values:
            mean_wob = sum(wob_values) / len(wob_values)
            std_wob = (sum((x - mean_wob) ** 2 for x in wob_values) / len(wob_values)) ** 0.5
            outlier_counts["wob"] = sum(1 for x in wob_values if abs(x - mean_wob) > 3 * std_wob)

        return DataQualityResponse(
            total_rows=total_rows,
            missing_rate_by_column=missing_rates,
            gaps_detected=gaps,
            outlier_counts=outlier_counts
        )
    except Exception as e:
        logger.error(f"Data quality calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate data quality: {str(e)}")

@app.get("/model/metrics")
async def get_model_metrics(db = Depends(get_db)):
    """Get ML model metrics from loaded model."""
    try:
        # Return the loaded model metrics if available
        if model_available and model_metrics:
            return model_metrics
        else:
            # Fallback when the model is not loaded yet
            return {
                "available": model_available,
                "message": "Model not trained yet. Run 'python train.py' to train the model."
            }
    except Exception as e:
        logger.error(f"Model metrics retrieval error: {e}")
        return {
            "available": False,
            "message": f"Error retrieving model metrics: {str(e)}"
        }

def calculate_recommendation(dls: float, inclination: float, vibration: float) -> str:
    """Rule-based recommendation logic"""
    if dls > 6:
        return "Hold"
    elif inclination > 45:  # Assuming increasing inclination trend
        return "Drop"
    else:
        return "Build"

def calculate_confidence(dls: float, vibration: float, torque: float) -> float:
    """Calculate confidence based on how far values are from limits"""
    # Lower confidence near limits
    confidence = 0.95

    # Reduce confidence based on DLS (higher DLS = lower confidence)
    if dls > 4:
        confidence -= (dls - 4) * 0.05
    if dls > 6:
        confidence -= (dls - 6) * 0.1

    # Reduce confidence for high vibration
    if vibration > 2:
        confidence -= (vibration - 2) * 0.1

    # Reduce confidence for extreme torque
    if torque > 30000 or torque < 5000:
        confidence -= 0.1

    return max(0.55, min(0.95, confidence))

def determine_gate_status(confidence: float, dls: float, vibration: float) -> tuple[str, Optional[str]]:
    """Determine gate status and rejection reason"""
    if confidence < 0.6 or dls > 8:
        reason = "LOW_CONFIDENCE" if confidence < 0.6 else "LIMIT_EXCEEDED"
        return "REJECTED", reason
    elif dls >= 6 or vibration > 3:
        return "REDUCED", None
    else:
        return "ACCEPTED", None

def determine_gate_status_config(confidence: float, dls: float, vibration: float, limits: Limits) -> tuple[str, Optional[str]]:
    """Determine gate status using config limits"""
    if confidence < limits.confidence_reject_threshold or dls > limits.dls_reject_threshold or vibration > limits.vibration_reject_threshold:
        if confidence < limits.confidence_reject_threshold:
            reason = "LOW_CONFIDENCE"
        elif dls > limits.dls_reject_threshold:
            reason = "DLS_LIMIT_EXCEEDED"
        else:
            reason = "VIBRATION_LIMIT_EXCEEDED"
        return "REJECTED", reason
    elif dls >= limits.dls_reduce_threshold or vibration > limits.vibration_reduce_threshold:
        return "REDUCED", None
    else:
        return "ACCEPTED", None

def get_event_tags(dls: float, vibration: float, confidence: float) -> List[str]:
    """Generate event tags based on conditions"""
    tags = []
    if dls > 6:
        tags.append("high_dls")
    if vibration > 3:
        tags.append("high_vibration")
    if confidence < 0.7:
        tags.append("low_confidence")
    return tags

async def predict_streaming(request: PredictRequest, current_user: User, db = Depends(get_db)) -> PredictResponse:
    """AI prediction for streaming (simplified version without auth requirements)"""
    try:
        # Get config for thresholds
        config_repo = ConfigRepository(db)
        config_data = config_repo.get_current_config()

        # Create limits object from database config
        limits = Limits(
            confidence_reject_threshold=float(config_data.get("alert_threshold_critical", 0.3)),
            confidence_reduce_threshold=float(config_data.get("alert_threshold_high", 0.5)),
            dls_reject_threshold=float(config_data.get("dls_reject_threshold", 3.0)),
            dls_reduce_threshold=float(config_data.get("dls_reduce_threshold", 2.0)),
            vibration_reject_threshold=float(config_data.get("vibration_reject_threshold", 0.5)),
            vibration_reduce_threshold=float(config_data.get("vibration_reduce_threshold", 0.3)),
            max_vibration_g=float(config_data.get("max_vibration_g", 0.5)),
            max_dls_deg_100ft=float(config_data.get("max_dls_deg_100ft", 3.0)),
            wob_range=[float(config_data.get("wob_min", 20)), float(config_data.get("wob_max", 60))],
            torque_range=[float(config_data.get("torque_min", 0)), float(config_data.get("torque_max", 50))],
            rpm_range=[float(config_data.get("rpm_min", 50)), float(config_data.get("rpm_max", 300))],
        )

        # Calculate recommendation and confidence (same logic as main predict function)
        if model_available and ml_model is not None:
            model_version = "rf-cal-v1"
            input_data = pd.DataFrame([{
                'Formation_Class': request.Formation_Class or 'Sandstone',
                'WOB_klbf': request.WOB_klbf,
                'RPM_demo': request.RPM_demo,
                'ROP_ft_hr': request.ROP_ft_hr,
                'PHIF': request.PHIF if request.PHIF is not None else 0.18,
                'VSH': request.VSH if request.VSH is not None else 0.25,
                'SW': request.SW if request.SW is not None else 0.35,
                'KLOGH': request.KLOGH if request.KLOGH is not None else 120,
                'Torque_kftlb': request.Torque_kftlb,
                'Vibration_g': request.Vibration_g,
                'DLS_deg_per_100ft': request.DLS_deg_per_100ft,
                'Inclination_deg': request.Inclination_deg,
                'Azimuth_deg': request.Azimuth_deg
            }])
            recommendation = ml_model.predict(input_data)[0]
            probabilities = ml_model.predict_proba(input_data)[0]
            confidence = float(max(probabilities))
        else:
            model_version = "rules-v1"
            recommendation = calculate_recommendation(
                request.DLS_deg_per_100ft,
                request.Inclination_deg,
                request.Vibration_g
            )
            confidence = calculate_confidence(
                request.DLS_deg_per_100ft,
                request.Vibration_g,
                request.Torque_kftlb
            )

        # Determine gate status
        gate_status, rejection_reason = determine_gate_status_config(
            confidence,
            request.DLS_deg_per_100ft,
            request.Vibration_g,
            limits
        )

        # Generate alert message
        if gate_status == "REJECTED":
            alert_message = f"Recommendation rejected: {rejection_reason}"
        elif gate_status == "REDUCED":
            alert_message = "Recommendation accepted with reduced aggressiveness"
        else:
            alert_message = "Recommendation accepted"

        # Create decision record
        decision_record = DecisionRecord(
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_version,
            feature_summary={
                "WOB_klbf": request.WOB_klbf,
                "RPM_demo": request.RPM_demo,
                "ROP_ft_hr": request.ROP_ft_hr,
                "Torque_kftlb": request.Torque_kftlb,
                "Vibration_g": request.Vibration_g,
                "DLS_deg_per_100ft": request.DLS_deg_per_100ft,
                "Inclination_deg": request.Inclination_deg,
                "Azimuth_deg": request.Azimuth_deg
            },
            steering_command=recommendation,
            confidence_score=confidence,
            gate_outcome=gate_status,
            rejection_reason=rejection_reason,
            execution_status="BLOCKED" if gate_status == "REJECTED" else "SENT",
            fallback_mode="HOLD_STEERING" if gate_status == "REJECTED" else None,
            event_tags=get_event_tags(request.DLS_deg_per_100ft, request.Vibration_g, confidence)
        )

        # For streaming, we'll skip database persistence to avoid conflicts
        # In production, you might want to persist streaming decisions too

        return PredictResponse(
            recommendation=recommendation,
            confidence=confidence,
            gate_status=gate_status,
            alert_message=alert_message,
            decision_record=decision_record
        )

    except Exception as e:
        logger.error(f"Streaming prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict")
async def predict(request: PredictRequest, db = Depends(get_db)) -> PredictResponse:
    """AI prediction endpoint with database persistence"""
    try:
        # Get config for thresholds
        config_repo = ConfigRepository(db)
        config_data = config_repo.get_current_config()

        # Create limits object from database config
        limits = Limits(
            confidence_reject_threshold=float(config_data.get("alert_threshold_critical", 0.3)),
            confidence_reduce_threshold=float(config_data.get("alert_threshold_high", 0.5)),
            dls_reject_threshold=float(config_data.get("dls_reject_threshold", 3.0)),
            dls_reduce_threshold=float(config_data.get("dls_reduce_threshold", 2.0)),
            vibration_reject_threshold=float(config_data.get("vibration_reject_threshold", 0.5)),
            vibration_reduce_threshold=float(config_data.get("vibration_reduce_threshold", 0.3)),
            max_vibration_g=float(config_data.get("max_vibration_g", 0.5)),
            max_dls_deg_100ft=float(config_data.get("max_dls_deg_100ft", 3.0)),
            wob_range=[float(config_data.get("wob_min", 20)), float(config_data.get("wob_max", 60))],
            torque_range=[float(config_data.get("torque_min", 0)), float(config_data.get("torque_max", 50))],
            rpm_range=[float(config_data.get("rpm_min", 50)), float(config_data.get("rpm_max", 300))],
        )

        # If Depth_ft provided, lookup formation data from telemetry database
        if request.Depth_ft is not None:
            telemetry_repo = TelemetryRepository(db)
            # Get telemetry data near the requested depth
            recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=10)
            if recent_telemetry:
                # Use the most recent telemetry for formation data
                latest_packet = recent_telemetry[0]
                request.PHIF = request.PHIF if request.PHIF is not None else latest_packet.porosity
                request.VSH = request.VSH if request.VSH is not None else latest_packet.volume_shale
                request.SW = request.SW if request.SW is not None else latest_packet.water_saturation
                request.KLOGH = request.KLOGH if request.KLOGH is not None else latest_packet.permeability
                request.Formation_Class = request.Formation_Class or latest_packet.formation_type

        # Calculate recommendation and confidence
        if model_available and ml_model is not None:
            # Use ML model for prediction
            model_version = "rf-cal-v1"

            # Prepare input data in correct order
            input_data = pd.DataFrame([{
                'Formation_Class': request.Formation_Class or 'Sandstone',
                'WOB_klbf': request.WOB_klbf,
                'RPM_demo': request.RPM_demo,
                'ROP_ft_hr': request.ROP_ft_hr,
                'PHIF': request.PHIF if request.PHIF is not None else 0.18,
                'VSH': request.VSH if request.VSH is not None else 0.25,
                'SW': request.SW if request.SW is not None else 0.35,
                'KLOGH': request.KLOGH if request.KLOGH is not None else 120,
                'Torque_kftlb': request.Torque_kftlb,
                'Vibration_g': request.Vibration_g,
                'DLS_deg_per_100ft': request.DLS_deg_per_100ft,
                'Inclination_deg': request.Inclination_deg,
                'Azimuth_deg': request.Azimuth_deg
            }])

            # Get prediction and probabilities
            recommendation = ml_model.predict(input_data)[0]
            probabilities = ml_model.predict_proba(input_data)[0]
            confidence = float(max(probabilities))  # Max probability as confidence

        else:
            # Fallback to rule-based logic
            model_version = "rules-v1"
            recommendation = calculate_recommendation(
                request.DLS_deg_per_100ft,
                request.Inclination_deg,
                request.Vibration_g
            )
            confidence = calculate_confidence(
                request.DLS_deg_per_100ft,
                request.Vibration_g,
                request.Torque_kftlb
            )

        # Determine gate status using config limits
        gate_status, rejection_reason = determine_gate_status_config(
            confidence,
            request.DLS_deg_per_100ft,
            request.Vibration_g,
            limits
        )

        # Generate alert message
        if gate_status == "REJECTED":
            alert_message = f"Recommendation rejected: {rejection_reason}"
        elif gate_status == "REDUCED":
            alert_message = "Recommendation accepted with reduced aggressiveness"
        else:
            alert_message = "Recommendation accepted"

        # Create decision record
        decision_record = DecisionRecord(
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_version,
            feature_summary={
                "WOB_klbf": request.WOB_klbf,
                "RPM_demo": request.RPM_demo,
                "ROP_ft_hr": request.ROP_ft_hr,
                "Torque_kftlb": request.Torque_kftlb,
                "Vibration_g": request.Vibration_g,
                "DLS_deg_per_100ft": request.DLS_deg_per_100ft,
                "Inclination_deg": request.Inclination_deg,
                "Azimuth_deg": request.Azimuth_deg
            },
            steering_command=recommendation,
            confidence_score=confidence,
            gate_outcome=gate_status,
            rejection_reason=rejection_reason,
            execution_status="BLOCKED" if gate_status == "REJECTED" else "SENT",
            fallback_mode="HOLD_STEERING" if gate_status == "REJECTED" else None,
            event_tags=get_event_tags(request.DLS_deg_per_100ft, request.Vibration_g, confidence)
        )

        # Persist decision to database
        decision_repo = DecisionRepository(db)
        decision_data = DecisionCreate(
            well_id="well_001",  # In real implementation, this would come from context
            user_id=current_user.username,  # Using username as user_id for now
            model_version=model_version,
            timestamp=datetime.fromisoformat(decision_record.timestamp),
            features=decision_record.feature_summary,
            recommendation=recommendation,
            confidence=confidence,
            gate_status=gate_status,
            rejection_reason=rejection_reason,
            execution_status=decision_record.execution_status,
            event_tags=decision_record.event_tags
        )
        saved_decision = decision_repo.create_decision(decision_data)
        logger.info(f"Decision persisted to database: {saved_decision.id}")

        # Generate and persist alerts if needed
        alert_repo = AlertRepository(db)
        alerts_created = []

        if gate_status == "REJECTED":
            alert_data = AlertCreate(
                well_id="well_001",
                severity=AlertSeverity.CRITICAL,
                title="AI Recommendation Rejected",
                message=f"AI recommendation rejected due to {rejection_reason}",
                status=AlertStatus.ACTIVE,
                source="ai_prediction",
                metadata={
                    "confidence": confidence,
                    "dls": request.DLS_deg_per_100ft,
                    "vibration": request.Vibration_g,
                    "decision_id": str(saved_decision.id)
                }
            )
            alert = alert_repo.create_alert(alert_data)
            alerts_created.append(alert)
            logger.info(f"Critical alert created: {alert.id}")

        elif gate_status == "REDUCED":
            alert_data = AlertCreate(
                well_id="well_001",
                severity=AlertSeverity.WARNING,
                title="AI Recommendation Modified",
                message="AI recommendation accepted with reduced aggressiveness",
                status=AlertStatus.ACTIVE,
                source="ai_prediction",
                metadata={
                    "confidence": confidence,
                    "dls": request.DLS_deg_per_100ft,
                    "vibration": request.Vibration_g,
                    "decision_id": str(saved_decision.id)
                }
            )
            alert = alert_repo.create_alert(alert_data)
            alerts_created.append(alert)
            logger.info(f"Warning alert created: {alert.id}")

        # Log prediction
        log_prediction(
            logger,
            timestamp=decision_record.timestamp,
            recommendation=recommendation,
            confidence=confidence,
            gate_status=gate_status,
            model_or_rules="MODEL" if model_available else "RULES",
        )

        return PredictResponse(
            recommendation=recommendation,
            confidence=confidence,
            gate_status=gate_status,
            alert_message=alert_message,
            decision_record=decision_record
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.websocket("/telemetry/stream")
async def telemetry_stream(websocket: WebSocket, db = Depends(get_db)):
    """WebSocket endpoint for real-time telemetry streaming with heartbeat support"""
    await websocket.accept()
    logger.info("WebSocket connection established for telemetry streaming")

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Real-time telemetry streaming started"
        })

        telemetry_repo = TelemetryRepository(db)
        last_telemetry_id = None
        message_count = 0
        
        # Heartbeat task to detect stale connections
        async def heartbeat():
            """Send periodic heartbeat to detect stale connections"""
            while True:
                try:
                    await asyncio.sleep(5)  # Send heartbeat every 5 seconds
                    if websocket.client_state.value == 1:  # CONNECTED state
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Heartbeat error: {e}")
                    break

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat())

        while True:
            try:
                # Get latest telemetry data from database
                recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=1)

                if recent_telemetry:
                    latest_packet = recent_telemetry[0]

                    # Only send if it's new data
                    if last_telemetry_id != latest_packet.id:
                        last_telemetry_id = latest_packet.id

                        # Send telemetry data
                        telemetry_data = {
                            "timestamp": latest_packet.timestamp.isoformat(),
                            "depth_ft": latest_packet.depth,
                            "wob_klbf": latest_packet.wob,
                            "torque_kftlb": latest_packet.torque,
                            "rpm": latest_packet.rpm,
                            "vibration_g": latest_packet.vibration,
                            "inclination_deg": latest_packet.inclination,
                            "azimuth_deg": latest_packet.azimuth,
                            "rop_ft_hr": latest_packet.rop,
                            "dls_deg_100ft": latest_packet.dls,
                            "gamma_gapi": latest_packet.gamma_ray,
                            "resistivity_ohm_m": latest_packet.resistivity,
                            "phif": latest_packet.porosity,
                            "vsh": latest_packet.volume_shale,
                            "sw": latest_packet.water_saturation,
                            "klogh": latest_packet.permeability,
                            "formation_class": latest_packet.formation_type or "Unknown"
                        }

                        await websocket.send_json({
                            "type": "telemetry",
                            "timestamp": datetime.now().isoformat(),
                            "data": telemetry_data
                        })

                        # Get AI recommendation if model is available
                        if model_available:
                            try:
                                # Create prediction request from telemetry data
                                predict_request = PredictRequest(
                                    WOB_klbf=telemetry_data["wob_klbf"],
                                    RPM_demo=telemetry_data["rpm"],
                                    ROP_ft_hr=telemetry_data["rop_ft_hr"],
                                    Torque_kftlb=telemetry_data["torque_kftlb"],
                                    Vibration_g=telemetry_data["vibration_g"],
                                    DLS_deg_per_100ft=telemetry_data["dls_deg_100ft"],
                                    Inclination_deg=telemetry_data["inclination_deg"],
                                    Azimuth_deg=telemetry_data["azimuth_deg"],
                                    Depth_ft=telemetry_data.get("depth_ft")
                                )

                                # For streaming, we'll create a mock user or skip user requirement
                                # In production, you'd want proper authentication for WebSocket
                                mock_user = User(username="system", role="operator", disabled=False)

                                # Get recommendation using the same logic as /predict endpoint
                                prediction_response = await predict_streaming(predict_request, mock_user, db)

                                await websocket.send_json({
                                    "type": "recommendation",
                                    "timestamp": datetime.now().isoformat(),
                                    "data": prediction_response.decision_record
                                })
                            except Exception as e:
                                logger.warning(f"Failed to get recommendation for streaming: {e}")

                        # Get data quality metrics periodically (every 10 messages)
                        message_count += 1
                        if message_count % 10 == 0:
                            try:
                                # Calculate data quality from recent telemetry
                                quality_response = await get_data_quality_endpoint(db)
                                await websocket.send_json({
                                    "type": "data_quality",
                                    "timestamp": datetime.now().isoformat(),
                                    "data": quality_response
                                })
                            except Exception as e:
                                logger.warning(f"Failed to get data quality for streaming: {e}")

                else:
                    # No telemetry data available
                    await websocket.send_json({
                        "type": "no_data",
                        "timestamp": datetime.now().isoformat(),
                        "message": "No telemetry data available in database"
                    })

                # Stream at 1Hz (adjustable)
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in telemetry streaming: {e}")
                await websocket.send_json({
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Streaming error: {str(e)}"
                })
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Cancel heartbeat task
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)