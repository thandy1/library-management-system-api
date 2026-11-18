"""Unit tests for InMemoryMemberService using a fresh seeded store per test."""

import pytest

from app.exceptions import ConflictError, NotFoundError
from app.schemas.members import MemberRequest
from app.services.in_memory_store import InMemoryStore
from app.services.members.in_memory import InMemoryMemberService


@pytest.fixture
def service() -> InMemoryMemberService:
    # New store per test: seed data is 3 members and 4 books.
    return InMemoryMemberService(InMemoryStore())


def member_request(**overrides) -> MemberRequest:
    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "membership_id": "MEM100",
        "phone": "555-111-2222",
    }
    return MemberRequest(**{**data, **overrides})


def test_create_member_assigns_next_id(service):
    created = service.create_member(member_request())
    assert created.id == 4
    assert service.get_member(4) == created


def test_create_member_with_duplicate_email_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.create_member(member_request(email="john@example.com"))
    assert len(service.list_members()) == 3  # nothing stored


def test_create_member_with_duplicate_membership_id_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.create_member(member_request(membership_id="MEM001"))
    assert len(service.list_members()) == 3


def test_list_members_returns_seeded_members(service):
    assert len(service.list_members()) == 3


def test_get_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_member(99)


def test_update_member_replaces_fields(service):
    updated = service.update_member(1, member_request(name="New Name"))
    assert updated.id == 1
    assert service.get_member(1).name == "New Name"


def test_update_member_may_keep_its_own_email(service):
    assert service.update_member(1, member_request(email="john@example.com"))


def test_update_member_with_another_members_email_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.update_member(1, member_request(email="jane@example.com"))
    assert service.get_member(1).name == "John Doe"  # unchanged


def test_update_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.update_member(99, member_request())


def test_delete_member_with_books_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.delete_member(1)  # seeded member 1 owns books 1 and 2
    assert service.get_member(1)  # still there


def test_delete_member_without_books_removes_it(service):
    created = service.create_member(member_request())  # new members own no books
    service.delete_member(created.id)
    with pytest.raises(NotFoundError):
        service.get_member(created.id)


def test_delete_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.delete_member(99)


def test_list_member_books_returns_only_that_members_books(service):
    assert [b.id for b in service.list_member_books(1)] == [1, 2]


def test_list_member_books_for_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.list_member_books(99)