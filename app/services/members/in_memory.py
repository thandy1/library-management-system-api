"""In-memory Member service."""

from app.exceptions import ConflictError, NotFoundError
from app.schemas.books import BookResponse
from app.schemas.members import MemberRequest, MemberResponse
from app.services.in_memory_store import InMemoryStore
from app.services.members.base import MemberService


class InMemoryMemberService(MemberService):
    """Member operations backed by process-local dictionaries."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def _require_unique(
        self, request: MemberRequest, exclude_member_id: int | None = None
    ) -> None:
        # A member may keep their own email/membership ID, so skip their own record.
        for member in self._store.members.values():
            if member.id == exclude_member_id:
                continue
            if member.email == request.email:
                raise ConflictError("Email must be unique")
            if member.membership_id == request.membership_id:
                raise ConflictError("Membership ID must be unique")

    def create_member(self, request: MemberRequest) -> MemberResponse:
        with self._store.lock:
            self._require_unique(request)
            new_id = max(self._store.members, default=0) + 1
            member = MemberResponse(id=new_id, **request.model_dump())
            self._store.members[new_id] = member
            return member

    def list_members(self) -> list[MemberResponse]:
        with self._store.lock:
            return list(self._store.members.values())

    def get_member(self, member_id: int) -> MemberResponse:
        with self._store.lock:
            member = self._store.members.get(member_id)
            if member is None:
                raise NotFoundError("Member not found")
            return member

    def update_member(self, member_id: int, request: MemberRequest) -> MemberResponse:
        with self._store.lock:
            self.get_member(member_id)
            self._require_unique(request, exclude_member_id=member_id)
            updated = MemberResponse(id=member_id, **request.model_dump())
            self._store.members[member_id] = updated
            return updated

    def delete_member(self, member_id: int) -> None:
        with self._store.lock:
            self.get_member(member_id)
            if any(b.member_id == member_id for b in self._store.books.values()):
                raise ConflictError("Delete the member's books before deleting the member")
            del self._store.members[member_id]

    def list_member_books(self, member_id: int) -> list[BookResponse]:
        with self._store.lock:
            self.get_member(member_id)
            return [b for b in self._store.books.values() if b.member_id == member_id]