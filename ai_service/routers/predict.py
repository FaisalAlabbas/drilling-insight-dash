"""Prediction route — POST /predict with DB persistence."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from database.db import get_db
from database.repositories import ConfigRepository, DecisionRepository, AlertRepository, TelemetryRepository
from database.schemas import DecisionCreate, AlertCreate, AlertSeverity, AlertStatus
from schemas import PredictRequest, PredictResponse
from services.prediction import run_decision_pipeline
from logging_config import log_prediction
from settings import settings
import model_loader

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prediction"])


@router.post("/predict")
async def predict(request: PredictRequest, db=Depends(get_db)) -> PredictResponse:
    """AI prediction endpoint with database persistence."""
    try:
        # Get config for thresholds
        config_repo = ConfigRepository(db)
        config_data = config_repo.get_current_config()

        # Depth-based formation enrichment
        if request.Depth_ft is not None:
            telemetry_repo = TelemetryRepository(db)
            recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=10)
            if recent_telemetry:
                request.PHIF = request.PHIF if request.PHIF is not None else 0.15
                request.VSH = request.VSH if request.VSH is not None else 0.2
                request.SW = request.SW if request.SW is not None else 0.3
                request.KLOGH = request.KLOGH if request.KLOGH is not None else 100.0
                request.Formation_Class = request.Formation_Class or "Sandstone"

        # Run the shared decision pipeline
        result = run_decision_pipeline(request, config_data)

        # Persist decision to database
        decision_repo = DecisionRepository(db)
        decision_data = DecisionCreate(
            well_id="well_001",
            user_id="system",
            model_version=result.model_version,
            timestamp=datetime.fromisoformat(result.decision_record.timestamp),
            feature_summary=result.decision_record.feature_summary,
            steering_command=result.recommendation,
            confidence_score=result.confidence,
            gate_outcome=result.gate_status,
            rejection_reason=result.rejection_reason,
            execution_status=result.decision_record.execution_status,
            event_tags=result.decision_record.event_tags,
            system_mode=settings.SYSTEM_MODE,
            actuator_outcome=result.actuator_outcome,
        )
        saved_decision = decision_repo.create_decision(decision_data)
        logger.info(f"Decision persisted to database: {saved_decision.id}")

        # Generate and persist alerts if needed
        alert_repo = AlertRepository(db)

        if result.gate_status == "REJECTED":
            alert_data = AlertCreate(
                well_id="well_001",
                timestamp=datetime.utcnow(),
                severity=AlertSeverity.critical,
                title="AI Recommendation Rejected",
                message=f"AI recommendation rejected due to {result.rejection_reason}",
                status=AlertStatus.active,
                metadata={
                    "confidence": result.confidence,
                    "dls": request.DLS_deg_per_100ft,
                    "vibration": request.Vibration_g,
                    "decision_id": str(saved_decision.id)
                }
            )
            alert = alert_repo.create_alert(alert_data)
            logger.info(f"Critical alert created: {alert.id}")

        elif result.gate_status == "REDUCED":
            alert_data = AlertCreate(
                well_id="well_001",
                timestamp=datetime.utcnow(),
                severity=AlertSeverity.high,
                title="AI Recommendation Modified",
                message="AI recommendation accepted with reduced aggressiveness",
                status=AlertStatus.active,
                metadata={
                    "confidence": result.confidence,
                    "dls": request.DLS_deg_per_100ft,
                    "vibration": request.Vibration_g,
                    "decision_id": str(saved_decision.id)
                }
            )
            alert = alert_repo.create_alert(alert_data)
            logger.info(f"Warning alert created: {alert.id}")

        # Log prediction
        log_prediction(
            logger,
            timestamp=result.decision_record.timestamp,
            recommendation=result.recommendation,
            confidence=result.confidence,
            gate_status=result.gate_status,
            model_or_rules="MODEL" if model_loader.model_available else "RULES",
            system_mode=settings.SYSTEM_MODE,
        )

        return result.response

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
