"""Test doubles for database-service unit tests. No PostgreSQL involved."""

from app.models.book import Book


class FakeTransaction:
    """Mimics `session.begin()`: records commit on clean exit, rollback on error."""

    def __init__(self, session: "FakeSession") -> None:
        self._session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self._session.committed = True
        else:
            self._session.rolled_back = True
        return False  # never swallow the exception


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)

    def flush(self) -> None:
        pass


class FakeSessionFactory:
    """Callable like a sessionmaker; keeps the last session for assertions."""

    def __init__(self) -> None:
        self.session = FakeSession()

    def __call__(self) -> FakeSession:
        self.session = FakeSession()
        return self.session


class FakeMemberRepository:
    """Only the lookup the Book service needs: does this member id exist?"""

    def __init__(self, member_ids: set[int]) -> None:
        self._ids = member_ids

    def get(self, member_id: int):
        return object() if member_id in self._ids else None


class FakeBookRepository:
    """Dict-backed stand-in with the same method names as BookRepository."""

    def __init__(self, books: dict[int, Book] | None = None) -> None:
        self.books = books or {}
        self.add_calls = 0

    def get(self, book_id: int) -> Book | None:
        return self.books.get(book_id)

    def list_all(self) -> list[Book]:
        return list(self.books.values())

    def get_by_isbn(self, isbn: str) -> Book | None:
        return next((b for b in self.books.values() if b.isbn == isbn), None)

    def add(self, book: Book) -> None:
        self.add_calls += 1
        book.id = max(self.books, default=0) + 1  # the DB would generate this
        self.books[book.id] = book

    def delete(self, book: Book) -> None:
        del self.books[book.id]