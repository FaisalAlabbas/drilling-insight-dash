"""
Database connection and session management using SQLAlchemy 2.0.
"""

import os
from typing import Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Database URL from environment
# Default to SQLite for development, PostgreSQL for production
import sys
_APP_ENV = os.getenv("APP_ENV", "development").lower()
_DEFAULT_DB = "sqlite:///drilling_insight.db" if _APP_ENV == "development" else "postgresql://drilling_user:drilling_password@localhost:5432/drilling_insight"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# Ensure SQLite uses sync driver for sync operations
if DATABASE_URL.startswith("sqlite+aiosqlite://"):
    SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
else:
    SYNC_DATABASE_URL = DATABASE_URL

# Convert to async URL for async operations
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Metadata for table definitions
metadata = MetaData()

# Synchronous engine and session - use sync URL for SQLite compatibility
if SYNC_DATABASE_URL.startswith("sqlite://"):
    engine = create_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    engine = create_engine(
        SYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous engine and session (only for PostgreSQL or when async needed)
if ASYNC_DATABASE_URL.startswith("postgresql+asyncpg://"):
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
else:
    # For SQLite, create a simple async wrapper if needed in the future
    async_engine = None

if async_engine:
    AsyncSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
    )
else:
    AsyncSessionLocal = None

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    Use with `Depends(get_db)` in route functions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_database():
    """Create all tables defined in models."""
    from .models import Base  # Import Base to ensure all models are registered
    Base.metadata.create_all(bind=engine)

def drop_database():
    """Drop all tables (use with caution!)."""
    from .models import Base
    Base.metadata.drop_all(bind=engine)

def reset_database():
    """Reset database by dropping and recreating all tables."""
    drop_database()
    create_database()

# Health check function
def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

# Initialize database on import
def init_db():
    """Initialize database connection and create tables if they don't exist."""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Create tables if they don't exist
        create_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise