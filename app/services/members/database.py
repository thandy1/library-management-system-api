"""Database-backed Member service. Owns one transaction per operation."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import ConflictError, NotFoundError
from app.models.member import Member
from app.repositories.books import BookRepository
from app.repositories.members import MemberRepository
from app.schemas.books import BookResponse
from app.schemas.members import MemberRequest, MemberResponse
from app.services.integrity import translate_integrity_error
from app.services.members.base import MemberService

_HAS_BOOKS = "Delete the member's books before deleting the member"


class DatabaseMemberService(MemberService):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _check_unique(
        members: MemberRepository, request: MemberRequest, exclude_id: int | None = None
    ) -> None:
        by_email = members.get_by_email(request.email)
        if by_email is not None and by_email.id != exclude_id:
            raise ConflictError("Email must be unique")
        by_mid = members.get_by_membership_id(request.membership_id)
        if by_mid is not None and by_mid.id != exclude_id:
            raise ConflictError("Membership ID must be unique")

    def create_member(self, request: MemberRequest) -> MemberResponse:
        try:
            with self._session_factory() as session, session.begin():
                members = MemberRepository(session)
                self._check_unique(members, request)
                member = Member(**request.model_dump())
                members.add(member)
                return MemberResponse.model_validate(member, from_attributes=True)
        except IntegrityError as exc:
            raise translate_integrity_error(exc, ConflictError(_HAS_BOOKS)) from exc

    def list_members(self) -> list[MemberResponse]:
        with self._session_factory() as session:
            return [
                MemberResponse.model_validate(m, from_attributes=True)
                for m in MemberRepository(session).list_all()
            ]

    def get_member(self, member_id: int) -> MemberResponse:
        with self._session_factory() as session:
            member = MemberRepository(session).get(member_id)
            if member is None:
                raise NotFoundError("Member not found")
            return MemberResponse.model_validate(member, from_attributes=True)

    def update_member(self, member_id: int, request: MemberRequest) -> MemberResponse:
        try:
            with self._session_factory() as session, session.begin():
                members = MemberRepository(session)
                member = members.get(member_id)
                if member is None:
                    raise NotFoundError("Member not found")
                self._check_unique(members, request, exclude_id=member_id)
                for field, value in request.model_dump().items():
                    setattr(member, field, value)
                session.flush()
                return MemberResponse.model_validate(member, from_attributes=True)
        except IntegrityError as exc:
            raise translate_integrity_error(exc, ConflictError(_HAS_BOOKS)) from exc

    def delete_member(self, member_id: int) -> None:
        try:
            with self._session_factory() as session, session.begin():
                members = MemberRepository(session)
                member = members.get(member_id)
                if member is None:
                    raise NotFoundError("Member not found")
                if BookRepository(session).member_has_books(member_id):
                    raise ConflictError(_HAS_BOOKS)
                members.delete(member)
        except IntegrityError as exc:  # FK RESTRICT if a book was added concurrently
            raise translate_integrity_error(exc, ConflictError(_HAS_BOOKS)) from exc

    def list_member_books(self, member_id: int) -> list[BookResponse]:
        with self._session_factory() as session:
            if MemberRepository(session).get(member_id) is None:
                raise NotFoundError("Member not found")
            return [
                BookResponse.model_validate(b, from_attributes=True)
                for b in BookRepository(session).list_by_member(member_id)
            ]