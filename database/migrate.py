#!/usr/bin/env python3
"""
Database Migration Runner for Drilling Insight Dashboard
Run migrations in order against a PostgreSQL database.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from pathlib import Path

def get_database_connection():
    """Get database connection from environment variables."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/drilling_insight")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def run_migration(conn, migration_file):
    """Run a single migration file."""
    print(f"Running migration: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    try:
        with conn.cursor() as cursor:
            cursor.execute(migration_sql)
        conn.commit()
        print(f"✓ Migration {migration_file} completed successfully")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Migration {migration_file} failed: {e}")
        sys.exit(1)

def get_migration_files():
    """Get migration files in order."""
    migration_dir = Path(__file__).parent / 'migrations'
    if not migration_dir.exists():
        print(f"Error: Migration directory not found: {migration_dir}")
        sys.exit(1)

    migration_files = sorted(migration_dir.glob('*.sql'))
    if not migration_files:
        print("No migration files found")
        sys.exit(1)

    return migration_files

def main():
    """Main migration runner."""
    print("Drilling Insight Dashboard - Database Migration Runner")
    print("=" * 55)

    # Get migration files
    migration_files = get_migration_files()
    print(f"Found {len(migration_files)} migration files:")
    for mf in migration_files:
        print(f"  - {mf.name}")
    print()

    # Confirm execution
    response = input("This will run migrations against the database. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled.")
        sys.exit(0)

    # Connect to database
    conn = get_database_connection()
    print("Connected to database successfully")
    print()

    # Run migrations
    try:
        for migration_file in migration_files:
            run_migration(conn, migration_file)
        print()
        print("✓ All migrations completed successfully!")
        print()
        print("Next steps:")
        print("1. Set DATABASE_URL in your application environment")
        print("2. Run the application and verify database connectivity")
        print("3. Check the seeded demo data in your application")

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()