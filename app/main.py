"""FastAPI application for the Library Management System API."""


from fastapi import FastAPI


app = FastAPI(
    title="Library Management System API",
    description="Manages library books and members, tracks borrowing relationships, "
                "and enforces unique constraints and business rules.",
    version="0.1.0"
)