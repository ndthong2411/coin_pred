"""
Initialize database and create tables.
Run this script first to set up the database.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import init_database, db
from src.utils import log
from config import settings


def main():
    """Initialize database."""
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)

    print(f"\nDatabase URL: {settings.database.database_url}")

    # Create tables
    print("\nCreating database tables...")
    try:
        init_database()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return 1

    # Check connection
    print("\nChecking database connection...")
    if db.check_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return 1

    # Show table counts
    print("\nTable counts:")
    tables = ['ohlcv', 'sentiment_data', 'features', 'predictions', 'trades']
    for table in tables:
        try:
            count = db.get_table_count(table)
            print(f"  {table:20s}: {count:>6} rows")
        except:
            print(f"  {table:20s}: ERROR")

    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
