"""FastAPI dependencies that authenticate Bearer tokens and enforce roles."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.users import AuthenticatedUser, Role, get_user_for_token
from app.config import Settings
from app.dependencies import get_settings

ResponseDocs = dict[int | str, dict[str, Any]]

# auto_error=False lets us return our own 401 (with WWW-Authenticate) instead
# of FastAPI's default. The scheme also publishes Bearer security to OpenAPI,
# which gives Swagger UI its Authorize button.
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuthentication")
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]

# Reused in router decorators so OpenAPI documents what the code returns.
UNAUTHORIZED_RESPONSE: dict[str, Any] = {
    "description": "Missing or invalid Bearer token",
    "headers": {
        "WWW-Authenticate": {
            "description": "Authentication scheme required by this endpoint.",
            "schema": {"type": "string"},
        }
    },
}
FORBIDDEN_RESPONSE: dict[str, Any] = {"description": "Administrator role required"}
AUTHENTICATED_RESPONSES: ResponseDocs = {401: UNAUTHORIZED_RESPONSE}
ADMIN_RESPONSES: ResponseDocs = {401: UNAUTHORIZED_RESPONSE, 403: FORBIDDEN_RESPONSE}

AppSettings = Annotated[Settings, Depends(get_settings)]


def unauthenticated() -> HTTPException:
    """Build the standard 401 for absent or invalid credentials."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: BearerCredentials, settings: AppSettings
) -> AuthenticatedUser:
    """Authenticate the Bearer token and return its predefined user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthenticated()
    user = get_user_for_token(credentials.credentials, settings)
    if user is None:
        raise unauthenticated()
    return user


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> AuthenticatedUser:
    """Allow only administrators to continue to a write route."""
    if current_user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )
    return current_user


AdminUser = Annotated[AuthenticatedUser, Depends(require_admin)]