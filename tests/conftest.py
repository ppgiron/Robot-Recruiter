"""Test configuration and fixtures for Robot Recruiter."""

import os
import pytest
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import sys
from unittest.mock import patch

from src.github_talent_intelligence.db import Base, get_session, init_db
from src.github_talent_intelligence.candidate_db import DatabaseManager


@pytest.fixture(scope="session")
def alembic_config():
    """Get Alembic configuration."""
    config = Config("alembic.ini")
    # Override the database URL to use the test database
    config.set_main_option("sqlalchemy.url", "postgresql://postgres@localhost:5432/robot_recruiter_test")
    return config


@pytest.fixture(scope="session")
def postgresql_engine():
    """Create PostgreSQL engine for integration tests."""
    db_url = "postgresql://postgres@localhost:5432/robot_recruiter_test"
    engine = create_engine(db_url)
    return engine


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    return engine


@pytest.fixture
def create_tables(sqlite_engine):
    Base.metadata.create_all(bind=sqlite_engine)
    yield
    Base.metadata.drop_all(bind=sqlite_engine)


@pytest.fixture
def postgresql_session(postgresql_engine, alembic_config):
    print("[DEBUG] postgresql_session: START", file=sys.stderr)
    print("[DEBUG] postgresql_session: Ensuring public schema exists", file=sys.stderr)
    with postgresql_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
        conn.execute(text("SET search_path TO public;"))
        print("[DEBUG] postgresql_session: Dropping all tables before migrations", file=sys.stderr)
        drop_sql = """
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE;';
            END LOOP;
        END $$;
        """
        conn.execute(text(drop_sql))
    print("[DEBUG] postgresql_session: BEFORE Alembic migrations", file=sys.stderr)
    command.upgrade(alembic_config, "head")
    print("[DEBUG] postgresql_session: AFTER Alembic migrations", file=sys.stderr)
    print("[DEBUG] postgresql_session: Creating session", file=sys.stderr)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgresql_engine)
    session = SessionLocal()
    print("[DEBUG] postgresql_session: Yielding session", file=sys.stderr)
    yield session
    print("[DEBUG] postgresql_session: Closing session", file=sys.stderr)
    session.close()
    print("[DEBUG] postgresql_session: Truncating all tables for cleanup", file=sys.stderr)
    with postgresql_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        truncate_sql = """
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'TRUNCATE TABLE public.' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE;';
            END LOOP;
        END $$;
        """
        conn.execute(text(truncate_sql))
    print("[DEBUG] postgresql_session: Cleanup complete", file=sys.stderr)


@pytest.fixture
def sqlite_session(sqlite_engine, create_tables):
    """Create SQLite session with tables created."""
    Session = sessionmaker(bind=sqlite_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def postgresql_db_manager(postgresql_engine, alembic_config):
    print("[DEBUG] postgresql_db_manager: START", file=sys.stderr)
    print("[DEBUG] postgresql_db_manager: Ensuring public schema exists", file=sys.stderr)
    with postgresql_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS public;"))
        conn.execute(text("SET search_path TO public;"))
    print("[DEBUG] postgresql_db_manager: BEFORE Alembic migrations", file=sys.stderr)
    command.upgrade(alembic_config, "head")
    print("[DEBUG] postgresql_db_manager: AFTER Alembic migrations", file=sys.stderr)
    print("[DEBUG] postgresql_db_manager: Creating DatabaseManager", file=sys.stderr)
    db_url = "postgresql://postgres@localhost:5432/robot_recruiter_test"
    db_manager = DatabaseManager(db_url)
    print("[DEBUG] postgresql_db_manager: Yielding db_manager", file=sys.stderr)
    yield db_manager
    print("[DEBUG] postgresql_db_manager: Truncating all tables for cleanup", file=sys.stderr)
    with postgresql_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        # Dynamically truncate all tables in public schema
        truncate_sql = """
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'TRUNCATE TABLE public.' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE;';
            END LOOP;
        END $$;
        """
        conn.execute(text(truncate_sql))
    print("[DEBUG] postgresql_db_manager: Cleanup complete", file=sys.stderr)


@pytest.fixture
def sqlite_db_manager(sqlite_engine):
    """Create SQLite DatabaseManager with tables created."""
    print("[DEBUG] sqlite_db_manager: Creating DatabaseManager", file=sys.stderr)
    db_url = "sqlite:///:memory:"
    db_manager = DatabaseManager(db_url)
    db_manager.create_tables()  # Ensure all tables are created
    
    yield db_manager
    print("[DEBUG] sqlite_db_manager: Cleanup complete", file=sys.stderr)


@pytest.fixture
def temp_db_file():
    """Create a temporary database file for file-based SQLite tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "postgresql: mark test to run only with PostgreSQL"
    )
    config.addinivalue_line(
        "markers", "sqlite: mark test to run only with SQLite"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


# Environment variables for test configuration
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Store original values
    original_db_url = os.environ.get("ROBOT_RECRUITER_DB_URL")
    original_candidate_db_url = os.environ.get("CANDIDATE_DB_URL")
    
    # Set test values (will be overridden by specific fixtures)
    os.environ["ROBOT_RECRUITER_DB_URL"] = "sqlite:///:memory:"
    os.environ["CANDIDATE_DB_URL"] = "sqlite:///:memory:"
    
    yield
    
    # Restore original values
    if original_db_url:
        os.environ["ROBOT_RECRUITER_DB_URL"] = original_db_url
    else:
        os.environ.pop("ROBOT_RECRUITER_DB_URL", None)
    
    if original_candidate_db_url:
        os.environ["CANDIDATE_DB_URL"] = original_candidate_db_url
    else:
        os.environ.pop("CANDIDATE_DB_URL", None)


class TestBase:
    @pytest.fixture(autouse=True)
    def _sqlite_patch(self, request, sqlite_engine, sqlite_session):
        # Patch get_engine and get_session to use the test engine/session
        with patch('src.github_talent_intelligence.db.get_engine', return_value=sqlite_engine), \
             patch('src.github_talent_intelligence.db.get_session', return_value=sqlite_session):
            self.engine = sqlite_engine
            self.session = sqlite_session
            yield
