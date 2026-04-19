"""Health check router."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from database.db import get_db, check_database_connection
from database.repositories import TelemetryRepository
from actuator import virtual_actuator
from settings import settings
import model_loader

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db=Depends(get_db)):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_mode": settings.SYSTEM_MODE,
        "telemetry_source": "Simulated telemetry" if settings.SYSTEM_MODE == "SIMULATION" else "Prototype telemetry",
        "checks": {}
    }

    # Check database connectivity
    try:
        if check_database_connection():
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
        if model_loader.model_available and model_loader.ml_model is not None:
            health_status["checks"]["model"] = {
                "status": "healthy",
                "details": f"Model loaded, version: {model_loader.model_metrics.get('model_version', 'unknown') if model_loader.model_metrics else 'unknown'}"
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
        if model_loader.model_schema is not None:
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

    # Check virtual actuator
    actuator_state = virtual_actuator.get_status()
    if actuator_state["state"] in ("FAULT", "MANUAL"):
        health_status["checks"]["actuator"] = {
            "status": "degraded",
            "details": f"Actuator in {actuator_state['state']} state" + (f": {actuator_state['fault_reason']}" if actuator_state.get('fault_reason') else "")
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["actuator"] = {
            "status": "healthy",
            "details": f"Actuator {actuator_state['state']}, commands processed: {actuator_state['command_count']}"
        }

    # Backward-compatible flag used by tests and clients
    health_status["ok"] = health_status["status"] == "healthy"

    return health_status
