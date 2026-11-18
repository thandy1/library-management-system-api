"""Shared pytest fixtures (see the professor's conftest for the lifetime diagrams).

Fixture flow: database_client -> reset_database -> db_engine -> postgres_container
The container and engine live for the whole pytest run; tables are dropped and
recreated per test, so every test starts with empty, isolated state.
"""

import os
from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient
from testcontainers.community.postgres import PostgresContainer

from app.auth.users import Role, get_demo_token_for_role
from app.config import Settings, StorageBackend

# Fixed test tokens so tests never depend on a developer's local .env.
TEST_MEMBER_TOKEN = "test-member-token"
TEST_ADMIN_TOKEN = "test-admin-token"


@pytest.fixture(autouse=True)
def test_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force known tokens for every test; env vars override .env values."""
    monkeypatch.setenv("DEMO_MEMBER_TOKEN", TEST_MEMBER_TOKEN)
    monkeypatch.setenv("DEMO_ADMIN_TOKEN", TEST_ADMIN_TOKEN)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start one disposable PostgreSQL database for the entire pytest session."""
    with PostgresContainer(
        "postgres:18",
        username="postgres",
        password="postgres",
        dbname="library_test",
        driver="psycopg",
    ) as container:
        # Point the app at the temporary DB, never the local "library" database.
        os.environ["DATABASE_URL"] = container.get_connection_url()
        yield container
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def db_engine(postgres_container: PostgresContainer) -> Engine:
    """Return the application engine configured for the temporary container."""
    from app import models  # noqa: F401  (registers tables on Base.metadata)
    from app.database.session import create_database

    return create_database(Settings()).engine


@pytest.fixture
def reset_database(db_engine: Engine) -> Generator[None, None, None]:
    """Give each integration test empty Book and Member tables."""
    from app.models.base import Base

    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    yield
    Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def db_session(
    reset_database: None, db_engine: Engine
) -> Generator[Session, None, None]:
    """Provide one real Session for a repository integration test."""
    session_factory = sessionmaker(bind=db_engine, autoflush=False)
    with session_factory() as session:
        yield session
        session.rollback()


@pytest.fixture
def database_client(reset_database: None) -> Generator[TestClient, None, None]:
    """TestClient running the real app against the temporary database."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def memory_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """TestClient whose lifespan selects the in-memory services."""
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.main import app

    with TestClient(app) as test_client:
        # The lifespan builds a fresh InMemoryStore, so no state leaks between tests.
        yield test_client


@pytest.fixture
def demo_settings() -> Settings:
    """Settings with explicit tokens and no database requirement."""
    return Settings(
        storage_backend=StorageBackend.MEMORY,
        demo_member_token=TEST_MEMBER_TOKEN,
        demo_admin_token=TEST_ADMIN_TOKEN,
    )


@pytest.fixture
def member_headers(demo_settings: Settings) -> dict[str, str]:
    """Authorization header for the member role."""
    return {
        "Authorization": f"Bearer {get_demo_token_for_role(Role.MEMBER, demo_settings)}"
    }


@pytest.fixture
def admin_headers(demo_settings: Settings) -> dict[str, str]:
    """Authorization header for the administrator role."""
    return {
        "Authorization": f"Bearer {get_demo_token_for_role(Role.ADMIN, demo_settings)}"
    }


@pytest.fixture
def admin_client(database_client: TestClient, admin_headers: dict[str, str]) -> TestClient:
    """Database-backed client sending the admin token by default."""
    database_client.headers.update(admin_headers)
    return database_client


@pytest.fixture
def member_client(database_client: TestClient, member_headers: dict[str, str]) -> TestClient:
    """Database-backed client sending the member token by default."""
    database_client.headers.update(member_headers)
    return database_client