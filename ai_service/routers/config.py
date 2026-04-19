"""Configuration routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from database.db import get_db
from database.repositories import ConfigRepository
from schemas import ConfigResponse
from services.config_builder import build_limits, cfg_float
from settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Config"])


@router.get("/config", response_model=ConfigResponse)
async def get_config(db=Depends(get_db)):
    """Get configuration and limits."""
    try:
        config_repo = ConfigRepository(db)
        raw_config = config_repo.get_current_config()
        limits = build_limits(raw_config)

        return ConfigResponse(
            sampling_rate_hz=cfg_float(raw_config, "telemetry_collection_interval", 1.0),
            limits=limits,
            units={
                "wob": "klbf",
                "torque": "kft-lb",
                "rop": "ft/hr",
                "dls": "deg/100ft",
                "vibration": "g"
            },
            system_mode=settings.SYSTEM_MODE,
        )
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")
