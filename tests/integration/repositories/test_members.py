"""Member repository behavior against real PostgreSQL (Testcontainers)."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.member import Member
from app.repositories.members import MemberRepository


def make_member(n: int = 1) -> Member:
    return Member(
        name=f"Member {n}",
        email=f"member{n}@example.com",
        membership_id=f"M-{n:04d}",
        phone="555-123-4567",
    )


def test_add_generates_id(db_session):
    repo = MemberRepository(db_session)
    member = make_member()
    assert member.id is None

    repo.add(member)

    assert isinstance(member.id, int)
    assert repo.get(member.id) is member


def test_generated_ids_increase(db_session):
    repo = MemberRepository(db_session)
    first, second = make_member(1), make_member(2)
    repo.add(first)
    repo.add(second)
    assert second.id > first.id


def test_list_all_orders_by_id(db_session):
    repo = MemberRepository(db_session)
    for n in (1, 2, 3):
        repo.add(make_member(n))
    ids = [m.id for m in repo.list_all()]
    assert ids == sorted(ids) and len(ids) == 3


def test_lookup_by_email_and_membership_id(db_session):
    repo = MemberRepository(db_session)
    repo.add(make_member(1))
    assert repo.get_by_email("member1@example.com").membership_id == "M-0001"
    assert repo.get_by_membership_id("M-0001").email == "member1@example.com"
    assert repo.get_by_email("nobody@example.com") is None
    assert repo.get_by_membership_id("M-9999") is None


def test_get_missing_returns_none(db_session):
    assert MemberRepository(db_session).get(999_999) is None


def test_duplicate_email_violates_unique_constraint(db_session):
    repo = MemberRepository(db_session)
    repo.add(make_member(1))
    duplicate = make_member(2)
    duplicate.email = "member1@example.com"
    with pytest.raises(IntegrityError):
        repo.add(duplicate)
    db_session.rollback()


def test_duplicate_membership_id_violates_unique_constraint(db_session):
    repo = MemberRepository(db_session)
    repo.add(make_member(1))
    duplicate = make_member(2)
    duplicate.membership_id = "M-0001"
    with pytest.raises(IntegrityError):
        repo.add(duplicate)
    db_session.rollback()


def test_delete_removes_member(db_session):
    repo = MemberRepository(db_session)
    member = make_member()
    repo.add(member)
    member_id = member.id
    repo.delete(member)
    assert repo.get(member_id) is None