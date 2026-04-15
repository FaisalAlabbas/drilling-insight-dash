# Drilling Insight Dashboard - Database Schema

This directory contains PostgreSQL database migrations and seed data for the Drilling Insight Dashboard project.

## Files

- `001_init.sql` - Complete database schema with tables, indexes, constraints, and initial configuration
- `002_seed_demo.sql` - Demo data for testing and development

## Database Schema Overview

### Core Entities

#### Users

- User management with role-based access control
- Roles: `operator`, `engineer`, `admin`
- Authentication and session tracking

#### Wells

- Well information and metadata
- Drilling progress tracking
- Location and operational data

#### Telemetry Packets (Time-Series)

- Real-time drilling telemetry data
- Partitioned by month for performance
- Optimized for time-range queries

#### Decisions

- AI-powered steering recommendations
- Decision execution tracking
- Feature summaries and confidence scores

#### Alerts

- System alerts and notifications
- Severity levels and status tracking
- Acknowledgment and resolution workflow

#### Model Versions

- ML model version management
- Performance metrics and schemas
- Model activation/deactivation

#### System Config

- Application configuration storage
- JSON-based flexible configuration
- Encrypted sensitive values support

#### Audit Logs

- Complete audit trail
- User actions and system events
- Security and compliance tracking

### Performance Optimizations

#### Time-Series Optimization

- `telemetry_packets` table partitioned by month
- Composite indexes on `(well_id, timestamp)`
- Efficient data retention policies

#### Query Optimization

- Strategic indexes for common query patterns
- GIN indexes for JSONB fields
- Foreign key constraints with appropriate cascade rules

#### Data Types

- UUID primary keys for scalability
- JSONB for flexible data storage
- Appropriate numeric precision for measurements
- Enum types for data integrity

## Setup Instructions

### Prerequisites

- PostgreSQL 13+ with uuid-ossp and pg_trgm extensions
- Database user with schema creation privileges

### Running Migrations

1. Create a new database:

```sql
CREATE DATABASE drilling_insight;
```

2. Connect to the database and run the migrations:

```bash
psql -d drilling_insight -f database/migrations/001_init.sql
psql -d drilling_insight -f database/migrations/002_seed_demo.sql
```

### Environment Variables

Set the following environment variables for the application:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/drilling_insight
```

## Demo Data

The seed file includes:

- **3 Users**: operator, engineer, admin (password: same as username)
- **3 Wells**: Active and completed wells with realistic data
- **10 Telemetry Records**: Recent drilling data for Well-A1
- **3 Decisions**: AI recommendations with different outcomes
- **3 Alerts**: Various severity levels and statuses
- **2 Model Versions**: Current and previous ML models
- **System Configuration**: Default settings and thresholds
- **Audit Logs**: Sample user actions

## Maintenance

### Data Retention

- Telemetry data: 365 days (configurable)
- Alert history: 90 days (configurable)
- Automatic cleanup functions provided

### Partition Management

- Monthly partitions for telemetry data
- Automatic partition creation recommended for production
- Archive old partitions as needed

### Backup Strategy

- Regular database backups
- Point-in-time recovery capability
- Test restore procedures

## Security Considerations

- Password hashing required (demo uses bcrypt placeholders)
- Row-level security policies can be added for multi-tenant scenarios
- Audit logging enabled for compliance
- Sensitive configuration values can be encrypted

## Performance Monitoring

Key metrics to monitor:

- Query performance on telemetry_packets
- Index usage and maintenance
- Partition growth and cleanup
- Connection pooling efficiency

## Migration Notes

- Schema designed for horizontal scaling
- JSONB fields allow for schema evolution
- Enum types ensure data consistency
- UUID keys prevent collision in distributed systems
