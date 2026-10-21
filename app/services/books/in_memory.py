"""In-memory Book service."""

from app.exceptions import ConflictError, NotFoundError
from app.schemas.books import BookRequest, BookResponse
from app.services.books.base import BookService
from app.services.in_memory_store import InMemoryStore


class InMemoryBookService(BookService):
    """Book operations backed by process-local dictionaries."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def _require_member(self, member_id: int) -> None:
        if member_id not in self._store.members:
            raise NotFoundError("Member not found")

    def _require_unique_isbn(self, isbn: str, exclude_book_id: int | None = None) -> None:
        for book in self._store.books.values():
            if book.isbn == isbn and book.id != exclude_book_id:
                raise ConflictError("ISBN must be unique")

    def create_book(self, request: BookRequest) -> BookResponse:
        with self._store.lock:
            self._require_member(request.member_id)
            self._require_unique_isbn(request.isbn)
            new_id = max(self._store.books, default=0) + 1
            book = BookResponse(id=new_id, **request.model_dump())
            self._store.books[new_id] = book
            return book

    def list_books(self) -> list[BookResponse]:
         with self._store.lock:
            return list(self._store.books.values())

    def get_book(self, book_id: int) -> BookResponse:
        with self._store.lock:
            book = self._store.books.get(book_id)
            if book is None:
                raise NotFoundError("Book not found")
            return book

    def update_book(self, book_id: int, request: BookRequest) -> BookResponse:
         with self._store.lock:
            self.get_book(book_id)  # raises NotFoundError if missing
            self._require_member(request.member_id)
            self._require_unique_isbn(request.isbn, exclude_book_id=book_id)
            updated = BookResponse(id=book_id, **request.model_dump())
            self._store.books[book_id] = updated
            return updated

    def delete_book(self, book_id: int) -> None:
        with self._store.lock:
            self.get_book(book_id)
            del self._store.books[book_id]