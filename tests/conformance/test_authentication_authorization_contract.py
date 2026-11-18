"""HTTP-boundary tests for authentication, authorization, and OpenAPI security.

Each HTTP test runs against both storage backends. The plain client has no
default Authorization header; every request passes the headers it needs.
"""

import pytest
from starlette.testclient import TestClient

BEARER_SCHEME = "BearerAuthentication"
WRITE_METHODS = {"post", "put", "patch", "delete"}

NEW_MEMBER = {
    "name": "Test Person",
    "email": "test.person@example.com",
    "membership_id": "TEST001",
    "phone": "555-123-4567",
}
UPDATED_MEMBER = {**NEW_MEMBER, "name": "Renamed Person"}


def book_payload(member_id: int) -> dict:
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "9781234567897",
        "published_year": 2000,
        "member_id": member_id,
    }


def snapshot(client: TestClient, admin_headers: dict[str, str]) -> dict:
    """Capture all stored Books and Members for before/after comparison."""
    return {
        "books": client.get("/books", headers=admin_headers).json(),
        "members": client.get("/members", headers=admin_headers).json(),
    }


READ_ROUTES = ["/books", "/members", "/books/1", "/members/1", "/members/1/books"]
WRITE_REQUESTS = [
    ("POST", "/members", NEW_MEMBER),
    ("PUT", "/members/1", UPDATED_MEMBER),
    ("DELETE", "/members/1", None),
    ("POST", "/books", book_payload(1)),
    ("PUT", "/books/1", book_payload(1)),
    ("DELETE", "/books/1", None),
]
WRITE_IDS = [f"{method} {path}" for method, path, _ in WRITE_REQUESTS]


# --- Public routes -----------------------------------------------------------

@pytest.mark.parametrize("path", ["/", "/health"])
def test_public_routes_need_no_token(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_documentation_routes_are_public(client, path):
    assert client.get(path).status_code == 200


# --- 401: missing, malformed, unknown ---------------------------------------

@pytest.mark.parametrize("path", READ_ROUTES)
def test_protected_reads_without_token_return_401_with_bearer_challenge(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "authorization",
    ["Bearer wrong-token", "Basic dGVzdDp0ZXN0", "Token abc", "Bearer", ""],
    ids=["unknown-token", "wrong-scheme", "malformed-scheme", "no-token-value", "empty-header"],
)
def test_invalid_authorization_header_returns_401(client, authorization):
    response = client.get("/books", headers={"Authorization": authorization})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(("method", "path", "body"), WRITE_REQUESTS, ids=WRITE_IDS)
def test_unauthenticated_writes_return_401_and_change_nothing(
    client, admin_headers, method, path, body
):
    before = snapshot(client, admin_headers)
    response = client.request(method, path, json=body)
    assert response.status_code == 401
    assert snapshot(client, admin_headers) == before


# --- Roles -------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/books", "/members"])
def test_member_role_can_read_collections(client, member_headers, path):
    assert client.get(path, headers=member_headers).status_code == 200


@pytest.mark.parametrize("path", ["/books", "/members"])
def test_admin_role_can_read_collections(client, admin_headers, path):
    assert client.get(path, headers=admin_headers).status_code == 200


@pytest.mark.parametrize(("method", "path", "body"), WRITE_REQUESTS, ids=WRITE_IDS)
def test_member_role_write_returns_403_and_changes_nothing(
    client, admin_headers, member_headers, method, path, body
):
    before = snapshot(client, admin_headers)
    response = client.request(method, path, json=body, headers=member_headers)
    assert response.status_code == 403
    assert snapshot(client, admin_headers) == before


def test_admin_can_create_update_and_delete_members_and_books(client, admin_headers):
    created_member = client.post("/members", json=NEW_MEMBER, headers=admin_headers)
    assert created_member.status_code == 201
    member_id = created_member.json()["id"]

    created_book = client.post("/books", json=book_payload(member_id), headers=admin_headers)
    assert created_book.status_code == 201
    book_id = created_book.json()["id"]

    updated_member = client.put(
        f"/members/{member_id}", json=UPDATED_MEMBER, headers=admin_headers
    )
    assert updated_member.status_code == 200
    assert updated_member.json()["name"] == "Renamed Person"

    # The book must go first: deleting a Member who still has Books is blocked.
    assert client.delete(f"/books/{book_id}", headers=admin_headers).status_code == 204
    assert client.delete(f"/members/{member_id}", headers=admin_headers).status_code == 204


# --- Published OpenAPI security contract ------------------------------------

@pytest.fixture(scope="module")
def openapi_schema() -> dict:
    # Documentation is generated from route definitions, so memory mode is enough.
    from app.main import app

    return app.openapi()


def operations(schema: dict, prefixes: tuple[str, ...]):
    """Yield (path, method, operation) for paths starting with any prefix."""
    for path, path_item in schema["paths"].items():
        if path.startswith(prefixes):
            for method, operation in path_item.items():
                yield path, method, operation


def test_openapi_publishes_http_bearer_security_scheme(openapi_schema):
    scheme = openapi_schema["components"]["securitySchemes"][BEARER_SCHEME]
    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"


def test_every_book_and_member_operation_requires_bearer_security(openapi_schema):
    found = list(operations(openapi_schema, ("/books", "/members")))
    assert found, "expected Book and Member operations in the schema"
    for path, method, operation in found:
        assert {BEARER_SCHEME: []} in operation.get("security", []), f"{method} {path}"


@pytest.mark.parametrize("path", ["/", "/health"])
def test_public_operations_publish_no_security_requirement(openapi_schema, path):
    assert "security" not in openapi_schema["paths"][path]["get"]


def test_protected_operations_document_401_and_write_operations_document_403(openapi_schema):
    for path, method, operation in operations(openapi_schema, ("/books", "/members")):
        responses = operation["responses"]
        assert "401" in responses, f"{method} {path} missing 401"
        if method in WRITE_METHODS:
            assert "403" in responses, f"{method} {path} missing 403"
        else:
            assert "403" not in responses, f"{method} {path} should not document 403"


def test_401_response_documents_www_authenticate_header(openapi_schema):
    operation = openapi_schema["paths"]["/books"]["get"]
    assert "WWW-Authenticate" in operation["responses"]["401"]["headers"]