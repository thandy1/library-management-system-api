"""Unit tests for DatabaseMemberService decisions and transaction outcomes.

Repositories and Session are fakes, so no PostgreSQL runs. Real constraint
behavior is covered later by the Testcontainers integration tests.
"""

import pytest
from sqlalchemy.exc import IntegrityError

import app.services.members.database as database_module
from app.exceptions import ConflictError, NotFoundError
from app.models.book import Book
from app.models.member import Member
from app.schemas.members import MemberRequest
from app.services.members.database import DatabaseMemberService
from tests.unit.services.fakes import (
    FakeBookRepository,
    FakeMemberStore,
    FakeSessionFactory,
    FakeUniqueViolation,
)


def make_member(member_id: int, email: str, membership_id: str) -> Member:
    return Member(
        id=member_id, name="Name", email=email,
        membership_id=membership_id, phone="555-123-4567",
    )


def member_request(**overrides) -> MemberRequest:
    data = {"name": "Ada", "email": "new@example.com",
            "membership_id": "NEW", "phone": "555-111-2222"}
    return MemberRequest(**{**data, **overrides})


@pytest.fixture
def members() -> FakeMemberStore:
    return FakeMemberStore({
        1: make_member(1, "one@example.com", "M1"),
        2: make_member(2, "two@example.com", "M2"),
    })


@pytest.fixture
def books() -> FakeBookRepository:
    # Member 1 owns one book; member 2 owns none.
    book = Book(id=1, title="T", author="A", isbn="I1", published_year=2000, member_id=1)
    return FakeBookRepository({1: book})


@pytest.fixture
def factory() -> FakeSessionFactory:
    return FakeSessionFactory()


@pytest.fixture
def service(monkeypatch, members, books, factory) -> DatabaseMemberService:
    # Swap the repository classes the service module looks up at call time.
    monkeypatch.setattr(database_module, "MemberRepository", lambda session: members)
    monkeypatch.setattr(database_module, "BookRepository", lambda session: books)
    return DatabaseMemberService(factory)


def test_create_member_commits_and_returns_generated_id(service, factory):
    created = service.create_member(member_request())
    assert created.id == 3
    assert factory.session.committed and not factory.session.rolled_back


def test_create_member_with_duplicate_email_rolls_back_without_adding(service, members, factory):
    with pytest.raises(ConflictError):
        service.create_member(member_request(email="one@example.com"))
    assert members.add_calls == 0
    assert factory.session.rolled_back and not factory.session.committed


def test_create_member_with_duplicate_membership_id_rolls_back(service, members, factory):
    with pytest.raises(ConflictError):
        service.create_member(member_request(membership_id="M1"))
    assert members.add_calls == 0
    assert factory.session.rolled_back


def test_create_member_translates_database_unique_violation(service, members, factory):
    # Simulates a race: both pre-checks passed, but PostgreSQL rejected the INSERT.
    driver_error = FakeUniqueViolation(constraint_name="members_email_key")
    members.raise_on_add = IntegrityError(
        statement="INSERT INTO members ...",
        params={},
        orig=driver_error,
    )

    with pytest.raises(ConflictError, match="Email must be unique"):
        service.create_member(member_request())

    assert factory.session.rolled_back


def test_get_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_member(99)


def test_list_members_returns_all(service):
    assert [m.id for m in service.list_members()] == [1, 2]


def test_update_member_commits_changes(service, factory):
    updated = service.update_member(1, member_request(email="one@example.com", name="New"))
    assert updated.name == "New"
    assert factory.session.committed


def test_update_member_with_another_members_email_rolls_back(service, members, factory):
    with pytest.raises(ConflictError):
        service.update_member(1, member_request(email="two@example.com"))
    assert members.members[1].name == "Name"  # unchanged
    assert factory.session.rolled_back


def test_update_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.update_member(99, member_request())


def test_delete_member_without_books_commits(service, members, factory):
    service.delete_member(2)
    assert 2 not in members.members
    assert factory.session.committed


def test_delete_member_with_books_raises_conflict_and_keeps_member(service, members, factory):
    with pytest.raises(ConflictError):
        service.delete_member(1)
    assert 1 in members.members
    assert factory.session.rolled_back


def test_delete_missing_member_raises_not_found(service, factory):
    with pytest.raises(NotFoundError):
        service.delete_member(99)
    assert factory.session.rolled_back


def test_list_member_books_returns_only_that_members_books(service):
    assert [b.id for b in service.list_member_books(1)] == [1]
    assert service.list_member_books(2) == []


def test_list_member_books_for_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.list_member_books(99)