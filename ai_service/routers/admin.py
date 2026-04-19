"""Admin routes — user CRUD, config CRUD, alerts, audit logs."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from database.db import get_db
from database.repositories import UserRepository, ConfigRepository, AlertRepository
from auth import require_role
from schemas import User, CreateUserRequest, UpdateUserRequest, UpdateConfigRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── User Management (admin only) ─────────────────────────────────

@router.get("/users")
async def admin_list_users(current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """List all users."""
    user_repo = UserRepository(db)
    users = user_repo.get_all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.get("/users/stats")
async def admin_user_stats(current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Get user statistics."""
    user_repo = UserRepository(db)
    return user_repo.get_user_stats()


@router.post("/users", status_code=201)
async def admin_create_user(req: CreateUserRequest, current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Create a new user."""
    from database.schemas import UserCreate, UserRole as SchemaUserRole
    user_repo = UserRepository(db)

    existing = user_repo.get_by_username(req.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user_data = UserCreate(
        username=req.username,
        email=req.email,
        password=req.password,
        role=SchemaUserRole(req.role),
    )
    new_user = user_repo.create_user(user_data)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role),
        "is_active": new_user.is_active,
    }


@router.put("/users/{user_id}")
async def admin_update_user(user_id: str, req: UpdateUserRequest, current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Update a user's role, email, status, or password."""
    from database.schemas import UserUpdate as SchemaUserUpdate, UserRole as SchemaUserRole
    user_repo = UserRepository(db)

    update_data = {}
    if req.email is not None:
        update_data["email"] = req.email
    if req.role is not None:
        update_data["role"] = SchemaUserRole(req.role)
    if req.is_active is not None:
        update_data["is_active"] = req.is_active
    if req.password is not None:
        update_data["password"] = req.password

    schema = SchemaUserUpdate(**update_data)
    updated = user_repo.update_user(user_id, schema)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": updated.id,
        "username": updated.username,
        "email": updated.email,
        "role": updated.role.value if hasattr(updated.role, 'value') else str(updated.role),
        "is_active": updated.is_active,
    }


@router.delete("/users/{user_id}")
async def admin_deactivate_user(user_id: str, current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Deactivate a user."""
    user_repo = UserRepository(db)
    result = user_repo.deactivate_user(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated", "id": user_id}


# ─── System Config (admin only) ───────────────────────────────────

@router.get("/config")
async def admin_get_config(current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Get all system configuration entries."""
    config_repo = ConfigRepository(db)
    configs = config_repo.get_all_configs()
    return [
        {
            "id": c.id,
            "key": c.key,
            "value": c.value,
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]


@router.put("/config/{key}")
async def admin_update_config(key: str, req: UpdateConfigRequest, current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Update a configuration value with audit logging."""
    config_repo = ConfigRepository(db)
    updated = config_repo.update_config_with_audit(
        key=key,
        new_value=req.value,
        user_id=current_user.username,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Config key not found")
    return {
        "key": updated.key,
        "value": updated.value,
        "description": updated.description,
    }


@router.get("/config/history/{key}")
async def admin_config_history(key: str, current_user: User = Depends(require_role("admin")), db=Depends(get_db)):
    """Get audit history for a configuration key."""
    config_repo = ConfigRepository(db)
    logs = config_repo.get_config_history(key)
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "user_id": log.user_id,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
        }
        for log in logs
    ]


# ─── Alert Management (engineer+) ─────────────────────────────────

@router.get("/alerts")
async def admin_list_alerts(
    severity: Optional[str] = None,
    alert_status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    current_user: User = Depends(require_role("engineer")),
    db=Depends(get_db),
):
    """List alerts with optional severity/status filters."""
    from database.schemas import AlertQuery, AlertSeverity as SchemaSeverity, AlertStatus as SchemaStatus
    alert_repo = AlertRepository(db)

    query = AlertQuery(
        severity=SchemaSeverity(severity) if severity else None,
        status=SchemaStatus(alert_status) if alert_status else None,
        page=page,
        per_page=per_page,
    )
    result = alert_repo.fetch_alerts_by_severity_status(query)

    items = []
    for a in result.items:
        items.append({
            "id": a.id,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "severity": a.severity.value if hasattr(a.severity, 'value') else str(a.severity),
            "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
            "title": a.title,
            "message": a.message,
            "well_id": a.well_id,
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        })

    return {"items": items, "total": result.total, "page": result.page, "pages": result.pages}


@router.put("/alerts/{alert_id}/acknowledge")
async def admin_acknowledge_alert(alert_id: str, current_user: User = Depends(require_role("engineer")), db=Depends(get_db)):
    """Acknowledge an alert."""
    alert_repo = AlertRepository(db)
    result = alert_repo.acknowledge_alert(alert_id, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged", "id": alert_id}


@router.put("/alerts/{alert_id}/resolve")
async def admin_resolve_alert(alert_id: str, current_user: User = Depends(require_role("engineer")), db=Depends(get_db)):
    """Resolve an alert."""
    alert_repo = AlertRepository(db)
    result = alert_repo.resolve_alert(alert_id, current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved", "id": alert_id}


@router.get("/alerts/stats")
async def admin_alert_stats(current_user: User = Depends(require_role("engineer")), db=Depends(get_db)):
    """Get alert statistics."""
    alert_repo = AlertRepository(db)
    return alert_repo.get_alert_stats()


# ─── Audit Logs (admin only) ──────────────────────────────────────

@router.get("/audit-logs")
async def admin_audit_logs(
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db=Depends(get_db),
):
    """Get recent audit log entries."""
    from database.models import AuditLog
    from sqlalchemy import select, desc

    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    result = db.execute(stmt)
    logs = list(result.scalars().all())

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "old_values": log.old_values,
            "new_values": log.new_values,
        }
        for log in logs
    ]
