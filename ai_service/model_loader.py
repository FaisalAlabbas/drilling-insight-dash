"""
ML model loading and global model state.
Isolates model artifacts from the FastAPI app so they can be imported
independently by the prediction service.
"""

import os
import json
import joblib
import logging

from settings import settings
from logging_config import setup_logging, log_model_load

logger = setup_logging(__name__, settings.LOG_LEVEL)

# Global model state
ml_model = None
model_schema = None
model_metrics = None
model_available = False


def load_ml_model():
    """Load ML model and artifacts on startup."""
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
            logger.info(f"Model version: {model_metrics.get('model_version', 'unknown') if model_metrics else 'unknown'}")
        else:
            logger.warning("ML model files not found, falling back to rule-based logic")
            log_model_load(logger, False, settings.MODEL_PATH, "Model files not found")
            model_available = False
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")
        log_model_load(logger, False, settings.MODEL_PATH, str(e))
        model_available = False
