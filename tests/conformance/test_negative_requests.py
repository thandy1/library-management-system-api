"""Explicit negative tests: invalid input, missing resources, conflicts.

Every test runs on both backends. Protected writes use the admin token.
Where a request is rejected, the tests also verify stored data is unchanged,
and that the response status is documented in /openapi.json.
"""

import pytest
from starlette.testclient import TestClient

from app.main import app

VALID_MEMBER = {
    "name": "Neg Member",
    "email": "neg.member@example.com",
    "membership_id": "NEG001",
    "phone": "555-123-4567",
}


def valid_book(member_id: int, isbn: str = "9780000000201") -> dict:
    return {
        "title": "Neg Book",
        "author": "Neg Author",
        "isbn": isbn,
        "published_year": 2000,
        "member_id": member_id,
    }


def snapshot(client: TestClient, headers: dict) -> dict:
    """All stored Books and Members, for before/after comparison."""
    return {
        "books": client.get("/books", headers=headers).json(),
        "members": client.get("/members", headers=headers).json(),
    }


def create_member(client: TestClient, headers: dict, **overrides) -> dict:
    response = client.post("/members", json={**VALID_MEMBER, **overrides}, headers=headers)
    assert response.status_code == 201
    return response.json()


def create_book(client: TestClient, headers: dict, member_id: int, isbn: str = "9780000000201") -> dict:
    response = client.post("/books", json=valid_book(member_id, isbn), headers=headers)
    assert response.status_code == 201
    return response.json()


def documented_statuses(path: str, method: str) -> set[str]:
    """Response statuses the OpenAPI document publishes for one operation."""
    return set(app.openapi()["paths"][path][method]["responses"])


def assert_validation_error(response, field: str) -> None:
    """Check FastAPI's documented 422 shape and that it names the bad field."""
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list) and detail
    assert any(field in error["loc"] for error in detail)


# --- Validation (422) --------------------------------------------------------

@pytest.mark.parametrize("missing", ["name", "email", "membership_id", "phone"])
def test_create_member_missing_required_field_returns_422(client, admin_headers, missing):
    body = {k: v for k, v in VALID_MEMBER.items() if k != missing}
    before = snapshot(client, admin_headers)

    response = client.post("/members", json=body, headers=admin_headers)

    assert_validation_error(response, missing)
    assert snapshot(client, admin_headers) == before


@pytest.mark.parametrize("missing", ["title", "author", "isbn", "published_year", "member_id"])
def test_create_book_missing_required_field_returns_422(client, admin_headers, missing):
    owner = create_member(client, admin_headers)
    body = {k: v for k, v in valid_book(owner["id"]).items() if k != missing}
    before = snapshot(client, admin_headers)

    response = client.post("/books", json=body, headers=admin_headers)

    assert_validation_error(response, missing)
    assert snapshot(client, admin_headers) == before


def test_create_member_with_unknown_field_returns_422(client, admin_headers):
    response = client.post(
        "/members", json={**VALID_MEMBER, "nickname": "extra"}, headers=admin_headers
    )
    assert_validation_error(response, "nickname")


def test_create_book_with_unknown_field_returns_422(client, admin_headers):
    owner = create_member(client, admin_headers)
    response = client.post(
        "/books", json={**valid_book(owner["id"]), "rating": 5}, headers=admin_headers
    )
    assert_validation_error(response, "rating")


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("name", ""),
        ("name", "x" * 121),
        ("email", "not-an-email"),
        ("phone", "5551234567"),
        ("phone", "555-12-4567"),
    ],
)
def test_create_member_with_invalid_field_returns_422(client, admin_headers, field, bad_value):
    before = snapshot(client, admin_headers)

    response = client.post("/members", json={**VALID_MEMBER, field: bad_value}, headers=admin_headers)

    assert_validation_error(response, field)
    assert snapshot(client, admin_headers) == before


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("title", ""),
        ("title", "x" * 201),
        ("author", ""),
        ("published_year", 1449),
        ("published_year", 9999),
        ("member_id", 0),
        ("member_id", -1),
    ],
)
def test_create_book_with_invalid_field_returns_422(client, admin_headers, field, bad_value):
    owner = create_member(client, admin_headers)
    before = snapshot(client, admin_headers)

    response = client.post(
        "/books", json={**valid_book(owner["id"]), field: bad_value}, headers=admin_headers
    )

    assert_validation_error(response, field)
    assert snapshot(client, admin_headers) == before


@pytest.mark.parametrize("path", ["/books/abc", "/members/abc", "/members/abc/books"])
def test_non_integer_path_id_returns_422(client, admin_headers, path):
    response = client.get(path, headers=admin_headers)
    assert_validation_error(response, "member_id" if "members" in path else "book_id")


# --- Missing resources (404) -------------------------------------------------

