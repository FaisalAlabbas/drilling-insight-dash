"""
Base repository class with common database operations.
"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError

from ..models import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: Session, model_class: Type[ModelType]):
        self.session = session
        self.model_class = model_class

    def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get entity by ID."""
        try:
            stmt = select(self.model_class).where(self.model_class.id == id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all entities with pagination."""
        try:
            stmt = select(self.model_class).offset(skip).limit(limit)
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def create(self, data: Dict[str, Any]) -> ModelType:
        """Create a new entity."""
        try:
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid4())

            entity = self.model_class(**data)
            self.session.add(entity)
            self.session.flush()  # Flush to get the ID
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """Update an entity by ID."""
        try:
            stmt = (
                update(self.model_class)
                .where(self.model_class.id == id)
                .values(**data)
                .returning(self.model_class)
            )
            result = self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            if entity:
                self.session.flush()
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        try:
            stmt = delete(self.model_class).where(self.model_class.id == id)
            result = self.session.execute(stmt)
            return result.rowcount > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def exists(self, id: str) -> bool:
        """Check if entity exists by ID."""
        try:
            stmt = select(self.model_class.id).where(self.model_class.id == id)
            result = self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        try:
            stmt = select(self.model_class)
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        conditions.append(getattr(self.model_class, key) == value)
                if conditions:
                    stmt = stmt.where(and_(*conditions))

            result = self.session.execute(stmt)
            return len(result.scalars().all())
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def filter_by(self, filters: Dict[str, Any], order_by: Optional[str] = None,
                  descending: bool = False, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Filter entities with optional ordering and pagination."""
        try:
            stmt = select(self.model_class)

            # Apply filters
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    conditions.append(getattr(self.model_class, key) == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                column = getattr(self.model_class, order_by)
                if descending:
                    stmt = stmt.order_by(desc(column))
                else:
                    stmt = stmt.order_by(column)

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)

            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e