# Library Management System API

A REST API for managing library books and members, built with FastAPI and Pydantic. 

## Overview

This API allows library staff to:
- Create, retrieve, update, and delete Book records
- Create, retrieve, update, and delete Member records
- Associate Books with Members (one Member can have many Books)
- Retrieve all Books borrowed by a specific Member
- Enforce business rules (unique ISBN/email/membership ID, prevent deletion of Members with active Books)

Data is stored in application memory for this milestone. Assignment 2 will add database persistence with SQLAlchemy.

## Tech Stack

- **FastAPI** - Modern Python web framework for building REST APIs
- **Pydantic** - Data validation using Python type hints
- **Uvicorn** - ASGI server to run the application
- **Python 3.10+**

## Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd library-management-system-api
git switch assignment-1
```

### 2. Install project dependencies   
```bash
uv sync
```

### 3. Running the project
```bash
uv run uvicorn app.main:app --reload
```

The development server will be available at `http://localhost:8000`.

Access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Requests

### Create a Member
```bash
POST http://localhost:8000/members
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "membership_id": "MEM001",
  "phone": "555-1234"
}
```

### Create a Book
```bash
POST http://localhost:8000/books
Content-Type: application/json

{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "isbn": "9780743273565",
  "published_year": 1925,
  "member_id": 1
}
```

### Get All Books
```bash
GET http://localhost:8000/books
```

### Get Books for a Member
```bash
GET http://localhost:8000/members/1/books
```

### Update a Book
```bash
PUT http://localhost:8000/books/1
Content-Type: application/json

{
  "title": "The Great Gatsby (Revised)",
  "author": "F. Scott Fitzgerald",
  "isbn": "9780743273565",
  "published_year": 1925,
  "member_id": 1
}
```

### Delete a Book
```bash
DELETE http://localhost:8000/books/1
```

### Delete a Member (only if no active books)
```bash
DELETE http://localhost:8000/members/1
```

## Project Structure

```
library-management-system-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and route registration
│   └── routes/
│       ├── __init__.py
│       ├── books.py         # Book CRUD endpoints
│       └── members.py       # Member CRUD endpoints
├── schemas/
│   ├── __init__.py
│   ├── books.py             # Book request/response schemas
│   └── members.py           # Member request/response schemas
├── helpers.py               # Validation and utility functions
├── storage.py               # In-memory data storage
├── pyproject.toml           # Project dependencies and metadata
├── uv.lock                  # Locked dependency versions
├── README.md                # This file
└── .gitignore
```