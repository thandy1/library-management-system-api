"""SQLAlchemy queries for members. Never commits; the service owns the transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.member import Member


class MemberRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, member_id: int) -> Member | None:
        return self._session.get(Member, member_id)

    def list_all(self) -> list[Member]:
        return list(self._session.scalars(select(Member).order_by(Member.id)))

    def get_by_email(self, email: str) -> Member | None:
        return self._session.scalar(select(Member).where(Member.email == email))

    def get_by_membership_id(self, membership_id: str) -> Member | None:
        return self._session.scalar(
            select(Member).where(Member.membership_id == membership_id)
        )

    def add(self, member: Member) -> None:
        self._session.add(member)
        self._session.flush()  # sends the INSERT so PostgreSQL generates member.id

    def delete(self, member: Member) -> None:
        self._session.delete(member)
        self._session.flush()