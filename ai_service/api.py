import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
from datetime import datetime
import os
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Drilling Insight AI Service",
    description="AI-powered steering recommendations for drill operations",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory where this api.py file is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "models/recommendation_model.pkl")

# Global state
MODEL = None
MODEL_LOADED = False
STARTUP_TIME = datetime.utcnow()

def load_model():
    """Load model with error handling"""
    global MODEL, MODEL_LOADED
    try:
        if os.path.exists(MODEL_PATH):
            MODEL = joblib.load(MODEL_PATH)
            MODEL_LOADED = True
            logger.info(f"Model loaded successfully from {MODEL_PATH}")
            return True
        else:
            logger.warning(f"Model file not found at {MODEL_PATH}")
            logger.info("API will work with fallback mock predictions")
            MODEL_LOADED = False
            return False
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.info("API will work with fallback mock predictions")
        MODEL_LOADED = False
        return False

# Load model on startup
load_model()

# Define schema for preprocessing
SCHEMA = {
    "cat_cols": ["Formation_Class"],
    "num_cols": [
        "WOB_klbf", "RPM_demo", "ROP_ft_hr", "PHIF", "VSH", "SW", "KLOGH",
        "Torque_kftlb", "Vibration_g", "DLS_deg_per_100ft",
        "Inclination_deg", "Azimuth_deg"
    ]
}

# Default control parameters
DEFAULT_CONTROLS = {
    "DLS normal max (deg/100ft)": 2.0,
    "DLS block max (deg/100ft)": 3.0,
    "Vibration caution max (g)": 0.5,
    "WOB low preference (klbf)": 20,
    "WOB high preference (klbf)": 60,
    "Confidence threshold": 0.5,
}

# Try to load controls from Excel
def load_controls():
    """Load control parameters from Excel with fallback to defaults"""
    try:
        excel_path = os.path.join(CURRENT_DIR, "models/rss_dashboard_dataset_built_recalc.xlsx")
        if os.path.exists(excel_path):
            controls_df = pd.read_excel(excel_path, sheet_name="Controls")
            controls = dict(zip(controls_df["Prototype Control Parameters"], controls_df["Unnamed: 1"]))
            logger.info(f"Controls loaded from Excel: {len(controls)} parameters")
            return controls
    except Exception as e:
        logger.warning(f"Could not load controls from Excel: {str(e)}")
    
    logger.info("Using default control parameters")
    return DEFAULT_CONTROLS

CONTROLS = load_controls()

def gate(row: dict, conf: float):
    """
    Safety gating logic to validate model recommendations against operational limits.
    Returns: (gate_outcome, rejection_reason, execution_status, fallback_mode, alert_message)
    """
    try:
        dls_normal = float(CONTROLS.get("DLS normal max (deg/100ft)", 2.0))
        dls_block = float(CONTROLS.get("DLS block max (deg/100ft)", 3.0))
        vib_max = float(CONTROLS.get("Vibration caution max (g)", 0.5))
        wob_low = float(CONTROLS.get("WOB low preference (klbf)", 20))
        wob_high = float(CONTROLS.get("WOB high preference (klbf)", 60))
        conf_th = float(CONTROLS.get("Confidence threshold", 0.5))

        dls = float(row.get("DLS_deg_per_100ft", 0))
        vib = float(row.get("Vibration_g", 0))
        wob = float(row.get("WOB_klbf", 0))

        # Critical conditions (reject immediately)
        if conf < conf_th:
            return ("REJECTED", "LOW_CONFIDENCE", "BLOCKED", "HOLD_STEERING", 
                   f"Confidence {conf:.2f} below threshold {conf_th}")

        if dls > dls_block:
            return ("REJECTED", "LIMIT_EXCEEDED", "BLOCKED", "HOLD_STEERING", 
                   f"DLS {dls:.2f} exceeds block limit {dls_block}")

        # Caution conditions (allow with warnings)
        caution_reasons = []
        if dls > dls_normal:
            caution_reasons.append(f"DLS {dls:.2f} in caution zone")
        if vib > vib_max:
            caution_reasons.append(f"Vibration {vib:.2f}g exceeds {vib_max}g")
        if not (wob_low <= wob <= wob_high):
            caution_reasons.append(f"WOB {wob:.1f} outside {wob_low}-{wob_high} band")

        if caution_reasons:
            return ("REDUCED", None, "SENT", None, "; ".join(caution_reasons))

        return ("ACCEPTED", None, "SENT", None, "Normal operation")
    except Exception as e:
        logger.error(f"Error in gating logic: {str(e)}")
        return ("REJECTED", "SENSOR_ANOMALY", "BLOCKED", "HOLD_STEERING", f"Gating error: {str(e)}")

class PredictRequest(BaseModel):
    """Request schema for steering recommendation prediction"""
    Depth_ft: Optional[float] = None
    WOB_klbf: float
    RPM_demo: float
    ROP_ft_hr: float
    PHIF: float
    VSH: float
    SW: float
    KLOGH: float
    Formation_Class: str
    Torque_kftlb: float
    Vibration_g: float
    DLS_deg_per_100ft: float
    Inclination_deg: float
    Azimuth_deg: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "WOB_klbf": 35.0,
                "RPM_demo": 110.0,
                "ROP_ft_hr": 75.0,
                "PHIF": 0.22,
                "VSH": 0.32,
                "SW": 0.42,
                "KLOGH": 0.52,
                "Torque_kftlb": 3500.0,
                "Vibration_g": 0.35,
                "DLS_deg_per_100ft": 1.8,
                "Inclination_deg": 50.0,
                "Azimuth_deg": 105.0,
                "Formation_Class": "Limestone"
            }
        }

