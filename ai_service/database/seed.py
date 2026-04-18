"""
Database seeding script for Drilling Insight Dashboard.
Populates the database with initial data for development and testing.
"""

import os
import random
import math
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .db import get_session
from .models import (
    User, Well, SystemConfig, ModelVersion, UserRole,
    TelemetryPacket, Decision, Alert,
    AlertSeverity, AlertStatus, GateOutcome, ExecutionStatus,
)

# Password hashing (must match api.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_users(session: Session) -> None:
    """Seed initial users."""
    users_data = [
        {
            "id": "user_admin_001",
            "username": "admin",
            "email": "admin@drillinginsight.com",
            "password_hash": pwd_context.hash("admin123"),
            "role": UserRole.admin,
            "is_active": True,
        },
        {
            "id": "user_engineer_001",
            "username": "engineer1",
            "email": "engineer1@drillinginsight.com",
            "password_hash": pwd_context.hash("engineer123"),
            "role": UserRole.engineer,
            "is_active": True,
        },
        {
            "id": "user_operator_001",
            "username": "operator1",
            "email": "operator1@drillinginsight.com",
            "password_hash": pwd_context.hash("operator123"),
            "role": UserRole.operator,
            "is_active": True,
        },
    ]

    for user_data in users_data:
        existing = session.query(User).filter_by(username=user_data["username"]).first()
        if not existing:
            user = User(**user_data)
            session.add(user)
            print(f"  Created user: {user_data['username']}")
        else:
            # Update password hash if user already exists (fix plain-text passwords)
            existing.password_hash = user_data["password_hash"]
            existing.role = user_data["role"]
            print(f"  Updated user: {user_data['username']}")

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
            "total_depth_ft": 2500.0,
            "current_depth_ft": 1850.5,
        },
        {
            "id": "well_002",
            "name": "Well Beta-2",
            "location": "Gulf of Mexico Platform B",
            "operator": "DeepDrill Inc",
            "status": "active",
            "total_depth_ft": 3200.0,
            "current_depth_ft": 2100.2,
        },
        {
            "id": "well_003",
            "name": "Well Gamma-3",
            "location": "Arctic Region Platform C",
            "operator": "ArcticDrilling LLC",
            "status": "planned",
            "total_depth_ft": 2800.0,
            "current_depth_ft": 0.0,
        },
    ]

    for well_data in wells_data:
        existing = session.query(Well).filter_by(id=well_data["id"]).first()
        if not existing:
            well = Well(**well_data)
            session.add(well)
            print(f"  Created well: {well_data['name']}")

    session.commit()


def seed_system_config(session: Session) -> None:
    """Seed initial system configuration."""
    config_data = [
        {
            "id": "config_001",
            "key": "telemetry_collection_interval",
            "value": {"value": 30},
            "description": "Telemetry data collection interval in seconds",
        },
        {
            "id": "config_002",
            "key": "alert_threshold_high",
            "value": {"value": 85.0},
            "description": "High alert threshold percentage",
        },
        {
            "id": "config_003",
            "key": "alert_threshold_critical",
            "value": {"value": 95.0},
            "description": "Critical alert threshold percentage",
        },
        {
            "id": "config_004",
            "key": "max_decisions_per_hour",
            "value": {"value": 10},
            "description": "Maximum AI decisions allowed per hour",
        },
        {
            "id": "config_005",
            "key": "data_retention_days",
            "value": {"value": 90},
            "description": "Number of days to retain telemetry data",
        },
        {
            "id": "config_006",
            "key": "maintenance_mode",
            "value": {"value": False},
            "description": "System maintenance mode flag",
        },
        {
            "id": "config_007",
            "key": "max_vibration_g",
            "value": {"value": 0.5},
            "description": "Maximum vibration threshold (g)",
        },
        {
            "id": "config_008",
            "key": "max_dls_deg_100ft",
            "value": {"value": 3.0},
            "description": "Maximum dogleg severity (deg/100ft)",
        },
    ]

    for config_item in config_data:
        existing = session.query(SystemConfig).filter_by(key=config_item["key"]).first()
        if not existing:
            config = SystemConfig(**config_item)
            session.add(config)
            print(f"  Created config: {config_item['key']}")

    session.commit()


