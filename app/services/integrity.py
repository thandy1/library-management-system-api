"""Translate database integrity errors into safe application exceptions."""

from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, LibraryError

# Constraint names PostgreSQL generated (seen in \d output).
_UNIQUE_MESSAGES = {
    "books_isbn_key": "ISBN must be unique",
    "members_email_key": "Email must be unique",
    "members_membership_id_key": "Membership ID must be unique",
}


def translate_integrity_error(exc: IntegrityError, fk_error: LibraryError) -> LibraryError:
    """Map a violated constraint to a ConflictError (or fk_error for the foreign key)."""
    constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    if constraint in _UNIQUE_MESSAGES:
        return ConflictError(_UNIQUE_MESSAGES[constraint])
    if constraint == "books_member_id_fkey":
        # Meaning depends on the operation, so the caller supplies it.
        return fk_error
    return ConflictError("The request conflicts with existing data")