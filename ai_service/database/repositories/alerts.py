"""
Repository for alert operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from math import ceil
from sqlalchemy import select, desc, and_, or_, func, update
from sqlalchemy.orm import Session, joinedload

from ..models import Alert, User
from ..schemas import AlertCreate, AlertUpdate, AlertQuery, PaginatedAlertResponse, AlertStatus, AlertSeverity
from .base import BaseRepository

class AlertRepository(BaseRepository[Alert]):
    """Repository for alert operations."""

    def __init__(self, session: Session):
        super().__init__(session, Alert)

    def create_alert(self, alert_data: AlertCreate) -> Alert:
        """
        Create a new alert.
        This implements the 'create alert' CRUD function.
        """
        data = alert_data.model_dump()
        return self.create(data)

    def fetch_alerts_by_severity_status(self, query: AlertQuery) -> PaginatedAlertResponse:
        """
        Fetch alerts by severity/status with pagination.
        This implements the 'fetch alerts by severity/status' CRUD function.
        """
        try:
            # Build base query with user relationships
            stmt = select(Alert).options(
                joinedload(Alert.user),
                joinedload(Alert.acknowledged_user),
                joinedload(Alert.resolved_user)
            )

            # Apply filters
            conditions = []
            if query.well_id:
                conditions.append(Alert.well_id == query.well_id)
            if query.severity:
                conditions.append(Alert.severity == query.severity)
            if query.status:
                conditions.append(Alert.status == query.status)
            if query.alert_type:
                conditions.append(Alert.alert_type == query.alert_type)
            if query.start_time:
                conditions.append(Alert.timestamp >= query.start_time)
            if query.end_time:
                conditions.append(Alert.timestamp <= query.end_time)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.execute(count_stmt).scalar() or 0

            # Apply ordering and pagination
            stmt = stmt.order_by(desc(Alert.timestamp))
            stmt = stmt.offset((query.page - 1) * query.per_page).limit(query.per_page)

            # Execute query
            result = self.session.execute(stmt)
            alerts = list(result.scalars().unique().all())

            # Calculate pagination info
            pages = ceil(total / query.per_page) if total > 0 else 1

            return PaginatedAlertResponse(
                items=alerts,
                total=total,
                page=query.page,
                per_page=query.per_page,
                pages=pages
            )
        except Exception as e:
            self.session.rollback()
            raise e

    def update_alert(self, alert_id: str, update_data: AlertUpdate) -> Optional[Alert]:
        """Update an alert's status and other fields."""
        data = update_data.model_dump(exclude_unset=True)
        return self.update(alert_id, data)

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        return self.update(alert_id, {
            'status': AlertStatus.acknowledged,
            'acknowledged_at': datetime.now(),
            'acknowledged_by': user_id
        })

    def resolve_alert(self, alert_id: str, user_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        return self.update(alert_id, {
            'status': AlertStatus.resolved,
            'resolved_at': datetime.now(),
            'resolved_by': user_id
        })

    def get_active_alerts(self, well_id: Optional[str] = None,
                         severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by well and severity."""
        try:
            stmt = (
                select(Alert)
                .options(
                    joinedload(Alert.user),
                    joinedload(Alert.acknowledged_user),
                    joinedload(Alert.resolved_user)
                )
                .where(Alert.status == AlertStatus.active)
            )

            if well_id:
                stmt = stmt.where(Alert.well_id == well_id)
            if severity:
                stmt = stmt.where(Alert.severity == severity)

            stmt = stmt.order_by(desc(Alert.timestamp))

            result = self.session.execute(stmt)
            return list(result.scalars().unique().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_alerts_by_well(self, well_id: str, limit: int = 50) -> List[Alert]:
        """Get recent alerts for a specific well."""
        try:
            stmt = (
                select(Alert)
                .options(
                    joinedload(Alert.user),
                    joinedload(Alert.acknowledged_user),
                    joinedload(Alert.resolved_user)
                )
                .where(Alert.well_id == well_id)
                .order_by(desc(Alert.timestamp))
                .limit(limit)
            )
            result = self.session.execute(stmt)
            return list(result.scalars().unique().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_critical_alerts(self, hours: int = 24) -> List[Alert]:
        """Get critical alerts from the last N hours."""
        try:
            from datetime import timedelta
            start_time = datetime.now() - timedelta(hours=hours)

            stmt = (
                select(Alert)
                .options(
                    joinedload(Alert.user),
                    joinedload(Alert.acknowledged_user),
                    joinedload(Alert.resolved_user)
                )
                .where(
                    and_(
                        Alert.severity == AlertSeverity.critical,
                        Alert.timestamp >= start_time
                    )
                )
                .order_by(desc(Alert.timestamp))
            )

            result = self.session.execute(stmt)
            return list(result.scalars().unique().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_alert_stats(self, well_id: Optional[str] = None,
                       days: int = 30) -> Dict[str, Any]:
        """Get alert statistics for analysis."""
        try:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)

            # Build base query
            stmt = select(Alert).where(Alert.timestamp >= start_date)
            if well_id:
                stmt = stmt.where(Alert.well_id == well_id)

            # Get all alerts in time range
            result = self.session.execute(stmt)
            alerts = list(result.scalars().all())

            if not alerts:
                return {
                    'total_alerts': 0,
                    'by_status': {},
                    'by_severity': {},
                    'by_type': {},
                    'acknowledgment_rate': 0.0,
                    'resolution_rate': 0.0
                }

            # Calculate statistics
            total = len(alerts)
            by_status = {}
            by_severity = {}
            by_type = {}

            acknowledged_count = 0
            resolved_count = 0

            for alert in alerts:
                # Count by status
                status = alert.status.value if hasattr(alert.status, 'value') else str(alert.status)
                by_status[status] = by_status.get(status, 0) + 1

                # Count by severity
                severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
                by_severity[severity] = by_severity.get(severity, 0) + 1

                # Count by type
                if alert.alert_type:
                    by_type[alert.alert_type] = by_type.get(alert.alert_type, 0) + 1

                # Count acknowledgments and resolutions
                if alert.acknowledged_at:
                    acknowledged_count += 1
                if alert.resolved_at:
                    resolved_count += 1

            acknowledgment_rate = (acknowledged_count / total) * 100 if total > 0 else 0
            resolution_rate = (resolved_count / total) * 100 if total > 0 else 0

            return {
                'total_alerts': total,
                'by_status': by_status,
                'by_severity': by_severity,
                'by_type': by_type,
                'acknowledgment_rate': round(acknowledgment_rate, 2),
                'resolution_rate': round(resolution_rate, 2),
                'time_range_days': days
            }
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_acknowledge_alerts(self, alert_ids: List[str], user_id: str) -> int:
        """Bulk acknowledge multiple alerts. Returns count of updated alerts."""
        try:
            now = datetime.now()
            stmt = (
                update(Alert)
                .where(
                    and_(
                        Alert.id.in_(alert_ids),
                        Alert.status == AlertStatus.active
                    )
                )
                .values(
                    status=AlertStatus.acknowledged,
                    acknowledged_at=now,
                    acknowledged_by=user_id,
                    updated_at=now
                )
            )

            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount
        except Exception as e:
            self.session.rollback()
            raise e