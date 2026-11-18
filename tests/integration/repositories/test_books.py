"""Book repository behavior and the Member-to-Book foreign key (real PostgreSQL)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.book import Book
from app.models.member import Member
from app.repositories.books import BookRepository
from app.repositories.members import MemberRepository


def add_member(db_session, n: int = 1) -> Member:
    member = Member(
        name=f"Member {n}",
        email=f"member{n}@example.com",
        membership_id=f"M-{n:04d}",
        phone="555-123-4567",
    )
    MemberRepository(db_session).add(member)
    return member


def make_book(member_id: int, n: int = 1) -> Book:
    return Book(
        title=f"Book {n}",
        author="Some Author",
        isbn=f"978000000000{n}",
        published_year=2000,
        member_id=member_id,
    )


def test_add_generates_id(db_session):
    member = add_member(db_session)
    repo = BookRepository(db_session)
    book = make_book(member.id)
    assert book.id is None

    repo.add(book)

    assert isinstance(book.id, int)
    assert repo.get(book.id) is book


def test_list_all_orders_by_id(db_session):
    member = add_member(db_session)
    repo = BookRepository(db_session)
    for n in (1, 2, 3):
        repo.add(make_book(member.id, n))
    ids = [b.id for b in repo.list_all()]
    assert ids == sorted(ids) and len(ids) == 3


def test_list_by_member_returns_only_that_members_books(db_session):
    first, second = add_member(db_session, 1), add_member(db_session, 2)
    repo = BookRepository(db_session)
    repo.add(make_book(first.id, 1))
    repo.add(make_book(first.id, 2))
    repo.add(make_book(second.id, 3))

    assert [b.isbn for b in repo.list_by_member(first.id)] == [
        "9780000000001",
        "9780000000002",
    ]
    assert len(repo.list_by_member(second.id)) == 1


def test_get_by_isbn(db_session):
    member = add_member(db_session)
    repo = BookRepository(db_session)
    repo.add(make_book(member.id, 1))
    assert repo.get_by_isbn("9780000000001").title == "Book 1"
    assert repo.get_by_isbn("0000000000000") is None


def test_member_has_books(db_session):
    with_books, without_books = add_member(db_session, 1), add_member(db_session, 2)
    repo = BookRepository(db_session)
    repo.add(make_book(with_books.id))
    assert repo.member_has_books(with_books.id) is True
    assert repo.member_has_books(without_books.id) is False


def test_duplicate_isbn_violates_unique_constraint(db_session):
    member = add_member(db_session)
    repo = BookRepository(db_session)
    repo.add(make_book(member.id, 1))
    duplicate = make_book(member.id, 2)
    duplicate.isbn = "9780000000001"
    with pytest.raises(IntegrityError):
        repo.add(duplicate)
    db_session.rollback()


def test_book_with_nonexistent_member_violates_foreign_key(db_session):
    with pytest.raises(IntegrityError) as exc:
        BookRepository(db_session).add(make_book(member_id=999_999))
    assert exc.value.orig.sqlstate == "23503"  # foreign_key_violation
    db_session.rollback()


def test_database_restricts_deleting_member_who_has_books(db_session):
    """Raw SQL so the test hits the ON DELETE RESTRICT rule itself, not ORM logic."""
    member = add_member(db_session)
    BookRepository(db_session).add(make_book(member.id))

    with pytest.raises(IntegrityError) as exc:
        db_session.execute(text("DELETE FROM members WHERE id = :id"), {"id": member.id})
        assert exc.value.orig.sqlstate == "23001"  # restrict_violation (ON DELETE RESTRICT)


def test_member_repository_delete_is_blocked_when_books_exist(db_session):
    member = add_member(db_session)
    BookRepository(db_session).add(make_book(member.id))

    with pytest.raises(IntegrityError):
        MemberRepository(db_session).delete(member)
    db_session.rollback()


def test_delete_book_then_member_succeeds(db_session):
    member = add_member(db_session)
    books = BookRepository(db_session)
    book = make_book(member.id)
    books.add(book)

    books.delete(book)
    MemberRepository(db_session).delete(member)

    assert books.get(book.id) is None
    assert MemberRepository(db_session).get(member.id) is None