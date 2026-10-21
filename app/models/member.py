"""ORM model for the members table."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Member(Base):
    """A library member who can have many books."""

    __tablename__ = "members"

    # PostgreSQL generates the id automatically.
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    membership_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)

    # The relationship lets Python navigate member.books. The foreign key is
    # stored on Book because Book is the "many" side of the relationship.
    books: Mapped[list["Book"]] = relationship(back_populates="member")