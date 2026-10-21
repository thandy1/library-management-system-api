"""Database-backed Book service. Owns one transaction per operation."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import ConflictError, NotFoundError
from app.models.book import Book
from app.repositories.books import BookRepository
from app.repositories.members import MemberRepository
from app.schemas.books import BookRequest, BookResponse
from app.services.books.base import BookService
from app.services.integrity import translate_integrity_error


class DatabaseBookService(BookService):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_book(self, request: BookRequest) -> BookResponse:
        try:
            # Fresh Session per operation; begin() commits on success, rolls back on error.
            with self._session_factory() as session, session.begin():
                books = BookRepository(session)
                if MemberRepository(session).get(request.member_id) is None:
                    raise NotFoundError("Member not found")
                if books.get_by_isbn(request.isbn) is not None:
                    raise ConflictError("ISBN must be unique")
                book = Book(**request.model_dump())
                books.add(book)
                return BookResponse.model_validate(book, from_attributes=True)
        except IntegrityError as exc:  # race: constraint is the final authority
            raise translate_integrity_error(exc, NotFoundError("Member not found")) from exc

    def list_books(self) -> list[BookResponse]:
        with self._session_factory() as session:
            return [
                BookResponse.model_validate(b, from_attributes=True)
                for b in BookRepository(session).list_all()
            ]

    def get_book(self, book_id: int) -> BookResponse:
        with self._session_factory() as session:
            book = BookRepository(session).get(book_id)
            if book is None:
                raise NotFoundError("Book not found")
            return BookResponse.model_validate(book, from_attributes=True)

    def update_book(self, book_id: int, request: BookRequest) -> BookResponse:
        try:
            with self._session_factory() as session, session.begin():
                books = BookRepository(session)
                book = books.get(book_id)
                if book is None:
                    raise NotFoundError("Book not found")
                if MemberRepository(session).get(request.member_id) is None:
                    raise NotFoundError("Member not found")
                existing = books.get_by_isbn(request.isbn)
                if existing is not None and existing.id != book_id:
                    raise ConflictError("ISBN must be unique")
                for field, value in request.model_dump().items():
                    setattr(book, field, value)
                session.flush()  # surface constraint errors inside the try
                return BookResponse.model_validate(book, from_attributes=True)
        except IntegrityError as exc:
            raise translate_integrity_error(exc, NotFoundError("Member not found")) from exc

    def delete_book(self, book_id: int) -> None:
        with self._session_factory() as session, session.begin():
            books = BookRepository(session)
            book = books.get(book_id)
            if book is None:
                raise NotFoundError("Book not found")
            books.delete(book)