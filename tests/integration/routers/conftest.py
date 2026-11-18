"""Fixtures shared by the router integration tests."""

import pytest
from starlette.testclient import TestClient

# Maps each backend name to the client fixture from tests/conftest.py.
_CLIENT_FIXTURES = {"database": "database_client", "memory": "memory_client"}


@pytest.fixture(params=["database", "memory"])
def client(request: pytest.FixtureRequest) -> TestClient:
    """Header-less client for each storage backend (Docker starts only for 'database')."""
    return request.getfixturevalue(_CLIENT_FIXTURES[request.param])