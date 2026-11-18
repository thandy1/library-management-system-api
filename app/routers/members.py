"""HTTP endpoints for the Member resource."""

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_member_service
from app.schemas.books import BookResponse
from app.schemas.members import MemberRequest, MemberResponse
from app.services.members.base import MemberService
from app.auth.dependencies import (
    ADMIN_RESPONSES,
    AUTHENTICATED_RESPONSES,
    get_current_user,
    require_admin,
)

router = APIRouter(prefix="/members", tags=["Members"])


# POST /members (admin only)
@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new member",
    description="Create a member from a validated request body.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        409: {"description": "Email or membership ID already exists"}
    },
)
def create_member(
    request: MemberRequest,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Create a member from a validated JSON request body."""
    return service.create_member(request)


# GET /members (any valid token)
@router.get(
    "",
    response_model=list[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List all members",
    description="Return every member currently stored by the application.",
    dependencies=[Depends(get_current_user)],
    responses=AUTHENTICATED_RESPONSES,
)
def get_all_members(
    service: MemberService = Depends(get_member_service),
) -> list[MemberResponse]:
    """Return every stored member."""
    return service.list_members()


# GET /members/{member_id} (any valid token)
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Return one member",
    description="Retrieve one member by its identifier.",
    dependencies=[Depends(get_current_user)],
    responses={
        **AUTHENTICATED_RESPONSES,
        404: {"description": "Member not found"}
    },
)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Return the member with the requested ID."""
    return service.get_member(member_id)


# PUT /members/{member_id} (admin only)
@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing member",
    description="Update all editable fields of an existing member.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Member not found"},
        409: {"description": "Email or membership ID already exists"},
    },
)
def update_member(
    member_id: int,
    request: MemberRequest,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Update the editable fields of an existing member."""
    return service.update_member(member_id, request)


# DELETE /members/{member_id} (admin only)
@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Delete a member by its identifier.",
    dependencies=[Depends(require_admin)],
    responses={
        **ADMIN_RESPONSES,
        404: {"description": "Member not found"},
        409: {"description": "Member has active books and cannot be deleted"},
    },
)
def delete_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> Response:
    """Delete a member that has no associated books."""
    service.delete_member(member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# GET /members/{member_id}/books (any valid token)
@router.get(
    "/{member_id}/books",
    response_model=list[BookResponse],
    status_code=status.HTTP_200_OK,
    summary="Get member's books",
    description="Retrieve all books borrowed by a specific member.",
    dependencies=[Depends(get_current_user)],
    responses={
        **AUTHENTICATED_RESPONSES,
        404: {"description": "Member not found"}
    },
)
def get_member_books(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> list[BookResponse]:
    """Return all books associated with the requested member."""
    return service.list_member_books(member_id)