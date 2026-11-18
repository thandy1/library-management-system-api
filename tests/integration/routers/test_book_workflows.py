"""Book workflows through the HTTP API, run against both storage backends."""

from starlette.testclient import TestClient


def create_member(client: TestClient, headers: dict, suffix: str) -> dict:
    response = client.post(
        "/members",
        json={
            "name": f"Owner {suffix}",
            "email": f"owner.{suffix}@example.com",
            "membership_id": f"BK-{suffix}",
            "phone": "555-987-6543",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def book_payload(member_id: int, isbn: str, title: str = "Workflow Book") -> dict:
    return {
        "title": title,
        "author": "Workflow Author",
        "isbn": isbn,
        "published_year": 1999,
        "member_id": member_id,
    }


def create_book(client: TestClient, headers: dict, member_id: int, isbn: str) -> dict:
    response = client.post("/books", json=book_payload(member_id, isbn), headers=headers)
    assert response.status_code == 201
    return response.json()


def test_created_book_is_returned_with_generated_id_and_can_be_fetched(client, admin_headers):
    owner = create_member(client, admin_headers, "a")

    created = create_book(client, admin_headers, owner["id"], "9780000000101")

    assert created["id"] > 0
    assert created["member_id"] == owner["id"]
    fetched = client.get(f"/books/{created['id']}", headers=admin_headers)
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_created_book_appears_in_book_list(client, admin_headers):
    owner = create_member(client, admin_headers, "b")
    created = create_book(client, admin_headers, owner["id"], "9780000000102")

    assert created in client.get("/books", headers=admin_headers).json()


def test_updated_book_changes_are_persisted(client, admin_headers):
    owner = create_member(client, admin_headers, "c")
    created = create_book(client, admin_headers, owner["id"], "9780000000103")

    response = client.put(
        f"/books/{created['id']}",
        json=book_payload(owner["id"], "9780000000103", title="New Title"),
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert client.get(f"/books/{created['id']}", headers=admin_headers).json()["title"] == "New Title"


def test_reassigning_book_moves_it_between_members_book_lists(client, admin_headers):
    first = create_member(client, admin_headers, "d")
    second = create_member(client, admin_headers, "e")
    book = create_book(client, admin_headers, first["id"], "9780000000104")

    client.put(
        f"/books/{book['id']}",
        json=book_payload(second["id"], "9780000000104"),
        headers=admin_headers,
    )

    first_books = client.get(f"/members/{first['id']}/books", headers=admin_headers).json()
    second_books = client.get(f"/members/{second['id']}/books", headers=admin_headers).json()
    assert first_books == []
    assert [b["id"] for b in second_books] == [book["id"]]


def test_deleted_book_can_no_longer_be_fetched(client, admin_headers):
    owner = create_member(client, admin_headers, "f")
    book = create_book(client, admin_headers, owner["id"], "9780000000105")

    assert client.delete(f"/books/{book['id']}", headers=admin_headers).status_code == 204

    assert client.get(f"/books/{book['id']}", headers=admin_headers).status_code == 404
    assert client.get(f"/members/{owner['id']}/books", headers=admin_headers).json() == []


def test_member_can_be_deleted_after_their_books_are_deleted(client, admin_headers):
    owner = create_member(client, admin_headers, "g")
    book = create_book(client, admin_headers, owner["id"], "9780000000106")
    client.delete(f"/books/{book['id']}", headers=admin_headers)

    assert client.delete(f"/members/{owner['id']}", headers=admin_headers).status_code == 204