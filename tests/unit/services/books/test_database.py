"""Unit tests for InMemoryBookService using a fresh seeded store per test."""

import pytest

from app.exceptions import ConflictError, NotFoundError
from app.schemas.books import BookRequest
from app.services.books.in_memory import InMemoryBookService
from app.services.in_memory_store import InMemoryStore


@pytest.fixture
def service() -> InMemoryBookService:
    # New store per test: seed data is 3 members and 4 books.
    return InMemoryBookService(InMemoryStore())


def book_request(**overrides) -> BookRequest:
    data = {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441013593",
        "published_year": 1965,
        "member_id": 1,
    }
    return BookRequest(**{**data, **overrides})


def test_create_book_assigns_next_id(service):
    created = service.create_book(book_request())
    assert created.id == 5
    assert service.get_book(5) == created


def test_create_book_with_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.create_book(book_request(member_id=99))
    assert len(service.list_books()) == 4  # nothing stored


def test_create_book_with_duplicate_isbn_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.create_book(book_request(isbn="9780451524935"))  # seeded "1984"
    assert len(service.list_books()) == 4


def test_list_books_returns_seeded_books(service):
    assert len(service.list_books()) == 4


def test_get_missing_book_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_book(99)


def test_update_book_replaces_fields(service):
    updated = service.update_book(1, book_request(title="New Title", isbn="111"))
    assert updated.id == 1
    assert service.get_book(1).title == "New Title"


def test_update_book_may_keep_its_own_isbn(service):
    # Seeded book 1 already owns this ISBN; re-saving it is not a duplicate.
    assert service.update_book(1, book_request(isbn="9780743273565"))


def test_update_book_with_another_books_isbn_raises_conflict(service):
    with pytest.raises(ConflictError):
        service.update_book(1, book_request(isbn="9780451524935"))
    assert service.get_book(1).title == "The Great Gatsby"  # unchanged


def test_update_missing_book_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.update_book(99, book_request())


def test_update_book_with_missing_member_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.update_book(1, book_request(member_id=99))


def test_delete_book_removes_it(service):
    service.delete_book(1)
    with pytest.raises(NotFoundError):
        service.get_book(1)


def test_delete_missing_book_raises_not_found(service):
    with pytest.raises(NotFoundError):
        service.delete_book(99)