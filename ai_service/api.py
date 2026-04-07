from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime
import logging
import pandas as pd
import joblib
import json
import os
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}

@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get configuration and limits"""
    controls = load_controls()

    return ConfigResponse(
        sampling_rate_hz=1.0,  # Default 1Hz
        limits={
            "vibration_max_g": float(controls.get("Vibration caution max (g)", 0.5)),
            "dls_normal_max": float(controls.get("DLS normal max (deg/100ft)", 2.0)),
            "dls_block_max": float(controls.get("DLS block max (deg/100ft)", 3.0)),
            "wob_band_low": float(controls.get("WOB low preference (klbf)", 20)),
            "wob_band_high": float(controls.get("WOB high preference (klbf)", 60)),
            "confidence_threshold": float(controls.get("Confidence threshold", 0.5)),
        },
        units={
            "wob": "klbf",
            "torque": "kft-lb",
            "rop": "ft/hr",
            "dls": "deg/100ft",
            "vibration": "g"
        }
    )

@app.get("/telemetry/next", response_model=TelemetryResponse)
async def get_next_telemetry_endpoint():
    """Get next telemetry record from dataset"""
    data = get_next_telemetry()
    if not data:
        raise HTTPException(status_code=404, detail="No telemetry data available")

    return TelemetryResponse(**data)

@app.get("/telemetry/quality", response_model=DataQualityResponse)
async def get_data_quality_endpoint():
    """Get data quality metrics"""
    return DataQualityResponse(**get_data_quality())

@app.get("/model/metrics")
async def get_model_metrics():
    """Get ML model metrics if available"""
    if model_available and model_metrics:
        return model_metrics
    else:
        return {"available": False, "message": "Model not trained yet. Run 'python train.py' to train the model."}

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

@app.post("/predict")
async def predict(request: PredictRequest) -> PredictResponse:
    """AI prediction endpoint"""
    try:
        # Get config for thresholds
        config = await get_config()

        # If Depth_ft provided, lookup formation data from dataset
        if request.Depth_ft is not None:
            from .dataset import load_dashboard_data
            df = load_dashboard_data()
            if not df.empty and "Depth_ft" in df.columns:
                # Find closest depth
                closest_idx = (df["Depth_ft"] - request.Depth_ft).abs().idxmin()
                row = df.loc[closest_idx]

                # Use formation data from dataset if not provided in request
                request.PHIF = request.PHIF if request.PHIF is not None else float(row.get("PHIF", 0.18))
                request.VSH = request.VSH if request.VSH is not None else float(row.get("VSH", 0.25))
                request.SW = request.SW if request.SW is not None else float(row.get("SW", 0.35))
                request.KLOGH = request.KLOGH if request.KLOGH is not None else float(row.get("KLOGH", 120))
                request.Formation_Class = request.Formation_Class or str(row.get("Formation_Class", "Sandstone"))

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
            config.limits
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)