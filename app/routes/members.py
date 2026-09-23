"""HTTP endpoints for the Member resource."""


from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.members import MemberRequest, MemberResponse
from app.schemas.books import BookResponse
from app.storage import books, members
from app.helpers import validate_isbn, validate_book_exists, validate_email_unique, validate_membership_id_unique, validate_member_exists, validate_member_has_no_books


router = APIRouter(prefix="/members", tags=["Members"])


# Create a new member.
@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new member",
    description="Create a member from a validated request body."
)
def create_member(request: MemberRequest) -> MemberResponse:
    """Create a member from a validated JSON request body."""
    validate_email_unique(request.email)
    validate_membership_id_unique(request.membership_id)
    # GENERATE NEW ID AND CREATE NEW ENTRY
    new_member_id = max(members.keys(), default=0) + 1 
    new_member = MemberResponse(id=new_member_id, **request.model_dump())
    members[new_member_id] = new_member
    return new_member


# Retrieve all members.
@router.get(
    "",
    response_model=list[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List all members",
    description="Return every member currently stored by the application."
)
def get_all_members() -> list[MemberResponse]:
    """Return every member currently stored in memory."""
    return list(members.values())


# Retrieve one member by its identifier.
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Return one member",
    description="Retrieve one member by its identifier.",
    responses={404: {"description": "Member not found"}}
)
def get_member(member_id: int) -> MemberResponse:
    """Return the member with the requested ID."""
    validate_member_exists(member_id)
    return members[member_id]


# Update an existing member.
@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing member",
    description="Update all editable fields of an existing member.",
    responses={404: {"description": "Member not found"}}
)
def update_member(member_id: int, request: MemberRequest) -> MemberResponse:
    """Update the editable fields of an existing member."""
    validate_member_exists(member_id)
    validate_email_unique(request.email, exclude_member_id=member_id)
    validate_membership_id_unique(request.membership_id, exclude_member_id=member_id)
    updated_member = MemberResponse(
        id=member_id,
        **request.model_dump()
    )
    members[member_id] = updated_member
    return updated_member


# Delete an existing member.
@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Delete a member from the in-memory storage.",
    responses={
        404: {"description": "Member not found"},
        409: {"description": "Member has active books and cannot be deleted"}
    }
)
def delete_member(member_id: int) -> None:
    """Delete a member from the in-memory storage."""
    validate_member_exists(member_id)
    validate_member_has_no_books(member_id)
    members.pop(member_id)


# Retrieve books for a member.
@router.get(
    "/{member_id}/books",
    response_model=list[BookResponse],
    status_code=status.HTTP_200_OK,
    summary="Get member's books",
    description="Retrieve all books borrowed by a specific member."
)
def get_member_books(member_id: int) -> list[BookResponse]:
    """Return all books associated with the requested member."""
    validate_member_exists(member_id)
    # Return all books where member_id matches
    return [book for book in books.values() if book.member_id == member_id]