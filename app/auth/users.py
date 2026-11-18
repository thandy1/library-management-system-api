"""Predefined classroom identities and token-to-role mapping.

Request roles are separate from stored Member records: a "member" role is a
level of API access, not a row in the members table.
"""

from dataclasses import dataclass
from enum import StrEnum

from app.config import Settings


class Role(StrEnum):
    """Roles supported by the simple permission policy."""

    MEMBER = "member"
    ADMIN = "admin"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity and role established by a valid Bearer token."""

    username: str
    role: Role


def get_demo_token_for_role(role: Role, settings: Settings) -> str:
    """Return the configured token for one role."""
    if role is Role.MEMBER:
        return settings.demo_member_token
    return settings.demo_admin_token


def get_user_for_token(token: str, settings: Settings) -> AuthenticatedUser | None:
    """Map a configured token to its predefined user, or None if unknown."""
    member_token = get_demo_token_for_role(Role.MEMBER, settings)
    admin_token = get_demo_token_for_role(Role.ADMIN, settings)

    # An empty setting means "unconfigured" and must never match a credential.
    if member_token and token == member_token:
        return AuthenticatedUser(username="member", role=Role.MEMBER)
    if admin_token and token == admin_token:
        return AuthenticatedUser(username="admin", role=Role.ADMIN)
    return None