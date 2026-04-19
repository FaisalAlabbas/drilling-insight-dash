"""Actuator management routes."""

import logging

from fastapi import APIRouter, Depends

from actuator import virtual_actuator
from schemas import FaultRequest, User
from auth import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actuator", tags=["Actuator"])


@router.get("/status")
async def actuator_status():
    """Return current virtual actuator state."""
    return virtual_actuator.get_status()


@router.post("/fault")
async def actuator_fault(request: FaultRequest, user: User = Depends(require_role("admin"))):
    """Inject a fault into the virtual actuator (admin only)."""
    virtual_actuator.enter_fault(request.reason)
    logger.warning(f"Actuator fault injected by {user.username}: {request.reason}")
    return {"status": "fault_injected", "reason": request.reason, **virtual_actuator.get_status()}


@router.post("/clear")
async def actuator_clear(user: User = Depends(require_role("operator"))):
    """Clear actuator fault or manual override (operator+)."""
    virtual_actuator.clear_fault()
    virtual_actuator.clear_manual()
    logger.info(f"Actuator fault/manual cleared by {user.username}")
    return {"status": "cleared", **virtual_actuator.get_status()}


@router.post("/manual")
async def actuator_manual(user: User = Depends(require_role("operator"))):
    """Enter manual override mode (operator+). Suspends automatic commands."""
    virtual_actuator.enter_manual()
    logger.info(f"Actuator manual override activated by {user.username}")
    return {"status": "manual_override", **virtual_actuator.get_status()}