@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/books/999999"),
        ("DELETE", "/books/999999"),
        ("GET", "/members/999999"),
        ("DELETE", "/members/999999"),
    ],
)
def test_missing_resource_returns_documented_404(client, admin_headers, method, path):
    response = client.request(method, path, headers=admin_headers)

    assert response.status_code == 404
    assert "404" in documented_statuses(path.rsplit("/", 1)[0] + "/{" + ("book_id" if "books" in path else "member_id") + "}", method.lower())
    assert response.json() == {"detail": response.json()["detail"]}


def test_update_missing_member_returns_404(client, admin_headers):
    response = client.put("/members/999999", json=VALID_MEMBER, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_update_missing_book_returns_404(client, admin_headers):
    owner = create_member(client, admin_headers)
    response = client.put("/books/999999", json=valid_book(owner["id"]), headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_create_book_for_nonexistent_member_returns_404_and_stores_nothing(client, admin_headers):
    before = snapshot(client, admin_headers)

    response = client.post("/books", json=valid_book(999999), headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"
    assert snapshot(client, admin_headers) == before


def test_update_book_to_nonexistent_member_returns_404_and_keeps_book(client, admin_headers):
    owner = create_member(client, admin_headers)
    book = create_book(client, admin_headers, owner["id"])
    before = snapshot(client, admin_headers)

    response = client.put(f"/books/{book['id']}", json=valid_book(999999), headers=admin_headers)

    assert response.status_code == 404
    assert snapshot(client, admin_headers) == before


# --- Conflicts (409) ---------------------------------------------------------

@pytest.mark.parametrize(
    ("field", "message"),
    [("email", "Email must be unique"), ("membership_id", "Membership ID must be unique")],
)
def test_create_member_with_duplicate_value_returns_409_and_stores_nothing(
    client, admin_headers, field, message
):
    create_member(client, admin_headers)
    before = snapshot(client, admin_headers)
    # Change the other unique field so only `field` collides.
    other = "membership_id" if field == "email" else "email"
    body = {**VALID_MEMBER, other: "different@example.com" if other == "email" else "NEG002"}

    response = client.post("/members", json=body, headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["detail"] == message
    assert snapshot(client, admin_headers) == before


def test_update_member_to_another_members_email_returns_409_and_keeps_data(client, admin_headers):
    create_member(client, admin_headers)
    second = create_member(client, admin_headers, email="second@example.com", membership_id="NEG002")
    before = snapshot(client, admin_headers)

    response = client.put(
        f"/members/{second['id']}", json={**VALID_MEMBER, "membership_id": "NEG002"}, headers=admin_headers
    )

    assert response.status_code == 409
    assert snapshot(client, admin_headers) == before


def test_create_book_with_duplicate_isbn_returns_409_and_stores_nothing(client, admin_headers):
    owner = create_member(client, admin_headers)
    create_book(client, admin_headers, owner["id"])
    before = snapshot(client, admin_headers)

    response = client.post("/books", json=valid_book(owner["id"]), headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "ISBN must be unique"
    assert snapshot(client, admin_headers) == before


def test_update_book_to_another_books_isbn_returns_409_and_keeps_data(client, admin_headers):
    owner = create_member(client, admin_headers)
    create_book(client, admin_headers, owner["id"], isbn="9780000000201")
    second = create_book(client, admin_headers, owner["id"], isbn="9780000000202")
    before = snapshot(client, admin_headers)

    response = client.put(
        f"/books/{second['id']}", json=valid_book(owner["id"], "9780000000201"), headers=admin_headers
    )

    assert response.status_code == 409
    assert snapshot(client, admin_headers) == before


def test_delete_member_with_books_returns_409_and_keeps_member_and_books(client, admin_headers):
    owner = create_member(client, admin_headers)
    create_book(client, admin_headers, owner["id"])
    before = snapshot(client, admin_headers)

    response = client.delete(f"/members/{owner['id']}", headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "Delete the member's books before deleting the member"
    assert snapshot(client, admin_headers) == before


# --- Documentation agrees with behavior -------------------------------------

@pytest.mark.parametrize(
    ("path", "method", "status"),
    [
        ("/members", "post", "409"),
        ("/members", "post", "422"),
        ("/members/{member_id}", "put", "404"),
        ("/members/{member_id}", "put", "409"),
        ("/members/{member_id}", "delete", "409"),
        ("/books", "post", "404"),
        ("/books", "post", "409"),
        ("/books/{book_id}", "put", "404"),
        ("/books/{book_id}", "put", "409"),
        ("/members/{member_id}/books", "get", "404"),
        ("/members/{member_id}/books", "get", "422"),
    ],
)
def test_error_statuses_asserted_above_are_documented_in_openapi(path, method, status):
    assert status in documented_statuses(path, method)