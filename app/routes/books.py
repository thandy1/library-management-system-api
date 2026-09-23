"""HTTP endpoints for the Book resource."""


from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.books import BookRequest, BookResponse
from app.schemas.members import MemberResponse
from app.storage import books, members
from app.helpers import validate_book_exists, validate_isbn, validate_member_exists


router = APIRouter(prefix="/books", tags=["Books"])


# Create a new book.
@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    description="Create a book from a validated request body."
)
def create_book(request: BookRequest) -> BookResponse:
    """Create a book from a validated JSON request body."""
    validate_member_exists(request.member_id) # Each Book must be associated with exactly one existing Member
    validate_isbn(request)
    # GENERATE NEW ID AND CREATE NEW ENTRY
    new_book_id = max(books.keys(), default=0) + 1
    new_book = BookResponse(id=new_book_id, **request.model_dump())
    books[new_book_id] = new_book
    return new_book

    
# Retrieve all books.
@router.get(
    "",
    response_model=list[BookResponse],
    status_code=status.HTTP_200_OK,
    summary="List all books",
    description="Return every book currently stored by the application."
)
def get_all_books() -> list[BookResponse]:
    """Return every book currently stored in memory."""
    return list(books.values())


# Retrieve one book by its identifier.
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Return one book",
    description="Retrieve one book by its identifier.",
    responses={404: {"description": "Book not found"}}
)
def get_book(book_id: int) -> BookResponse:
    """Return the book with the request ID."""
    validate_book_exists(book_id)
    return books[book_id]


# Updated an existing book.
@router.put(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing book",
    description="Update all editable fields of an existing book.",
    responses={404: {"description": "Book not found"}}
)
def update_book(book_id: int, request: BookRequest) -> BookResponse:
    """Update the editable fields of an existing book."""
    validate_book_exists(book_id)
    validate_isbn(request)
    validate_member_exists(request.member_id)
    updated_book = BookResponse(
        id=book_id,
        **request.model_dump()
    )
    books[book_id] = updated_book
    return updated_book


# Delete an existing book.
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a book from the in-memory storage",
    responses={404: {"description": "Book not found"}}
)
def delete_book(book_id: int) -> Response:
    """Delete a book from the in-memory storage."""
    validate_book_exists(book_id)
    books.pop(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)