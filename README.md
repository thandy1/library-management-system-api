# Library Management System API

A FastAPI service for managing library books and members. Every book is borrowed by exactly one member. Data is stored in PostgreSQL through SQLAlchemy, with an in-memory backend available for quick local runs.

## Prerequisites

- Python 3.11 or newer (developed on 3.13)
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL running locally

## PostgreSQL setup

Create a database and a user. Choose your own password and do not commit it.

```bash
sudo -u postgres psql
```

```sql
CREATE USER library_user WITH PASSWORD 'choose-a-password';
CREATE DATABASE library OWNER library_user;
```

Tables are created automatically on startup.

## Configuration

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `STORAGE_BACKEND` | `database` (default) or `memory` |
| `DATABASE_URL` | Required when the backend is `database`. Format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>` |
| `DATABASE_ECHO_SQL` | Optional. `true` logs generated SQL |

`.env` is listed in `.gitignore`. Never commit real credentials. If `STORAGE_BACKEND=database` and `DATABASE_URL` is missing, the app refuses to start.

## Install and run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Switching storage backends

Set `STORAGE_BACKEND` in `.env`, or override it for one run:

```bash
STORAGE_BACKEND=memory uv run uvicorn app.main:app --reload
```

- `database`: data persists in PostgreSQL across restarts.
- `memory`: starts with seed data (3 members, 4 books) and resets on every restart. Intended for quick demos only. Memory IDs are max+1; database IDs are never reused.

## Endpoints

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/members` | 201 | 409, 422 |
| GET | `/members` | 200 | |
| GET | `/members/{id}` | 200 | 404 |
| PUT | `/members/{id}` | 200 | 404, 409, 422 |
| DELETE | `/members/{id}` | 204 | 404, 409 |
| GET | `/members/{id}/books` | 200 | 404 |
| POST | `/books` | 201 | 404, 409, 422 |
| GET | `/books` | 200 | |
| GET | `/books/{id}` | 200 | 404 |
| PUT | `/books/{id}` | 200 | 404, 409, 422 |
| DELETE | `/books/{id}` | 204 | 404 |

## Sample requests

Create a member:

```bash
curl -X POST http://127.0.0.1:8000/members \
  -H "Content-Type: application/json" \
  -d '{"name": "Ada Lovelace", "email": "ada@example.com", "membership_id": "M-1001", "phone": "555-123-4567"}'
```

Create a book borrowed by that member (use the `id` returned above as `member_id`):

```bash
curl -X POST http://127.0.0.1:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441172719", "published_year": 1965, "member_id": 1}'
```

## Business rules and behavior

- A book must reference an existing member (404 otherwise).
- ISBN, member email, and membership ID must each be unique (409 on duplicates).
- A member who still has books cannot be deleted (409). The database also enforces this with a foreign key (`ON DELETE RESTRICT`).
- Deleting a book or member returns 204 with no body.
- Unknown or invalid fields are rejected with 422.

### Change from Assignment 1

A duplicate ISBN now returns **409 Conflict** (it was 400). On book update, checks run in the same order as create: book 404, member 404, ISBN 409.

## Design overview

- **Routers** are thin HTTP handlers. They call a service and return the result.
- **Services** hold business rules and raise `NotFoundError` or `ConflictError`, never HTTP errors. `main.py` maps these to 404 and 409.
- **Service abstraction**: `BookService` and `MemberService` have database and in-memory implementations. The active one is created once at startup and injected with FastAPI dependencies.
- **Transactions**: each database operation uses one session and one transaction, which commits on success and rolls back on any exception. Repositories only query and flush.
- **Integrity**: database `IntegrityError`s are translated to `ConflictError` without leaking database details. The in-memory backend uses a lock around every operation.

## Project structure

```
library-management-system-api/
├── app/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── book.py
│   │   └── member.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── services/
│   │   ├── books/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   └── in_memory.py
│   │   ├── members/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   └── in_memory.py
│   │   ├── __init__.py
│   │   ├── in_memory_store.py
│   │   └── integrity.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── __init__.py
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── main.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```