#!/usr/bin/env python3
"""
Database migration and seeding script for Drilling Insight Dashboard.
This script runs Alembic migrations and seeds the database with initial data.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Run database migrations and seeding."""
    print("Drilling Insight Dashboard - Database Migration & Seeding")
    print("=" * 60)

    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/drilling_insight")
        sys.exit(1)

    print(f"📍 Database URL: {db_url.replace(db_url.split('@')[0].split('//')[1], '***:***@')}")
    print()

    try:
        # Import database modules
        from database.db import check_database_connection
        from database.seed import seed_database

        print("🔍 Checking database connection...")
        if not check_database_connection():
            print("❌ Error: Cannot connect to database")
            print("Please ensure:")
            print("  - PostgreSQL is running")
            print("  - Database exists")
            print("  - Connection credentials are correct")
            sys.exit(1)

        print("✅ Database connection successful")
        print()

        print("🚀 Running Alembic migrations...")
        # Run Alembic upgrade
        os.system("cd database && alembic upgrade head")
        print("✅ Migrations completed")
        print()

        print("🌱 Seeding database with initial data...")
        seed_database()
        print("✅ Database seeding complete")
        print()

        print("🎉 Database migration and seeding complete!")
        print()
        print("The database is now ready for use.")

    except ImportError as e:
        print(f"❌ Error: Cannot import database modules: {e}")
        print("Make sure you're running this from the ai_service directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()