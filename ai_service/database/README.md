# Drilling Insight Dashboard - Database Layer

A comprehensive database layer for the Drilling Insight Dashboard built with SQLAlchemy 2.0, FastAPI, and PostgreSQL.

## Overview

This database layer provides:

- **SQLAlchemy 2.0 ORM models** with proper relationships and constraints
- **Pydantic schemas** for API request/response validation
- **Repository pattern** for clean data access layer
- **Alembic migrations** for database schema versioning
- **Async database operations** with connection pooling
- **Comprehensive error handling** and logging

## Architecture

```
database/
├── __init__.py          # Package exports
├── db.py                # Database connection and session management
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic validation schemas
├── init_db.py           # Database initialization script
├── migrate.py           # Migration and seeding script
├── seed.py              # Database seeding with initial data
├── test_db.py           # Database layer tests
├── alembic/             # Alembic migration files
│   ├── env.py
│   └── versions/
└── repositories/        # Repository pattern implementation
    ├── __init__.py
    ├── base.py          # Base repository with common CRUD
    ├── users.py         # User management operations
    ├── telemetry.py     # Telemetry data operations
    ├── decisions.py     # AI decision operations
    ├── alerts.py        # Alert management operations
    └── config.py        # System configuration operations
```

## Quick Start

### 1. Environment Setup

Set your database connection string:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/drilling_insight"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# Create tables and initial structure
python database/init_db.py

# Run migrations and seed data
python database/migrate.py
```

### 4. Run Tests

```bash
# Test without database connection (imports only)
python database/test_db.py

# Test with database connection (full CRUD)
DATABASE_URL="postgresql://..." python database/test_db.py
```

## Models

### Core Entities

- **User**: System users with role-based access
- **Well**: Drilling well information and status
- **TelemetryPacket**: Real-time sensor data from wells
- **Decision**: AI-generated drilling recommendations
- **Alert**: System alerts and notifications
- **ModelVersion**: AI model versions and metadata
- **SystemConfig**: System configuration settings
- **AuditLog**: Audit trail for configuration changes

### Relationships

```
User (1) ──── (N) Well
Well (1) ──── (N) TelemetryPacket
Well (1) ──── (N) Decision
Well (1) ──── (N) Alert
User (1) ──── (N) Decision
User (1) ──── (N) AuditLog
```

## Repositories

Each repository provides typed CRUD operations with proper error handling:

### UserRepository

```python
from database.repositories import UserRepository

# Authenticate user
user = repo.authenticate_user("username", "password")

# Create new user
user_data = UserCreate(username="newuser", email="user@example.com", ...)
user = repo.create_user(user_data)

# Get user statistics
stats = repo.get_user_stats()
```

### TelemetryRepository

```python
from database.repositories import TelemetryRepository

# Insert telemetry packet
packet = repo.insert_telemetry_packet(packet_data)

# Get latest telemetry by well
telemetry = repo.get_latest_by_well("well_001", limit=100)
```

### DecisionRepository

```python
from database.repositories import DecisionRepository

# Create decision
decision = repo.create_decision(decision_data)

# Get decision history with pagination
decisions = repo.get_decision_history(
    well_id="well_001",
    page=1,
    per_page=20,
    status="approved"
)
```

### AlertRepository

```python
from database.repositories import AlertRepository

# Create alert
alert = repo.create_alert(alert_data)

# Fetch alerts by severity and status
alerts = repo.fetch_alerts_by_severity_status(
    severity="critical",
    status="active",
    limit=50
)
```

### ConfigRepository

```python
from database.repositories import ConfigRepository

# Get current configuration
config = repo.get_current_config()

# Update configuration with audit
updated = repo.update_config_with_audit(
    key="alert_threshold_high",
    value="90.0",
    user_id="user_001",
    reason="Performance optimization"
)
```

## Database Operations

### Session Management

```python
from database.db import get_session, get_db

# For repository operations
with get_session() as session:
    repo = UserRepository(session)
    user = repo.get_by_username("admin")

# For FastAPI dependency injection
@app.get("/users/{user_id}")
def get_user(user_id: str, db = Depends(get_db)):
    repo = UserRepository(db)
    return repo.get_by_id(user_id)
```

### Async Operations

```python
from database.db import get_async_session

async with get_async_session() as session:
    # Async database operations
    result = await session.execute(query)
```

## Migrations

### Creating New Migrations

```bash
# Generate migration from model changes
cd database
alembic revision --autogenerate -m "Add new field to telemetry"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Manual Migration

```python
# database/alembic/versions/xxx_add_new_field.py
def upgrade():
    op.add_column('telemetry_packets',
                  sa.Column('new_field', sa.String(100)))

def downgrade():
    op.drop_column('telemetry_packets', 'new_field')
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 20)
- `DB_POOL_RECYCLE`: Connection recycle time in seconds (default: 3600)

### Connection String Format

```
postgresql://username:password@host:port/database
postgresql://username:password@host:port/database?sslmode=require
```

## Error Handling

All repository methods include comprehensive error handling:

```python
try:
    user = repo.create_user(user_data)
except IntegrityError:
    # Handle unique constraint violations
except ValidationError:
    # Handle schema validation errors
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Database error: {e}")
```

## Performance Considerations

### Indexing Strategy

- Primary keys on all tables
- Foreign key indexes for relationships
- Composite indexes for common query patterns
- Time-based indexes for telemetry data
- Partial indexes for active records

### Query Optimization

- Use `selectinload` for N+1 query prevention
- Implement pagination for large result sets
- Use database-level filtering when possible
- Monitor query performance with SQLAlchemy logging

### Connection Pooling

- Configurable pool size and overflow
- Connection recycling to prevent stale connections
- Proper session cleanup in FastAPI dependencies

## Testing

### Unit Tests

```python
import pytest
from database.repositories import UserRepository
from database.db import get_session

def test_user_creation():
    with get_session() as session:
        repo = UserRepository(session)
        user_data = UserCreate(...)
        user = repo.create_user(user_data)
        assert user.username == "testuser"
```

### Integration Tests

```python
def test_full_workflow():
    # Test complete user registration and login flow
    # Test telemetry insertion and retrieval
    # Test decision creation and history
```

## Security

### Password Handling

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("password")

# Verify password
valid = pwd_context.verify("password", hashed)
```

### SQL Injection Prevention

All queries use parameterized statements through SQLAlchemy ORM, preventing SQL injection attacks.

### Audit Logging

Configuration changes are automatically logged with user context and timestamps.

## Monitoring

### Health Checks

```python
from database.db import check_database_connection

if check_database_connection():
    print("Database is healthy")
else:
    print("Database connection failed")
```

### Metrics

Monitor query performance, connection pool usage, and error rates using your preferred monitoring solution.

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check PostgreSQL is running and credentials are correct
2. **Table Doesn't Exist**: Run `python database/init_db.py` to create tables
3. **Migration Errors**: Check Alembic migration files and database state
4. **Import Errors**: Ensure all dependencies are installed

### Debug Mode

Enable SQLAlchemy query logging:

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Contributing

1. Follow the repository pattern for new entities
2. Add comprehensive tests for new functionality
3. Update this README for API changes
4. Use type hints and proper error handling
5. Run tests before committing changes

## License

This database layer is part of the Drilling Insight Dashboard project.
