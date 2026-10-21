"""ORM model for the books table."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Book(Base):
    """A book that belongs to exactly one member."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    isbn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    published_year: Mapped[int]
    # RESTRICT makes the database itself refuse to delete a member who still has books.
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="RESTRICT"), nullable=False)

    member: Mapped["Member"] = relationship(back_populates="books")