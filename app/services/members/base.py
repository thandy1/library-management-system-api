"""Abstract Member service: the operations routers depend on."""

from abc import ABC, abstractmethod

from app.schemas.books import BookResponse
from app.schemas.members import MemberRequest, MemberResponse


class MemberService(ABC):
    """Contract that every Member storage implementation must follow."""

    @abstractmethod
    def create_member(self, request: MemberRequest) -> MemberResponse: ...

    @abstractmethod
    def list_members(self) -> list[MemberResponse]: ...

    @abstractmethod
    def get_member(self, member_id: int) -> MemberResponse: ...

    @abstractmethod
    def update_member(self, member_id: int, request: MemberRequest) -> MemberResponse: ...

    @abstractmethod
    def delete_member(self, member_id: int) -> None: ...

    @abstractmethod
    def list_member_books(self, member_id: int) -> list[BookResponse]: ...