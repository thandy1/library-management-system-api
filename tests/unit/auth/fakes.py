"""Minimal stand-in for Settings so auth unit tests need no env or .env file."""

from typing import cast

from app.config import Settings


class FakeAuthSettings:
    """Holds only the two token settings the auth code reads."""

    def __init__(self, demo_member_token: str, demo_admin_token: str) -> None:
        self.demo_member_token = demo_member_token
        self.demo_admin_token = demo_admin_token


def make_settings(member_token: str = "unit-member-token",
                  admin_token: str = "unit-admin-token") -> Settings:
    # cast tells the type checker to treat the fake as Settings.
    return cast(Settings, FakeAuthSettings(member_token, admin_token))