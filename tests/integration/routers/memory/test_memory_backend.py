"""Behavior specific to the in-memory API (seed data, max+1 IDs)."""

NEW_MEMBER = {
    "name": "Memory Member",
    "email": "memory.member@example.com",
    "membership_id": "MEM900",
    "phone": "555-333-4444",
}


def test_memory_backend_starts_with_seed_data(memory_client, admin_headers):
    members = memory_client.get("/members", headers=admin_headers).json()
    books = memory_client.get("/books", headers=admin_headers).json()

    assert [m["id"] for m in members] == [1, 2, 3]
    assert [b["id"] for b in books] == [1, 2, 3, 4]


def test_seeded_member_owns_expected_books(memory_client, admin_headers):
    books = memory_client.get("/members/1/books", headers=admin_headers).json()

    assert [b["id"] for b in books] == [1, 2]


def test_new_member_id_follows_highest_seeded_id(memory_client, admin_headers):
    created = memory_client.post("/members", json=NEW_MEMBER, headers=admin_headers).json()

    assert created["id"] == 4


def test_state_does_not_leak_between_tests(memory_client, admin_headers):
    # The lifespan builds a fresh store per test, so the earlier test's member is gone.
    members = memory_client.get("/members", headers=admin_headers).json()
    assert len(members) == 3