"""Helper Functions"""


from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.books import BookRequest, BookResponse
from app.schemas.members import MemberRequest, MemberResponse
from app.storage import books, members


def validate_book_exists(book_id: int) -> None:
    """Raise 404 if book doesn't exist."""
    if book_id not in books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )


def validate_isbn(request: BookRequest) -> None:
    """Raise 400 if the ISBN isn't unique."""
    if any(book.isbn == request.isbn for book in books.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISBN must be unique"
        )


def validate_email_unique(email: str, exclude_member_id: int | None = None) -> None:
    """Raise 400 if email is already in use by another member. 
    
    Args:
        email: Email address to check
        exclude_member_id: If provided, allow this member ID to keep the email 
                          (used when updating a member's own email)
    """
    for member in members.values():
        # During updates, allow the same member to keep their existing email.
        # Only reject if the email belongs to a DIFFERENT member.
        if member.email == email and member.id != exclude_member_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email must be unique"
            )


def validate_membership_id_unique(membership_id: str, exclude_member_id: int | None = None) -> None:
    """Raise 400 if membership_id is already in use."""
    for member in members.values():
        # During updates, allow the same member to keep their existing membership_id.
        # Only reject if the membership_id belongs to a DIFFERENT member.
        if member.membership_id == membership_id and member.id != exclude_member_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Membership ID must be unique"
            )


def validate_member_exists(member_id: int) -> None:
    """Raise 404 if member doesn't exist."""
    if member_id not in members:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

def validate_member_has_no_books(member_id: int) -> None:
    """Raise 409 if member has any associated books."""
    if any(book.member_id == member_id for book in books.values()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Delete the member's books before deleting the member"
            )
