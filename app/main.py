"""FastAPI application for the Library Management System API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  (registers ORM models on Base.metadata)
from app.config import Settings, StorageBackend
from app.database.session import create_database
from app.exceptions import ConflictError, NotFoundError
from app.models import Base
from app.routers.books import router as books_router
from app.routers.members import router as members_router
from app.services.books.database import DatabaseBookService
from app.services.books.in_memory import InMemoryBookService
from app.services.in_memory_store import InMemoryStore
from app.services.members.database import DatabaseMemberService
from app.services.members.in_memory import InMemoryMemberService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.settings = settings  # lets dependencies read the same Settings instance
    engine = None

    if settings.storage_backend == StorageBackend.DATABASE:
        infra = create_database(settings)
        engine = infra.engine
        Base.metadata.create_all(engine)
        app.state.book_service = DatabaseBookService(infra.session_factory)
        app.state.member_service = DatabaseMemberService(infra.session_factory)
    else:
        store = InMemoryStore()
        app.state.book_service = InMemoryBookService(store)
        app.state.member_service = InMemoryMemberService(store)

    yield

    if engine is not None:
        engine.dispose()


tags_metadata = [
    {"name": "Books", "description": "Operations for managing library books"},
    {"name": "Members", "description": "Operations for managing library members"},
]

app = FastAPI(
    title="Library Management System API",
    description="Manages library books and members, tracks borrowing relationships, "
                "and enforces unique constraints and business rules.",
    version="0.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.message})


# Public endpoints: no auth dependency, so no token is required.
@app.get(
    "/",
    tags=["Public"],
    summary="API root",
    description="Return basic API information. No authentication required.",
)
def read_root() -> dict[str, str]:
    """Identify the API and point callers to the documentation."""
    return {"name": "Library Management System API", "docs": "/docs"}


@app.get(
    "/health",
    tags=["Public"],
    summary="Health check",
    description="Report that the API process is running. No authentication required.",
)
def read_health() -> dict[str, str]:
    """Report liveness only; it does not query the database."""
    return {"status": "ok"}


app.include_router(books_router)
app.include_router(members_router)