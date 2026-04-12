#!/usr/bin/env python3
"""
Database initialization script for Drilling Insight Dashboard.
This script creates all tables and sets up the database for the first time.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Initialize the database."""
    print("Drilling Insight Dashboard - Database Initialization")
    print("=" * 55)

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
        from database.db import create_database, check_database_connection, init_db

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

        print("🏗️  Creating database tables...")
        create_database()
        print("✅ Tables created successfully")
        print()

        print("🎯 Running initialization...")
        init_db()
        print("✅ Database initialization complete")
        print()

        print("🎉 Database is ready!")
        print()
        print("Next steps:")
        print("1. Run the seed migration: python database/migrate.py")
        print("2. Start the application: python -m uvicorn api:app --reload")
        print("3. Visit http://localhost:8001/docs for API documentation")

    except ImportError as e:
        print(f"❌ Error: Cannot import database modules: {e}")
        print("Make sure you're running this from the ai_service directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()