def seed_model_versions(session: Session) -> None:
    """Seed initial AI model versions."""
    models_data = [
        {
            "id": "model_v1_0_0",
            "version": "1.0.0",
            "model_type": "drilling_optimization",
            "algorithm": "GradientBoosting",
            "training_date": datetime.now() - timedelta(days=7),
            "accuracy": 0.88,
            "precision": 0.86,
            "recall": 0.87,
            "f1_score": 0.86,
            "metrics": {"train_accuracy": 0.95, "test_accuracy": 0.88},
            "is_active": True,
        },
    ]

    for model_data in models_data:
        existing = session.query(ModelVersion).filter_by(id=model_data["id"]).first()
        if not existing:
            model = ModelVersion(**model_data)
            session.add(model)
            print(f"  Created model: {model_data['version']} ({model_data['model_type']})")

    session.commit()


def seed_telemetry(session: Session) -> None:
    """Seed telemetry data for the last 6 hours."""
    # Check if telemetry already exists
    existing = session.query(TelemetryPacket).first()
    if existing:
        print("  Telemetry data already exists, skipping")
        return

    now = datetime.now(timezone.utc)
    wells = ["well_001", "well_002"]
    count = 0

    for well_id in wells:
        # Generate data every 10 seconds for the last 6 hours (2160 records per well)
        base_depth = 1850.0 if well_id == "well_001" else 2100.0
        for i in range(2160):
            ts = now - timedelta(seconds=(2160 - i) * 10)
            t = i / 2160  # normalized time 0..1

            # Realistic drilling parameter variation with some noise
            depth = base_depth + t * 50  # slowly drilling deeper
            wob = 35.0 + 10 * math.sin(t * 6.28) + random.gauss(0, 2)
            rpm_val = 120 + 30 * math.sin(t * 3.14 + 1) + random.gauss(0, 5)
            rop = 45.0 + 15 * math.sin(t * 9.42) + random.gauss(0, 3)
            torque = 15.0 + 5 * math.sin(t * 4.71 + 2) + random.gauss(0, 1)
            vibration = 0.15 + 0.1 * abs(math.sin(t * 12.56)) + random.gauss(0, 0.02)
            dls = 1.5 + 0.5 * math.sin(t * 6.28 + 3) + random.gauss(0, 0.1)
            inclination = 15.0 + 5 * math.sin(t * 3.14) + random.gauss(0, 0.5)
            azimuth = 135.0 + 10 * math.sin(t * 1.57) + random.gauss(0, 1)
            temp = 65.0 + 15 * t + random.gauss(0, 1)
            pressure = 3500 + 500 * t + random.gauss(0, 20)
            mud_flow = 650 + 50 * math.sin(t * 6.28) + random.gauss(0, 10)

            packet = TelemetryPacket(
                id=f"tel_{well_id}_{i:05d}",
                well_id=well_id,
                timestamp=ts,
                wob_klbf=round(max(0, wob), 2),
                rpm=round(max(0, rpm_val), 1),
                rop_ft_hr=round(max(0, rop), 2),
                torque_kftlb=round(max(0, torque), 2),
                vibration_g=round(max(0, vibration), 3),
                dls_deg_100ft=round(max(0, dls), 2),
                inclination_deg=round(inclination, 2),
                azimuth_deg=round(azimuth, 2),
                depth_ft=round(depth, 1),
                temperature_c=round(temp, 1),
                pressure_psi=round(pressure, 1),
                mud_flow_gpm=round(max(0, mud_flow), 1),
                quality_score=round(random.uniform(0.85, 1.0), 3),
            )
            session.add(packet)
            count += 1

        # Flush every well to avoid huge memory usage
        session.flush()

    session.commit()
    print(f"  Created {count} telemetry records for {len(wells)} wells")


