"""Unit tests for token-to-role mapping (no HTTP, no database)."""

import pytest

from app.auth.users import AuthenticatedUser, Role, get_demo_token_for_role, get_user_for_token
from tests.unit.auth.fakes import make_settings

MEMBER_TOKEN = "unit-member-token"
ADMIN_TOKEN = "unit-admin-token"


def test_get_demo_token_for_member_role_returns_member_token():
    assert get_demo_token_for_role(Role.MEMBER, make_settings()) == MEMBER_TOKEN


def test_get_demo_token_for_admin_role_returns_admin_token():
    assert get_demo_token_for_role(Role.ADMIN, make_settings()) == ADMIN_TOKEN


def test_member_token_maps_to_member_user():
    user = get_user_for_token(MEMBER_TOKEN, make_settings())
    assert user == AuthenticatedUser(username="member", role=Role.MEMBER)


def test_admin_token_maps_to_admin_user():
    user = get_user_for_token(ADMIN_TOKEN, make_settings())
    assert user == AuthenticatedUser(username="admin", role=Role.ADMIN)


@pytest.mark.parametrize("token", ["wrong-token", "UNIT-MEMBER-TOKEN", " unit-member-token", ""])
def test_unknown_token_maps_to_no_user(token):
    assert get_user_for_token(token, make_settings()) is None


def test_empty_token_is_rejected_when_roles_are_unconfigured():
    # Unconfigured roles default to "", so "" must never authenticate.
    settings = make_settings(member_token="", admin_token="")
    assert get_user_for_token("", settings) is None


def test_unconfigured_admin_role_does_not_block_configured_member_role():
    settings = make_settings(admin_token="")
    user = get_user_for_token(MEMBER_TOKEN, settings)
    assert user is not None
    assert user.role is Role.MEMBER
    assert get_user_for_token("", settings) is None