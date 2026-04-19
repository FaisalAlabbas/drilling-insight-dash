"""Telemetry routes — REST + WebSocket streaming."""

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket

from database.db import get_db
from database.repositories import TelemetryRepository, ConfigRepository
from schemas import TelemetryResponse, DataQualityResponse, PredictRequest
from services.prediction import run_decision_pipeline
from actuator import virtual_actuator
from settings import settings
import model_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/next", response_model=TelemetryResponse)
async def get_next_telemetry_endpoint(db=Depends(get_db)):
    """Get next telemetry record from database."""
    try:
        telemetry_repo = TelemetryRepository(db)
        telemetry_data = telemetry_repo.get_latest_by_well("well_001", limit=1)

        if not telemetry_data:
            raise HTTPException(status_code=404, detail="No telemetry data available")

        latest_packet = telemetry_data[0]

        return TelemetryResponse(
            timestamp=latest_packet.timestamp.isoformat(),
            depth_ft=latest_packet.depth_ft or 0.0,
            wob_klbf=latest_packet.wob_klbf or 0.0,
            torque_kftlb=latest_packet.torque_kftlb or 0.0,
            rpm=latest_packet.rpm or 0.0,
            vibration_g=latest_packet.vibration_g or 0.0,
            inclination_deg=latest_packet.inclination_deg or 0.0,
            azimuth_deg=latest_packet.azimuth_deg or 0.0,
            rop_ft_hr=latest_packet.rop_ft_hr or 0.0,
            dls_deg_100ft=latest_packet.dls_deg_100ft or 0.0,
        )
    except Exception as e:
        logger.error(f"Telemetry retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve telemetry: {str(e)}")


def _calculate_data_quality(recent_telemetry) -> DataQualityResponse:
    """Compute data quality metrics from a list of telemetry ORM objects."""
    if not recent_telemetry:
        return DataQualityResponse(
            total_rows=0,
            missing_rate_by_column={},
            gaps_detected=0,
            outlier_counts={"vibration": 0, "dls": 0, "wob": 0}
        )

    total_rows = len(recent_telemetry)
    missing_rates = {}

    # Gap detection based on timestamp differences
    timestamps = sorted(packet.timestamp for packet in recent_telemetry)
    gaps = 0
    expected_interval = 30  # seconds

    for i in range(1, len(timestamps)):
        time_diff = (timestamps[i] - timestamps[i - 1]).total_seconds()
        if time_diff > expected_interval * 2:
            gaps += 1

    # Outlier detection using 3-sigma
    outlier_counts = {"vibration": 0, "dls": 0, "wob": 0}

    for field, attr in [("vibration", "vibration_g"), ("dls", "dls_deg_100ft"), ("wob", "wob_klbf")]:
        values = [getattr(p, attr) for p in recent_telemetry if getattr(p, attr) is not None]
        if values:
            mean = sum(values) / len(values)
            std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
            if std > 0:
                outlier_counts[field] = sum(1 for x in values if abs(x - mean) > 3 * std)

    return DataQualityResponse(
        total_rows=total_rows,
        missing_rate_by_column=missing_rates,
        gaps_detected=gaps,
        outlier_counts=outlier_counts,
    )


@router.get("/quality", response_model=DataQualityResponse)
async def get_data_quality_endpoint(db=Depends(get_db)):
    """Get data quality metrics from database."""
    try:
        telemetry_repo = TelemetryRepository(db)
        recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=1000)
        return _calculate_data_quality(recent_telemetry)
    except Exception as e:
        logger.error(f"Data quality calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate data quality: {str(e)}")


