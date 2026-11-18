"""Behavior specific to the PostgreSQL-backed API (empty start, persistent IDs)."""

NEW_MEMBER = {
    "name": "Db Member",
    "email": "db.member@example.com",
    "membership_id": "DB001",
    "phone": "555-111-2222",
}


def test_database_backend_starts_empty(database_client, admin_headers):
    assert database_client.get("/books", headers=admin_headers).json() == []
    assert database_client.get("/members", headers=admin_headers).json() == []


def test_database_ids_are_not_reused_after_delete(database_client, admin_headers):
    first = database_client.post("/members", json=NEW_MEMBER, headers=admin_headers).json()
    database_client.delete(f"/members/{first['id']}", headers=admin_headers)

    second = database_client.post("/members", json=NEW_MEMBER, headers=admin_headers).json()

    assert second["id"] > first["id"]


def test_state_does_not_leak_between_tests(database_client, admin_headers):
    # reset_database drops tables per test, so earlier tests' rows must be gone.
    assert database_client.get("/members", headers=admin_headers).json() == []