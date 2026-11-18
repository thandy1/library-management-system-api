"""HTTP endpoints for the Book resource."""

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_book_service
from app.schemas.books import BookRequest, BookResponse
from app.services.books.base import BookService
from app.auth.dependencies import (
    ADMIN_RESPONSES,
    AUTHENTICATED_RESPONSES,
    get_current_user,
    require_admin,
)

router = APIRouter(prefix="/books", tags=["Books"])


# POST /books (admin only)
@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    description="Create a book from a validated request body.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Member not found"},
        409: {"description": "A book with this ISBN already exists"},
    },
)
def create_book(
    request: BookRequest,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Create a book from a validated JSON request body."""
    return service.create_book(request)


# GET /books (any valid token)
@router.get(
    "",
    response_model=list[BookResponse],
    status_code=status.HTTP_200_OK,
    summary="List all books",
    description="Return every book currently stored by the application.",
    dependencies=[Depends(get_current_user)],
    responses=AUTHENTICATED_RESPONSES,
)
def get_all_books(
    service: BookService = Depends(get_book_service),
) -> list[BookResponse]:
    """Return every stored book."""
    return service.list_books()


# GET /books/{book_id} (any valid token)
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Return one book",
    description="Retrieve one book by its identifier.",
    dependencies=[Depends(get_current_user)],
    responses={
        **AUTHENTICATED_RESPONSES,
        404: {"description": "Book not found"},
    },
)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Return the book with the requested ID."""
    return service.get_book(book_id)


# PUT /books/{book_id} (admin only)
@router.put(
    "/{book_id}",
    response_model=BookResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing book",
    description="Update all editable fields of an existing book.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Book or member not found"},
        409: {"description": "A book with this ISBN already exists"},
    },
)
def update_book(
    book_id: int,
    request: BookRequest,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Update the editable fields of an existing book."""
    return service.update_book(book_id, request)


# DELETE /books/{book_id} (admin only)
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete a book by its identifier.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Book not found"},
    },
)
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> Response:
    """Delete a book."""
    service.delete_book(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)