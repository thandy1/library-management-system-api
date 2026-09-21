"""Helper Functions"""


from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.books import BookRequest, BookResponse
from app.schemas.members import MemberRequest, MemberResponse
from app.storage import books, members


def validate_book_exists(book_id: int) -> None:
    """Raise 404 if book doesn't exist."""
    if book_id not in books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )


def validate_isbn(data: BookRequest) -> None:
    """Check if the ISBN is unique."""
    if any(book.isbn == data.isbn for book in books.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISBN must be unique"
        )