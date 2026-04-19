"""
Authentication and authorization helpers.
JWT token creation/validation, password hashing, role-based access control.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from settings import settings
from database.db import get_db
from database.repositories import UserRepository
from schemas import User, TokenData

logger = logging.getLogger(__name__)

# ── Constants ──

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ──

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


# ── User lookup ──

def get_user(username: str, db):
    """Get user from database."""
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(username)
        if user and user.is_active:
            return User(
                username=user.username,
                role=user.role.value,
                disabled=not user.is_active
            )
        return None
    except Exception as e:
        logger.error(f"Database error getting user {username}: {e}")
        return None

def authenticate_user(username: str, password: str, db):
    """Authenticate a user."""
    try:
        user_repo = UserRepository(db)
        user = user_repo.authenticate_user(username, password)
        if user:
            return User(
                username=user.username,
                role=user.role.value,
                disabled=not user.is_active
            )
        return None
    except Exception as e:
        logger.error(f"Authentication error for {username}: {e}")
        return None


# ── JWT ──

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ── FastAPI dependencies ──

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
):
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Dependency factory to require a minimum role level."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        role_hierarchy = {"operator": 1, "engineer": 2, "admin": 3}
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}, Current: {current_user.role}"
            )
        return current_user
    return role_checker
