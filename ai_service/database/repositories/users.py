"""
Repository for user operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import UserCreate, UserUpdate
from .base import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            stmt = select(User).where(User.username == username)
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            stmt = select(User).where(User.email == email)
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            self.session.rollback()
            raise e

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        try:
            user = self.get_by_username(username)
            if user and user.is_active:
                # In a real implementation, you'd verify the password hash
                # For now, we'll do a simple check (demo purposes only)
                if password == user.password_hash:  # This should be hashed comparison
                    # Update last login
                    self.update(user.id, {'last_login_at': datetime.now()})
                    return user
            return None
        except Exception as e:
            self.session.rollback()
            raise e

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with password hashing."""
        try:
            data = user_data.model_dump()

            # In a real implementation, you'd hash the password
            # For demo purposes, we'll store it as-is (NEVER do this in production)
            data['password_hash'] = data.pop('password')

            return self.create(data)
        except Exception as e:
            self.session.rollback()
            raise e

    def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        data = update_data.model_dump(exclude_unset=True)

        # Handle password update
        if 'password' in data:
            # In a real implementation, you'd hash the password
            data['password_hash'] = data.pop('password')

        return self.update(user_id, data)

    def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        return self.update(user_id, {'is_active': False})

    def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account."""
        return self.update(user_id, {'is_active': True})

    def get_active_users(self) -> List[User]:
        """Get all active users."""
        try:
            stmt = select(User).where(User.is_active == True)
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role."""
        try:
            stmt = select(User).where(
                and_(
                    User.role == role,
                    User.is_active == True
                )
            )
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login timestamp."""
        return self.update(user_id, {'last_login_at': datetime.now()})

    def change_password(self, user_id: str, new_password: str) -> Optional[User]:
        """Change user's password."""
        # In a real implementation, you'd hash the password
        return self.update(user_id, {'password_hash': new_password})

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            from sqlalchemy import func

            # Get total users
            total_stmt = select(func.count(User.id))
            total_users = self.session.execute(total_stmt).scalar() or 0

            # Get active users
            active_stmt = select(func.count(User.id)).where(User.is_active == True)
            active_users = self.session.execute(active_stmt).scalar() or 0

            # Get users by role
            role_stmt = select(User.role, func.count(User.id)).group_by(User.role)
            role_result = self.session.execute(role_stmt)
            users_by_role = {row[0]: row[1] for row in role_result.all()}

            # Get recent logins (last 30 days)
            from datetime import timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_login_stmt = select(func.count(User.id)).where(
                and_(
                    User.last_login_at >= thirty_days_ago,
                    User.is_active == True
                )
            )
            recent_logins = self.session.execute(recent_login_stmt).scalar() or 0

            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'users_by_role': users_by_role,
                'recent_logins': recent_logins
            }
        except Exception as e:
            self.session.rollback()
            raise e

    def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by username or email."""
        try:
            from sqlalchemy import or_, func

            search_pattern = f"%{query}%"
            stmt = select(User).where(
                and_(
                    User.is_active == True,
                    or_(
                        func.lower(User.username).like(func.lower(search_pattern)),
                        func.lower(User.email).like(func.lower(search_pattern))
                    )
                )
            ).limit(limit)

            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_deactivate_users(self, user_ids: List[str]) -> int:
        """Bulk deactivate multiple users. Returns count of updated users."""
        try:
            stmt = (
                update(User)
                .where(User.id.in_(user_ids))
                .values(is_active=False, updated_at=datetime.now())
            )

            result = self.session.execute(stmt)
            self.session.commit()
            return result.rowcount
        except Exception as e:
            self.session.rollback()
            raise e