def seed_decisions(session: Session) -> None:
    """Seed AI decision records."""
    existing = session.query(Decision).first()
    if existing:
        print("  Decision data already exists, skipping")
        return

    now = datetime.now(timezone.utc)
    commands = ["MAINTAIN", "INCREASE_WOB", "DECREASE_WOB", "INCREASE_RPM", "DECREASE_RPM", "ADJUST_TRAJECTORY"]
    outcomes = [GateOutcome.accepted, GateOutcome.accepted, GateOutcome.accepted, GateOutcome.reduced, GateOutcome.rejected]
    statuses = [ExecutionStatus.sent, ExecutionStatus.sent, ExecutionStatus.sent, ExecutionStatus.pending, ExecutionStatus.blocked]
    count = 0

    for i in range(100):
        ts = now - timedelta(minutes=(100 - i) * 3)
        cmd = random.choice(commands)
        confidence = round(random.uniform(0.55, 0.98), 3)
        outcome = random.choice(outcomes)
        exec_status = random.choice(statuses)

        decision = Decision(
            id=f"dec_{i:05d}",
            well_id=random.choice(["well_001", "well_002"]),
            timestamp=ts,
            model_version="1.0.0",
            steering_command=cmd,
            confidence_score=confidence,
            gate_outcome=outcome,
            execution_status=exec_status,
            rejection_reason="Low confidence" if outcome == GateOutcome.rejected else None,
            feature_summary={"wob": round(random.uniform(25, 50), 1), "rpm": round(random.uniform(80, 180), 1)},
            event_tags=[cmd.lower()],
        )
        session.add(decision)
        count += 1

    session.commit()
    print(f"  Created {count} decision records")


def seed_alerts(session: Session) -> None:
    """Seed alert records."""
    existing = session.query(Alert).first()
    if existing:
        print("  Alert data already exists, skipping")
        return

    now = datetime.now(timezone.utc)
    alert_templates = [
        ("High Vibration Detected", "Vibration levels exceeded threshold", AlertSeverity.high, "vibration", 0.5),
        ("WOB Out of Range", "Weight on bit exceeded safe operating range", AlertSeverity.medium, "wob", 60.0),
        ("Critical DLS Warning", "Dogleg severity approaching critical limit", AlertSeverity.critical, "dls", 3.0),
        ("RPM Fluctuation", "Rotary speed showing unusual variation", AlertSeverity.low, "rpm", 300.0),
        ("Temperature Rising", "Downhole temperature increasing above normal", AlertSeverity.high, "temperature", 80.0),
        ("Pressure Spike", "Sudden increase in standpipe pressure", AlertSeverity.critical, "pressure", 4500.0),
        ("Low ROP Warning", "Rate of penetration below minimum threshold", AlertSeverity.medium, "rop", 10.0),
        ("Torque Limit Approaching", "Torque nearing maximum safe value", AlertSeverity.high, "torque", 45.0),
    ]
    count = 0

    for i in range(30):
        template = alert_templates[i % len(alert_templates)]
        ts = now - timedelta(minutes=random.randint(5, 360))

        # Mix of statuses
        if i < 10:
            alert_status = AlertStatus.active
            ack_at = None
            res_at = None
        elif i < 20:
            alert_status = AlertStatus.acknowledged
            ack_at = ts + timedelta(minutes=random.randint(1, 30))
            res_at = None
        else:
            alert_status = AlertStatus.resolved
            ack_at = ts + timedelta(minutes=random.randint(1, 30))
            res_at = ack_at + timedelta(minutes=random.randint(5, 60))

        alert = Alert(
            id=f"alert_{i:05d}",
            well_id=random.choice(["well_001", "well_002"]),
            timestamp=ts,
            severity=template[2],
            status=alert_status,
            title=template[0],
            message=template[1],
            alert_type=template[3],
            threshold_value=template[4],
            actual_value=round(template[4] * random.uniform(0.9, 1.3), 2),
            acknowledged_at=ack_at,
            resolved_at=res_at,
        )
        session.add(alert)
        count += 1

    session.commit()
    print(f"  Created {count} alert records")


def seed_database() -> None:
    """Main seeding function."""
    print("Starting database seeding...")

    with get_session() as session:
        try:
            print("\nSeeding users...")
            seed_users(session)

            print("\nSeeding wells...")
            seed_wells(session)

            print("\nSeeding system configuration...")
            seed_system_config(session)

            print("\nSeeding AI model versions...")
            seed_model_versions(session)

            print("\nSeeding telemetry data...")
            seed_telemetry(session)

            print("\nSeeding AI decisions...")
            seed_decisions(session)

            print("\nSeeding alerts...")
            seed_alerts(session)

            print("\nDatabase seeding completed successfully!")

        except Exception as e:
            session.rollback()
            print(f"Error during seeding: {e}")
            raise
        finally:
            session.close()


if __name__ == "__main__":
    seed_database()
