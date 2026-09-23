"""FastAPI application for the Library Management System API."""


from fastapi import FastAPI
from app.routes.books import router as books_router
from app.routes.members import router as members_router


app = FastAPI(
    title="Library Management System API",
    description="Manages library books and members, tracks borrowing relationships, "
                "and enforces unique constraints and business rules.",
    version="0.1.0"
)

app.include_router(books_router)
app.include_router(members_router)


