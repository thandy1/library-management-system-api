"""Abstract Book service: the operations routers depend on."""

from abc import ABC, abstractmethod

from app.schemas.books import BookRequest, BookResponse


class BookService(ABC):
    """Contract that every Book storage implementation must follow."""

    @abstractmethod
    def create_book(self, request: BookRequest) -> BookResponse: ...

    @abstractmethod
    def list_books(self) -> list[BookResponse]: ...

    @abstractmethod
    def get_book(self, book_id: int) -> BookResponse: ...

    @abstractmethod
    def update_book(self, book_id: int, request: BookRequest) -> BookResponse: ...

    @abstractmethod
    def delete_book(self, book_id: int) -> None: ...