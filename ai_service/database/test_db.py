#!/usr/bin/env python3
"""
Test script for the Drilling Insight Dashboard database layer.
Tests basic CRUD operations and repository functionality.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_connection():
    """Test database connection."""
    print("🔍 Testing database connection...")
    try:
        from database.db import check_database_connection
        if check_database_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_models_import():
    """Test that all models can be imported."""
    print("📦 Testing model imports...")
    try:
        from database.models import (
            User, Well, TelemetryPacket, Decision, Alert,
            ModelVersion, SystemConfig, AuditLog
        )
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import error: {e}")
        return False

def test_schemas_import():
    """Test that all schemas can be imported."""
    print("📋 Testing schema imports...")
    try:
        from database.schemas import (
            UserCreate, UserUpdate, TelemetryPacketCreate,
            DecisionCreate, AlertCreate, SystemConfigUpdate
        )
        print("✅ All schemas imported successfully")
        return True
    except Exception as e:
        print(f"❌ Schema import error: {e}")
        return False

def test_repositories_import():
    """Test that all repositories can be imported."""
    print("🏗️  Testing repository imports...")
    try:
        from database.repositories import (
            UserRepository, TelemetryRepository, DecisionRepository,
            AlertRepository, ConfigRepository
        )
        print("✅ All repositories imported successfully")
        return True
    except Exception as e:
        print(f"❌ Repository import error: {e}")
        return False

def test_basic_crud():
    """Test basic CRUD operations."""
    print("🔧 Testing basic CRUD operations...")
    try:
        from database.db import get_session
        from database.repositories import UserRepository
        from database.schemas import UserCreate

        with get_session() as session:
            repo = UserRepository(session)

            # Test create
            user_data = UserCreate(
                username="test_user",
                email="test@example.com",
                password="testpass123",
                role="operator"
            )
            user = repo.create_user(user_data)
            print(f"✅ Created test user: {user.username}")

            # Test read
            retrieved = repo.get_by_username("test_user")
            if retrieved and retrieved.username == "test_user":
                print("✅ User retrieval successful")
            else:
                print("❌ User retrieval failed")
                return False

            # Test update
            updated = repo.update_user(user.id, {"email": "updated@example.com"})
            if updated and updated.email == "updated@example.com":
                print("✅ User update successful")
            else:
                print("❌ User update failed")
                return False

            # Test delete (soft delete via deactivate)
            deactivated = repo.deactivate_user(user.id)
            if deactivated and not deactivated.is_active:
                print("✅ User deactivation successful")
            else:
                print("❌ User deactivation failed")
                return False

            # Clean up - actually delete for testing
            repo.delete(user.id)
            print("✅ User cleanup successful")

        return True

    except Exception as e:
        print(f"❌ CRUD test error: {e}")
        return False

def main():
    """Run all database tests."""
    print("🧪 Drilling Insight Dashboard - Database Tests")
    print("=" * 50)

    # Check environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  Warning: DATABASE_URL not set, skipping database tests")
        print("Set DATABASE_URL to run full tests")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/drilling_insight")
        print()

        # Run import tests only
        tests = [
            ("Model Imports", test_models_import),
            ("Schema Imports", test_schemas_import),
            ("Repository Imports", test_repositories_import)
        ]
    else:
        # Run all tests
        tests = [
            ("Database Connection", test_database_connection),
            ("Model Imports", test_models_import),
            ("Schema Imports", test_schemas_import),
            ("Repository Imports", test_repositories_import),
            ("Basic CRUD Operations", test_basic_crud)
        ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            print()

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())