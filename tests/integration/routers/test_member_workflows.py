"""Member workflows through the HTTP API, run against both storage backends."""

from starlette.testclient import TestClient


def member_payload(suffix: str) -> dict:
    return {
        "name": f"Member {suffix}",
        "email": f"member.{suffix}@example.com",
        "membership_id": f"WF-{suffix}",
        "phone": "555-123-4567",
    }


def book_payload(member_id: int, isbn: str) -> dict:
    return {
        "title": "Workflow Book",
        "author": "Workflow Author",
        "isbn": isbn,
        "published_year": 2001,
        "member_id": member_id,
    }


def create_member(client: TestClient, headers: dict, suffix: str) -> dict:
    response = client.post("/members", json=member_payload(suffix), headers=headers)
    assert response.status_code == 201
    return response.json()


def test_created_member_is_returned_with_generated_id_and_can_be_fetched(client, admin_headers):
    created = create_member(client, admin_headers, "a")

    assert created["id"] > 0
    assert created["email"] == "member.a@example.com"
    fetched = client.get(f"/members/{created['id']}", headers=admin_headers)
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_created_member_appears_in_member_list(client, admin_headers):
    created = create_member(client, admin_headers, "b")

    listed = client.get("/members", headers=admin_headers).json()

    assert created in listed


def test_updated_member_changes_are_persisted(client, admin_headers):
    created = create_member(client, admin_headers, "c")
    changes = {**member_payload("c"), "name": "Renamed Member"}

    response = client.put(f"/members/{created['id']}", json=changes, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed Member"
    refetched = client.get(f"/members/{created['id']}", headers=admin_headers).json()
    assert refetched["name"] == "Renamed Member"


def test_deleted_member_can_no_longer_be_fetched(client, admin_headers):
    created = create_member(client, admin_headers, "d")

    assert client.delete(f"/members/{created['id']}", headers=admin_headers).status_code == 204

    assert client.get(f"/members/{created['id']}", headers=admin_headers).status_code == 404
    assert created not in client.get("/members", headers=admin_headers).json()


def test_member_books_returns_only_that_members_books(client, admin_headers):
    owner = create_member(client, admin_headers, "e")
    other = create_member(client, admin_headers, "f")
    owned = client.post("/books", json=book_payload(owner["id"], "9780000000011"), headers=admin_headers).json()
    client.post("/books", json=book_payload(other["id"], "9780000000012"), headers=admin_headers)

    response = client.get(f"/members/{owner['id']}/books", headers=admin_headers)

    assert response.status_code == 200
    assert [book["id"] for book in response.json()] == [owned["id"]]


def test_member_with_no_books_returns_empty_list(client, admin_headers):
    member = create_member(client, admin_headers, "g")

    response = client.get(f"/members/{member['id']}/books", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_member_books_for_missing_member_returns_404(client, admin_headers):
    assert client.get("/members/999999/books", headers=admin_headers).status_code == 404