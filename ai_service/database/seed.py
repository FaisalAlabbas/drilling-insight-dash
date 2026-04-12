"""
Database seeding script for Drilling Insight Dashboard.
Populates the database with initial data for development and testing.
"""

import os
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from .db import get_session
from .models import User, Well, SystemConfig, ModelVersion
from .schemas import UserRole, ModelStatus

def seed_users(session: Session) -> None:
    """Seed initial users."""
    users_data = [
        {
            "id": "user_admin_001",
            "username": "admin",
            "email": "admin@drillinginsight.com",
            "password_hash": "admin123",  # In production, this would be hashed
            "role": UserRole.ADMIN,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": "user_engineer_001",
            "username": "engineer1",
            "email": "engineer1@drillinginsight.com",
            "password_hash": "engineer123",
            "role": UserRole.ENGINEER,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": "user_operator_001",
            "username": "operator1",
            "email": "operator1@drillinginsight.com",
            "password_hash": "operator123",
            "role": UserRole.OPERATOR,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    for user_data in users_data:
        # Check if user already exists
        existing = session.query(User).filter_by(username=user_data["username"]).first()
        if not existing:
            user = User(**user_data)
            session.add(user)
            print(f"✓ Created user: {user_data['username']}")

    session.commit()

def seed_wells(session: Session) -> None:
    """Seed initial wells."""
    wells_data = [
        {
            "id": "well_001",
            "name": "Well Alpha-1",
            "location": "North Sea Platform A",
            "operator": "DrillingCorp Ltd",
            "status": "active",
            "depth_target": 2500.0,
            "current_depth": 1850.5,
            "drilling_rig": "Rig-Alpha",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": "well_002",
            "name": "Well Beta-2",
            "location": "Gulf of Mexico Platform B",
            "operator": "DeepDrill Inc",
            "status": "active",
            "depth_target": 3200.0,
            "current_depth": 2100.2,
            "drilling_rig": "Rig-Beta",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": "well_003",
            "name": "Well Gamma-3",
            "location": "Arctic Region Platform C",
            "operator": "ArcticDrilling LLC",
            "status": "planned",
            "depth_target": 2800.0,
            "current_depth": 0.0,
            "drilling_rig": "Rig-Gamma",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    for well_data in wells_data:
        # Check if well already exists
        existing = session.query(Well).filter_by(id=well_data["id"]).first()
        if not existing:
            well = Well(**well_data)
            session.add(well)
            print(f"✓ Created well: {well_data['name']}")

    session.commit()

def seed_system_config(session: Session) -> None:
    """Seed initial system configuration."""
    config_data = [
        {
            "key": "telemetry_collection_interval",
            "value": "30",
            "description": "Telemetry data collection interval in seconds",
            "data_type": "integer",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "key": "alert_threshold_high",
            "value": "85.0",
            "description": "High alert threshold percentage",
            "data_type": "float",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "key": "alert_threshold_critical",
            "value": "95.0",
            "description": "Critical alert threshold percentage",
            "data_type": "float",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "key": "max_decisions_per_hour",
            "value": "10",
            "description": "Maximum AI decisions allowed per hour",
            "data_type": "integer",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "key": "data_retention_days",
            "value": "90",
            "description": "Number of days to retain telemetry data",
            "data_type": "integer",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "key": "maintenance_mode",
            "value": "false",
            "description": "System maintenance mode flag",
            "data_type": "boolean",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    for config_item in config_data:
        # Check if config already exists
        existing = session.query(SystemConfig).filter_by(key=config_item["key"]).first()
        if not existing:
            config = SystemConfig(**config_item)
            session.add(config)
            print(f"✓ Created config: {config_item['key']}")

    session.commit()

def seed_model_versions(session: Session) -> None:
    """Seed initial AI model versions."""
    models_data = [
        {
            "id": "model_v1_0_0",
            "version": "1.0.0",
            "model_type": "drilling_optimization",
            "status": ModelStatus.ACTIVE,
            "accuracy_score": 0.92,
            "description": "Initial drilling optimization model",
            "parameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 100,
                "features": ["depth", "pressure", "temperature", "vibration"]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": "model_v1_1_0",
            "version": "1.1.0",
            "model_type": "anomaly_detection",
            "status": ModelStatus.TRAINING,
            "accuracy_score": 0.88,
            "description": "Anomaly detection model for equipment failure prediction",
            "parameters": {
                "algorithm": "isolation_forest",
                "contamination": 0.1,
                "n_estimators": 100,
                "features": ["vibration", "pressure", "flow_rate", "power_consumption"]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    for model_data in models_data:
        # Check if model already exists
        existing = session.query(ModelVersion).filter_by(id=model_data["id"]).first()
        if not existing:
            model = ModelVersion(**model_data)
            session.add(model)
            print(f"✓ Created model: {model_data['version']} ({model_data['model_type']})")

    session.commit()

def seed_database() -> None:
    """Main seeding function."""
    print("🌱 Starting database seeding...")

    with get_session() as session:
        try:
            print("\n👥 Seeding users...")
            seed_users(session)

            print("\n🏭 Seeding wells...")
            seed_wells(session)

            print("\n⚙️  Seeding system configuration...")
            seed_system_config(session)

            print("\n🤖 Seeding AI model versions...")
            seed_model_versions(session)

            print("\n✅ Database seeding completed successfully!")

        except Exception as e:
            session.rollback()
            print(f"❌ Error during seeding: {e}")
            raise
        finally:
            session.close()

if __name__ == "__main__":
    seed_database()