@router.websocket("/stream")
async def telemetry_stream(websocket: WebSocket, db=Depends(get_db)):
    """WebSocket endpoint for real-time telemetry streaming with heartbeat support."""
    await websocket.accept()
    logger.info("WebSocket connection established for telemetry streaming")

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "message": "Real-time telemetry streaming started",
            "system_mode": settings.SYSTEM_MODE,
            "telemetry_source": "Simulated telemetry" if settings.SYSTEM_MODE == "SIMULATION" else "Prototype telemetry",
        })

        telemetry_repo = TelemetryRepository(db)
        config_repo = ConfigRepository(db)
        last_telemetry_id = None
        message_count = 0

        # Heartbeat task
        async def heartbeat():
            while True:
                try:
                    await asyncio.sleep(5)
                    if websocket.client_state.value == 1:  # CONNECTED
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Heartbeat error: {e}")
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

        while True:
            try:
                recent_telemetry = telemetry_repo.get_latest_by_well("well_001", limit=1)

                if recent_telemetry:
                    latest_packet = recent_telemetry[0]

                    if last_telemetry_id != latest_packet.id:
                        last_telemetry_id = latest_packet.id

                        telemetry_data = {
                            "timestamp": latest_packet.timestamp.isoformat(),
                            "depth_ft": latest_packet.depth_ft or 0.0,
                            "wob_klbf": latest_packet.wob_klbf or 0.0,
                            "torque_kftlb": latest_packet.torque_kftlb or 0.0,
                            "rpm": latest_packet.rpm or 0.0,
                            "vibration_g": latest_packet.vibration_g or 0.0,
                            "inclination_deg": latest_packet.inclination_deg or 0.0,
                            "azimuth_deg": latest_packet.azimuth_deg or 0.0,
                            "rop_ft_hr": latest_packet.rop_ft_hr or 0.0,
                            "dls_deg_100ft": latest_packet.dls_deg_100ft or 0.0,
                        }

                        await websocket.send_json({
                            "type": "telemetry",
                            "timestamp": datetime.now().isoformat(),
                            "data": telemetry_data,
                            "telemetry_source": "simulated" if settings.SYSTEM_MODE == "SIMULATION" else "prototype",
                        })

                        # AI recommendation via shared pipeline
                        if model_loader.model_available:
                            try:
                                predict_request = PredictRequest(
                                    WOB_klbf=telemetry_data["wob_klbf"],
                                    RPM_demo=telemetry_data["rpm"],
                                    ROP_ft_hr=telemetry_data["rop_ft_hr"],
                                    Torque_kftlb=telemetry_data["torque_kftlb"],
                                    Vibration_g=telemetry_data["vibration_g"],
                                    DLS_deg_per_100ft=telemetry_data["dls_deg_100ft"],
                                    Inclination_deg=telemetry_data["inclination_deg"],
                                    Azimuth_deg=telemetry_data["azimuth_deg"],
                                    Depth_ft=telemetry_data.get("depth_ft"),
                                )

                                raw_config = config_repo.get_current_config()
                                pipeline_result = run_decision_pipeline(predict_request, raw_config)

                                await websocket.send_json({
                                    "type": "recommendation",
                                    "timestamp": datetime.now().isoformat(),
                                    "data": pipeline_result.decision_record,
                                    "system_mode": settings.SYSTEM_MODE,
                                    "actuator_status": pipeline_result.response.actuator_status,
                                })
                            except Exception as e:
                                logger.warning(f"Failed to get recommendation for streaming: {e}")

                        # Data quality every 10 messages
                        message_count += 1
                        if message_count % 10 == 0:
                            try:
                                all_recent = telemetry_repo.get_latest_by_well("well_001", limit=1000)
                                quality = _calculate_data_quality(all_recent)
                                await websocket.send_json({
                                    "type": "data_quality",
                                    "timestamp": datetime.now().isoformat(),
                                    "data": quality
                                })
                            except Exception as e:
                                logger.warning(f"Failed to get data quality for streaming: {e}")

                else:
                    await websocket.send_json({
                        "type": "no_data",
                        "timestamp": datetime.now().isoformat(),
                        "message": "No telemetry data available in database"
                    })

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
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket connection closed")
