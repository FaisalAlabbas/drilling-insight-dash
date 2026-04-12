"""
Repository for decision operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from math import ceil
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.orm import Session, joinedload

from ..models import Decision, User
from ..schemas import DecisionCreate, DecisionUpdate, DecisionQuery, PaginatedDecisionResponse
from .base import BaseRepository

class DecisionRepository(BaseRepository[Decision]):
    """Repository for decision operations."""

    def __init__(self, session: Session):
        super().__init__(session, Decision)

    def create_decision(self, decision_data: DecisionCreate) -> Decision:
        """
        Create a new decision.
        This implements the 'create decision' CRUD function.
        """
        data = decision_data.model_dump()
        return self.create(data)

    def get_decision_history(self, query: DecisionQuery) -> PaginatedDecisionResponse:
        """
        Fetch decision history with pagination.
        This implements the 'fetch decision history with pagination' CRUD function.
        """
        try:
            # Build base query
            stmt = select(Decision).options(joinedload(Decision.user))

            # Apply filters
            conditions = []
            if query.well_id:
                conditions.append(Decision.well_id == query.well_id)
            if query.user_id:
                conditions.append(Decision.user_id == query.user_id)
            if query.execution_status:
                conditions.append(Decision.execution_status == query.execution_status)
            if query.gate_outcome:
                conditions.append(Decision.gate_outcome == query.gate_outcome)
            if query.start_time:
                conditions.append(Decision.timestamp >= query.start_time)
            if query.end_time:
                conditions.append(Decision.timestamp <= query.end_time)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = self.session.execute(count_stmt).scalar() or 0

            # Apply ordering and pagination
            stmt = stmt.order_by(desc(Decision.timestamp))
            stmt = stmt.offset((query.page - 1) * query.per_page).limit(query.per_page)

            # Execute query
            result = self.session.execute(stmt)
            decisions = list(result.scalars().unique().all())

            # Calculate pagination info
            pages = ceil(total / query.per_page) if total > 0 else 1

            return PaginatedDecisionResponse(
                items=decisions,
                total=total,
                page=query.page,
                per_page=query.per_page,
                pages=pages
            )
        except Exception as e:
            self.session.rollback()
            raise e

    def update_decision(self, decision_id: str, update_data: DecisionUpdate) -> Optional[Decision]:
        """Update a decision's execution status and other fields."""
        data = update_data.model_dump(exclude_unset=True)
        return self.update(decision_id, data)

    def get_decisions_by_well(self, well_id: str, limit: int = 50) -> List[Decision]:
        """Get recent decisions for a specific well."""
        try:
            stmt = (
                select(Decision)
                .options(joinedload(Decision.user))
                .where(Decision.well_id == well_id)
                .order_by(desc(Decision.timestamp))
                .limit(limit)
            )
            result = self.session.execute(stmt)
            return list(result.scalars().unique().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_pending_decisions(self, well_id: Optional[str] = None) -> List[Decision]:
        """Get decisions that are still pending execution."""
        try:
            stmt = (
                select(Decision)
                .options(joinedload(Decision.user))
                .where(Decision.execution_status == 'PENDING')
            )

            if well_id:
                stmt = stmt.where(Decision.well_id == well_id)

            stmt = stmt.order_by(desc(Decision.timestamp))

            result = self.session.execute(stmt)
            return list(result.scalars().unique().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_decision_stats(self, well_id: Optional[str] = None,
                          days: int = 30) -> Dict[str, Any]:
        """Get decision statistics for analysis."""
        try:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)

            # Build base query
            stmt = select(Decision).where(Decision.timestamp >= start_date)
            if well_id:
                stmt = stmt.where(Decision.well_id == well_id)

            # Get all decisions in time range
            result = self.session.execute(stmt)
            decisions = list(result.scalars().all())

            if not decisions:
                return {
                    'total_decisions': 0,
                    'by_status': {},
                    'by_outcome': {},
                    'avg_confidence': None
                }

            # Calculate statistics
            total = len(decisions)
            by_status = {}
            by_outcome = {}
            confidences = []

            for decision in decisions:
                # Count by status
                status = decision.execution_status.value if hasattr(decision.execution_status, 'value') else str(decision.execution_status)
                by_status[status] = by_status.get(status, 0) + 1

                # Count by outcome
                if decision.gate_outcome:
                    outcome = decision.gate_outcome.value if hasattr(decision.gate_outcome, 'value') else str(decision.gate_outcome)
                    by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

                # Collect confidence scores
                if decision.confidence_score is not None:
                    confidences.append(decision.confidence_score)

            avg_confidence = sum(confidences) / len(confidences) if confidences else None

            return {
                'total_decisions': total,
                'by_status': by_status,
                'by_outcome': by_outcome,
                'avg_confidence': avg_confidence,
                'time_range_days': days
            }
        except Exception as e:
            self.session.rollback()
            raise e

    def mark_decision_executed(self, decision_id: str, success: bool = True) -> Optional[Decision]:
        """Mark a decision as executed (sent or failed)."""
        status = 'SENT' if success else 'FAILED'
        return self.update(decision_id, {'execution_status': status})