@app.get("/health")
def health():
    """Detailed health check endpoint"""
    uptime_seconds = (datetime.utcnow() - STARTUP_TIME).total_seconds()
    return {
        "ok": True,
        "status": "healthy",
        "model_loaded": MODEL_LOADED,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.utcnow().isoformat(),
    }

def get_recommendation(inputs: dict) -> dict:
    """
    Get recommendation from the trained model.
    Falls back to mock prediction if model not available.
    
    Args:
        inputs: Dictionary with feature keys
    
    Returns:
        Dictionary with 'recommendation', 'confidence', and 'all_classes' keys
    """
    if not MODEL_LOADED or MODEL is None:
        logger.warning("Model not loaded, using fallback mock prediction")
        # Fallback mock prediction based on inputs
        vibration = float(inputs.get("Vibration_g", 0.5))
        dls = float(inputs.get("DLS_deg_per_100ft", 1.5))
        confidence = min(0.95, 0.6 + (1.0 - vibration / 5.0) * 0.2)
        
        if vibration > 1.5:
            rec = "Hold"
        elif dls > 2.0:
            rec = "Drop"
        else:
            rec = "Build"
        
        return {
            "recommendation": rec,
            "confidence": confidence,
            "all_classes": {"Build": 0.3, "Hold": 0.5, "Drop": 0.2}
        }
    
    try:
        # Create DataFrame with required features in correct order
        X = pd.DataFrame([inputs])[SCHEMA["cat_cols"] + SCHEMA["num_cols"]]
        
        # Get prediction and probability
        prediction = MODEL.predict(X)[0]
        probabilities = MODEL.predict_proba(X)[0]
        confidence = float(probabilities.max())
        
        logger.debug(f"Model prediction: {prediction} (confidence: {confidence:.3f})")
        
        return {
            "recommendation": str(prediction),
            "confidence": confidence,
            "all_classes": dict(zip(MODEL.classes_, [float(p) for p in probabilities]))
        }
    except Exception as e:
        logger.error(f"Error in model prediction: {str(e)}\n{traceback.format_exc()}")
        raise

@app.post("/predict")
def predict(req: PredictRequest):
    """
    Get steering recommendation for current telemetry.
    Includes safety gating and decision records.
    """
    try:
        row = req.model_dump()
        
        # Get model recommendation
        result = get_recommendation(row)
        rec = result["recommendation"]
        conf = result["confidence"]
        
        logger.info(f"Prediction: {rec} (confidence: {conf:.3f})")
        
        # Apply safety gating
        gate_status, rej_reason, exec_status, fallback_mode, alert_msg = gate(row, conf)
        
        # Map gate status to frontend expectations
        gate_outcome = "ACCEPTED" if gate_status in ("ACCEPTED", "REDUCED") else "REJECTED"
        event_tags = []
        if gate_status == "REDUCED":
            event_tags.append("reduced_mode")
        
        # Create decision record
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "rf-trained-v1",
            "feature_summary": {
                "mean_wob": float(row["WOB_klbf"]),
                "std_wob": 0.0,
                "mean_torque": float(row["Torque_kftlb"]),
                "std_torque": 0.0,
                "mean_rpm": float(row["RPM_demo"]),
                "std_rpm": 0.0,
                "mean_vibration": float(row["Vibration_g"]),
                "std_vibration": 0.0,
                "trend_inclination": 0.0,
                "trend_azimuth": 0.0,
                "instability_proxy": float(row["Vibration_g"] * row["DLS_deg_per_100ft"]),
            },
            "steering_command": rec,
            "confidence_score": float(conf),
            "gate_outcome": gate_outcome,
            "rejection_reason": rej_reason,
            "execution_status": exec_status,
            "fallback_mode": fallback_mode,
            "event_tags": event_tags + ([alert_msg] if alert_msg else []),
        }
        
        return {
            "recommendation": rec,
            "confidence": float(conf),
            "gate_status": gate_status,
            "alert_message": alert_msg,
            "decision_record": decision,
        }
    except Exception as e:
        logger.error(f"Error in predict endpoint: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/batch-predict")
def batch_predict(requests: List[PredictRequest]):
    """Batch prediction endpoint for multiple telemetry points"""
    try:
        results = []
        for req in requests:
            result = predict(req)
            results.append(result)
        return {"predictions": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error in batch predict endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@app.get("/model-info")
def model_info():
    """Get information about the loaded model"""
    try:
        if MODEL_LOADED and MODEL is not None:
            clf = MODEL.named_steps.get('clf')
            classes = list(MODEL.classes_) if hasattr(MODEL, 'classes_') else []
            
            return {
                "model_loaded": True,
                "model_type": type(clf).__name__ if clf else "Unknown",
                "classes": classes,
                "schema": SCHEMA,
                "controls": CONTROLS,
            }
        else:
            return {
                "model_loaded": False,
                "available_classes": ["Build", "Hold", "Drop"],  # Fallback
                "schema": SCHEMA,
                "controls": CONTROLS,
            }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Log server startup"""
    logger.info("="*60)
    logger.info("Drilling Insight AI Service Starting")
    logger.info(f"Model loaded: {MODEL_LOADED}")
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"Schema: {len(SCHEMA['num_cols'])} numeric, {len(SCHEMA['cat_cols'])} categorical features")
    logger.info(f"Controls loaded: {len(CONTROLS)} parameters")
    logger.info("="*60)

@app.on_event("shutdown")
async def shutdown_event():
    """Log server shutdown"""
    logger.info("Drilling Insight AI Service Shutting Down")