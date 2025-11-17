"""
Database connection and session management.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings
from .models import Base
from src.utils import log


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str = None):
        """
        Initialize database connection.

        Args:
            database_url: Database URL (default from settings)
        """
        self.database_url = database_url or settings.database.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize()

    def _initialize(self):
        """Initialize database engine and session factory."""
        # SQLite specific settings
        if "sqlite" in self.database_url:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False,  # Set to True for SQL debugging
            )

            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL settings
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,
            )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        log.info(f"Database initialized: {self.database_url}")

    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            log.info("Database tables created successfully")
        except Exception as e:
            log.error(f"Error creating tables: {e}")
            raise

    def drop_tables(self):
        """Drop all tables in the database. USE WITH CAUTION!"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            log.warning("All database tables dropped")
        except Exception as e:
            log.error(f"Error dropping tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db.session_scope() as session:
                session.add(obj)
                # Automatically commits on success, rolls back on error

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def check_connection(self) -> bool:
        """
        Check if database connection is alive.

        Returns:
            True if connected, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            log.error(f"Database connection check failed: {e}")
            return False

    def get_table_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        try:
            with self.session_scope() as session:
                result = session.execute(f"SELECT COUNT(*) FROM {table_name}")
                return result.scalar()
        except Exception as e:
            log.error(f"Error counting rows in {table_name}: {e}")
            return 0

    def clear_table(self, table_name: str):
        """
        Clear all data from a table.

        Args:
            table_name: Name of the table to clear
        """
        try:
            with self.session_scope() as session:
                session.execute(f"DELETE FROM {table_name}")
            log.info(f"Table {table_name} cleared")
        except Exception as e:
            log.error(f"Error clearing table {table_name}: {e}")
            raise

    def vacuum(self):
        """Vacuum the database (SQLite only)."""
        if "sqlite" in self.database_url:
            try:
                with self.engine.connect() as conn:
                    conn.execute("VACUUM")
                log.info("Database vacuumed")
            except Exception as e:
                log.error(f"Error vacuuming database: {e}")


# Global database instance
db = Database()


def init_database():
    """Initialize database and create tables."""
    db.create_tables()
    log.info("Database initialized and tables created")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI or other frameworks.

    Yields:
        Database session
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")

    # Initialize database
    init_database()

    # Check connection
    if db.check_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")

    # Test session
    with db.session_scope() as session:
        from .models import OHLCV
        from datetime import datetime

        # Create test record
        test_ohlcv = OHLCV(
            symbol="TEST/USDT",
            timeframe="1m",
            timestamp=datetime.utcnow(),
            open=100,
            high=105,
            low=95,
            close=102,
            volume=1000,
        )
        session.add(test_ohlcv)

    print(f"OHLCV count: {db.get_table_count('ohlcv')}")

    # Clean up test data
    db.clear_table("ohlcv")
    print("✅ Database test complete")
