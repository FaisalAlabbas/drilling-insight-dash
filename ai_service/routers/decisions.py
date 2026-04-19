"""Decision statistics routes."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from database.db import get_db
from database.repositories import DecisionRepository
from actuator import virtual_actuator
from settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["Decisions"])


@router.get("/stats")
async def decision_stats(days: int = 30, db=Depends(get_db)):
    """Return aggregated decision statistics for the verification page."""
    try:
        repo = DecisionRepository(db)
        stats = repo.get_decision_stats(days=days)

        # Add actuator outcome aggregation from recent decisions
        decisions = repo.get_all(limit=stats.get("total_decisions", 0) or 500)
        actuator_counts: Dict[str, int] = {}
        anomaly_count = 0
        envelope_violations = 0

        for d in decisions:
            if d.actuator_outcome:
                actuator_counts[d.actuator_outcome] = actuator_counts.get(d.actuator_outcome, 0) + 1
            outcome_val = d.gate_outcome.value if hasattr(d.gate_outcome, "value") else str(d.gate_outcome) if d.gate_outcome else None
            if outcome_val == "REJECTED":
                anomaly_count += 1
            if hasattr(d, "pete_violations") and d.pete_violations:
                envelope_violations += 1

        stats["actuator_counts"] = actuator_counts
        stats["anomaly_count"] = anomaly_count
        stats["envelope_violations"] = envelope_violations
        stats["system_mode"] = settings.SYSTEM_MODE
        stats["actuator_state"] = virtual_actuator.get_status()

        return stats
    except Exception as e:
        logger.error(f"Failed to get decision stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve decision statistics")
