"""Test doubles for database-service unit tests. No PostgreSQL involved."""

from app.models.book import Book
from app.models.member import Member
from types import SimpleNamespace


class FakeUniqueViolation(Exception):
    """Stands in for psycopg's UniqueViolation error.

    Real psycopg errors expose `.diag.constraint_name`, the name of the
    database constraint that was violated. The service reads that name to
    decide which "must be unique" message to return.
    """

    def __init__(self, constraint_name: str) -> None:
        super().__init__(f"duplicate key violates constraint {constraint_name}")
        self.diag = SimpleNamespace(constraint_name=constraint_name)


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

    def member_has_books(self, member_id: int) -> bool:
        return any(b.member_id == member_id for b in self.books.values())

    def list_by_member(self, member_id: int) -> list[Book]:
        return [b for b in self.books.values() if b.member_id == member_id]

class FakeMemberStore:
    """Dict-backed stand-in with the same method names as MemberRepository."""

    def __init__(self, members: dict[int, Member] | None = None) -> None:
        self.members = members or {}
        self.add_calls = 0
        # Set to an exception to simulate the database rejecting the INSERT.
        self.raise_on_add: Exception | None = None

    def get(self, member_id: int) -> Member | None:
        return self.members.get(member_id)

    def list_all(self) -> list[Member]:
        return list(self.members.values())

    def get_by_email(self, email: str) -> Member | None:
        return next((m for m in self.members.values() if m.email == email), None)

    def get_by_membership_id(self, membership_id: str) -> Member | None:
        return next(
            (m for m in self.members.values() if m.membership_id == membership_id), None
        )

    def add(self, member: Member) -> None:
        if self.raise_on_add is not None:
            raise self.raise_on_add
        self.add_calls += 1
        member.id = max(self.members, default=0) + 1  # the DB would generate this
        self.members[member.id] = member

    def delete(self, member: Member) -> None:
        del self.members[member.id]