"""Unit tests for Member schemas. No FastAPI, database, or Docker involved."""

import pytest
from pydantic import ValidationError

from app.schemas.members import MemberRequest, MemberResponse


def valid_member(**overrides) -> dict:
    """Build a valid payload; tests override only the field under test."""
    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "membership_id": "M-001",
        "phone": "555-123-4567",
    }
    return {**data, **overrides}


def error_fields(exc_info: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    """Return the field names that failed validation."""
    return {str(e["loc"][0]) for e in exc_info.value.errors()}


def test_valid_member_request_is_accepted():
    assert MemberRequest(**valid_member()).name == "Ada Lovelace"


@pytest.mark.parametrize("field", ["name", "email", "membership_id", "phone"])
def test_missing_required_field_is_rejected(field):
    data = valid_member()
    del data[field]
    with pytest.raises(ValidationError) as exc_info:
        MemberRequest(**data)
    assert error_fields(exc_info) == {field}


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError) as exc_info:
        MemberRequest(**valid_member(role="admin"))
    assert error_fields(exc_info) == {"role"}


def test_whitespace_is_trimmed():
    member = MemberRequest(**valid_member(name="  Ada  ", membership_id=" M-001 "))
    assert member.name == "Ada"
    assert member.membership_id == "M-001"


@pytest.mark.parametrize("value", ["", "   ", "x" * 121])
def test_invalid_name_length_is_rejected(value):
    with pytest.raises(ValidationError) as exc_info:
        MemberRequest(**valid_member(name=value))
    assert error_fields(exc_info) == {"name"}


@pytest.mark.parametrize("value", ["x", "x" * 120])
def test_name_length_boundaries_are_accepted(value):
    assert MemberRequest(**valid_member(name=value))


@pytest.mark.parametrize("email", ["not-an-email", "missing@tld", "@example.com", ""])
def test_invalid_email_is_rejected(email):
    with pytest.raises(ValidationError) as exc_info:
        MemberRequest(**valid_member(email=email))
    assert error_fields(exc_info) == {"email"}


@pytest.mark.parametrize(
    "phone",
    ["5551234567", "555-1234-567", "555-123-456", "555-123-45678", "abc-def-ghij", ""],
)
def test_invalid_phone_format_is_rejected(phone):
    with pytest.raises(ValidationError) as exc_info:
        MemberRequest(**valid_member(phone=phone))
    assert error_fields(exc_info) == {"phone"}


def test_member_response_requires_positive_id():
    assert MemberResponse(**valid_member(id=1)).id == 1
    with pytest.raises(ValidationError):
        MemberResponse(**valid_member(id=0))