"""
Repository for telemetry packet operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import Session

from ..models import TelemetryPacket, Well
from ..schemas import TelemetryPacketCreate, TelemetryQuery
from .base import BaseRepository

class TelemetryRepository(BaseRepository[TelemetryPacket]):
    """Repository for telemetry packet operations."""

    def __init__(self, session: Session):
        super().__init__(session, TelemetryPacket)

    def insert_telemetry_packet(self, telemetry_data: TelemetryPacketCreate) -> TelemetryPacket:
        """
        Insert a new telemetry packet.
        This implements the 'insert telemetry packet' CRUD function.
        """
        data = telemetry_data.model_dump()
        return self.create(data)

    def get_latest_by_well(self, well_id: str, limit: int = 1) -> List[TelemetryPacket]:
        """
        Fetch latest telemetry by well.
        This implements the 'fetch latest telemetry by well' CRUD function.
        """
        try:
            stmt = (
                select(TelemetryPacket)
                .where(TelemetryPacket.well_id == well_id)
                .order_by(desc(TelemetryPacket.timestamp))
                .limit(limit)
            )
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_telemetry_range(self, query: TelemetryQuery) -> List[TelemetryPacket]:
        """Get telemetry packets within a time range for a well."""
        try:
            stmt = select(TelemetryPacket).where(TelemetryPacket.well_id == query.well_id)

            if query.start_time:
                stmt = stmt.where(TelemetryPacket.timestamp >= query.start_time)
            if query.end_time:
                stmt = stmt.where(TelemetryPacket.timestamp <= query.end_time)

            stmt = stmt.order_by(desc(TelemetryPacket.timestamp)).limit(query.limit)

            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_recent_telemetry(self, well_id: str, hours: int = 24) -> List[TelemetryPacket]:
        """Get telemetry packets from the last N hours for a well."""
        start_time = datetime.now() - timedelta(hours=hours)
        return self.get_telemetry_range(
            TelemetryQuery(well_id=well_id, start_time=start_time, limit=1000)
        )

    def get_telemetry_stats(self, well_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get telemetry statistics for a well over the last N hours."""
        try:
            start_time = datetime.now() - timedelta(hours=hours)

            stmt = (
                select(
                    func.count(TelemetryPacket.id).label('count'),
                    func.avg(TelemetryPacket.wob_klbf).label('avg_wob'),
                    func.avg(TelemetryPacket.rpm).label('avg_rpm'),
                    func.avg(TelemetryPacket.rop_ft_hr).label('avg_rop'),
                    func.avg(TelemetryPacket.vibration_g).label('avg_vibration'),
                    func.min(TelemetryPacket.timestamp).label('oldest_timestamp'),
                    func.max(TelemetryPacket.timestamp).label('newest_timestamp')
                )
                .where(
                    and_(
                        TelemetryPacket.well_id == well_id,
                        TelemetryPacket.timestamp >= start_time
                    )
                )
            )

            result = self.session.execute(stmt).first()

            if result:
                return {
                    'count': result.count or 0,
                    'avg_wob_klbf': float(result.avg_wob) if result.avg_wob else None,
                    'avg_rpm': float(result.avg_rpm) if result.avg_rpm else None,
                    'avg_rop_ft_hr': float(result.avg_rop) if result.avg_rop else None,
                    'avg_vibration_g': float(result.avg_vibration) if result.avg_vibration else None,
                    'time_range': {
                        'start': result.oldest_timestamp,
                        'end': result.newest_timestamp
                    }
                }
            return {'count': 0}
        except Exception as e:
            self.session.rollback()
            raise e

    def get_wells_with_recent_data(self, hours: int = 24) -> List[str]:
        """Get list of well IDs that have telemetry data in the last N hours."""
        try:
            start_time = datetime.now() - timedelta(hours=hours)

            stmt = (
                select(TelemetryPacket.well_id.distinct())
                .where(TelemetryPacket.timestamp >= start_time)
            )

            result = self.session.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_old_telemetry(self, days_old: int = 365) -> int:
        """Delete telemetry packets older than specified days. Returns count deleted."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            from sqlalchemy import delete
            stmt = delete(TelemetryPacket).where(TelemetryPacket.timestamp < cutoff_date)

            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount
        except Exception as e:
            self.session.rollback()
            raise e