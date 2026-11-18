"""Unit tests for the authentication and role-check dependencies.

The dependency functions are called directly with hand-built inputs, so these
tests cover the decision logic. Full HTTP behavior is tested in conformance.
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import get_current_user, require_admin
from app.auth.users import AuthenticatedUser, Role
from tests.unit.auth.fakes import make_settings

MEMBER_TOKEN = "unit-member-token"
ADMIN_TOKEN = "unit-admin-token"


@pytest.fixture
def settings():
    return make_settings()


def bearer(token: str, scheme: str = "Bearer") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)


def test_get_current_user_returns_member_for_member_token(settings):
    user = get_current_user(bearer(MEMBER_TOKEN), settings)
    assert user.role is Role.MEMBER


def test_get_current_user_returns_admin_for_admin_token(settings):
    user = get_current_user(bearer(ADMIN_TOKEN), settings)
    assert user.role is Role.ADMIN


def test_get_current_user_accepts_lowercase_bearer_scheme(settings):
    user = get_current_user(bearer(MEMBER_TOKEN, scheme="bearer"), settings)
    assert user.role is Role.MEMBER


@pytest.mark.parametrize(
    "credentials",
    [
        None,                                   # no Authorization header
        bearer(MEMBER_TOKEN, scheme="Basic"),   # wrong scheme
        bearer("not-a-real-token"),             # unknown token
        bearer(""),                             # empty token
    ],
    ids=["missing", "wrong-scheme", "unknown-token", "empty-token"],
)
def test_get_current_user_rejects_bad_credentials_with_401(credentials, settings):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials, settings)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_require_admin_allows_admin():
    admin = AuthenticatedUser(username="admin", role=Role.ADMIN)
    assert require_admin(admin) is admin


def test_require_admin_rejects_member_with_403():
    member = AuthenticatedUser(username="member", role=Role.MEMBER)
    with pytest.raises(HTTPException) as exc_info:
        require_admin(member)
    assert exc_info.value.status_code == 403