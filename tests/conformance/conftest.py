"""Fixtures shared by the conformance and negative tests."""

import pytest
from starlette.testclient import TestClient


@pytest.fixture(params=["database", "memory"])
def client(request: pytest.FixtureRequest) -> TestClient:
    """Header-less client for each storage backend (Docker starts only for 'database')."""
    return request.getfixturevalue(f"{request.param}_client")