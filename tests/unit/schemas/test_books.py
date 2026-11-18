"""Unit tests for Book schemas. No FastAPI, database, or Docker involved."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.books import BookRequest, BookResponse

CURRENT_YEAR = datetime.now().year


def valid_book(**overrides) -> dict:
    """Build a valid payload; tests override only the field under test."""
    data = {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "978-0441013593",
        "published_year": 1965,
        "member_id": 1,
    }
    return {**data, **overrides}


def error_fields(exc_info: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    """Return the field names that failed validation."""
    return {str(e["loc"][0]) for e in exc_info.value.errors()}


def test_valid_book_request_is_accepted():
    book = BookRequest(**valid_book())
    assert book.title == "Dune"


@pytest.mark.parametrize("field", ["title", "author", "isbn", "published_year", "member_id"])
def test_missing_required_field_is_rejected(field):
    data = valid_book()
    del data[field]
    with pytest.raises(ValidationError) as exc_info:
        BookRequest(**data)
    assert error_fields(exc_info) == {field}


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        BookRequest(**valid_book(extra_field="nope"))
    assert error_fields(exc_info) == {"extra_field"}


def test_whitespace_is_trimmed():
    book = BookRequest(**valid_book(title="  Dune  ", isbn=" 123 "))
    assert book.title == "Dune"
    assert book.isbn == "123"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", ""),
        ("title", "   "),          # becomes empty after trimming
        ("title", "x" * 201),
        ("author", ""),
        ("author", "x" * 121),
        ("published_year", 1449),
        ("published_year", CURRENT_YEAR + 1),
        ("member_id", 0),
        ("member_id", -1),
    ],
)
def test_out_of_bounds_value_is_rejected(field, value):
    with pytest.raises(ValidationError) as exc_info:
        BookRequest(**valid_book(**{field: value}))
    assert error_fields(exc_info) == {field}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "x"),
        ("title", "x" * 200),
        ("author", "x"),
        ("author", "x" * 120),
        ("published_year", 1450),
        ("published_year", CURRENT_YEAR),
        ("member_id", 1),
    ],
)
def test_boundary_value_is_accepted(field, value):
    assert BookRequest(**valid_book(**{field: value}))


def test_wrong_type_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        BookRequest(**valid_book(published_year="not-a-year"))
    assert error_fields(exc_info) == {"published_year"}


def test_book_response_requires_positive_id():
    assert BookResponse(**valid_book(id=1)).id == 1
    with pytest.raises(ValidationError):
        BookResponse(**valid_book(id=0))


def test_book_request_rejects_client_supplied_id():
    # The server generates IDs, so clients may not send one.
    with pytest.raises(ValidationError) as exc_info:
        BookRequest(**valid_book(id=5))
    assert error_fields(exc_info) == {"id"}