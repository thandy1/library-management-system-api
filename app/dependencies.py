"""FastAPI dependencies that provide the active service implementations."""

from fastapi import Request

from app.services.books.base import BookService
from app.services.members.base import MemberService
from app.config import Settings


def get_book_service(request: Request) -> BookService:
    """Return the BookService created at application startup."""
    return request.app.state.book_service


def get_member_service(request: Request) -> MemberService:
    """Return the MemberService created at application startup."""
    return request.app.state.member_service

def get_settings(request: Request) -> Settings:
    """Return the validated settings created during application startup."""
    return request.app.state.settings