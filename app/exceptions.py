"""Application-specific exceptions raised by services and mapped to HTTP in routers."""


class LibraryError(Exception):
    """Base class for expected application errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(LibraryError):
    """A requested Book or Member does not exist (HTTP 404)."""


class ConflictError(LibraryError):
    """The operation conflicts with existing data (HTTP 409)."""