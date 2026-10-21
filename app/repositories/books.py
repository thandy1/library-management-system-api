"""SQLAlchemy queries for books. Never commits; the service owns the transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book


class BookRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, book_id: int) -> Book | None:
        return self._session.get(Book, book_id)

    def list_all(self) -> list[Book]:
        return list(self._session.scalars(select(Book).order_by(Book.id)))

    def list_by_member(self, member_id: int) -> list[Book]:
        return list(
            self._session.scalars(
                select(Book).where(Book.member_id == member_id).order_by(Book.id)
            )
        )

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self._session.scalar(select(Book).where(Book.isbn == isbn))

    def member_has_books(self, member_id: int) -> bool:
        return (
            self._session.scalar(
                select(Book.id).where(Book.member_id == member_id).limit(1)
            )
            is not None
        )

    def add(self, book: Book) -> None:
        self._session.add(book)
        self._session.flush()

    def delete(self, book: Book) -> None:
        self._session.delete(book)
        self._session.flush()