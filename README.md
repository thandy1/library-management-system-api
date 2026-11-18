# Library Management System API

A FastAPI service for managing library books and members. Every book is borrowed by exactly one member. Data is stored in PostgreSQL through SQLAlchemy, with an in-memory backend available for quick local runs. Book and Member endpoints require a Bearer token, and writes are restricted to the administrator role.

## Prerequisites

- Python 3.11 or newer (developed on 3.13)
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL running locally (to run the API with the `database` backend)
- [Docker](https://docs.docker.com/get-docker/) running (required by the test suite; see [Testing](#testing))

## PostgreSQL setup (for running the API)

Create a database and a user. Choose your own password and do not commit it.

```bash
sudo -u postgres psql
```

```sql
CREATE USER library_user WITH PASSWORD 'choose-a-password';
CREATE DATABASE library OWNER library_user;
```

Tables are created automatically on startup. The tests do **not** use this database (see [Testing](#testing)).

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
| `DEMO_MEMBER_TOKEN` | Bearer token that authenticates as the **member** role (read-only) |
| `DEMO_ADMIN_TOKEN` | Bearer token that authenticates as the **administrator** role (read and write) |

The two tokens are fixed classroom demonstration values, not real credentials. Use different values for each role and replace them if you ever deploy this anywhere. `.env` is listed in `.gitignore`; never commit it. If `STORAGE_BACKEND=database` and `DATABASE_URL` is missing, the app refuses to start.

## Install and run

```bash
uv sync
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs (click **Authorize** and paste a token)
- ReDoc: http://127.0.0.1:8000/redoc

### Switching storage backends

Set `STORAGE_BACKEND` in `.env`, or override it for one run:

```bash
STORAGE_BACKEND=memory uv run uvicorn app.main:app --reload
```

- `database`: data persists in PostgreSQL across restarts.
- `memory`: starts with seed data (3 members, 4 books) and resets on every restart. Intended for quick demos only. Memory IDs are max+1; database IDs are never reused.

## Authentication and authorization

Send the token in the `Authorization` header: `Authorization: Bearer <token>`. Request roles come from the configured tokens and are separate from stored Member records.

| Role | Token setting | Access |
|---|---|---|
| member | `DEMO_MEMBER_TOKEN` | GET (read) operations |
| administrator | `DEMO_ADMIN_TOKEN` | GET, POST, PUT, DELETE |

| Situation | Response |
|---|---|
| Missing, malformed, or unknown token | `401` with `WWW-Authenticate: Bearer` |
| Member token on a POST, PUT, or DELETE | `403` |
| Root, health, `/docs`, `/redoc`, `/openapi.json` | Public, no token needed |

Token checks and role checks live in reusable FastAPI dependencies (`app/auth/`). Services contain only Library business rules and know nothing about tokens or roles.

## Endpoints

| Method | Path | Access | Success | Errors |
|---|---|---|---|---|
| POST | `/members` | admin | 201 | 401, 403, 409, 422 |
| GET | `/members` | any role | 200 | 401 |
| GET | `/members/{id}` | any role | 200 | 401, 404, 422 |
| PUT | `/members/{id}` | admin | 200 | 401, 403, 404, 409, 422 |
| DELETE | `/members/{id}` | admin | 204 | 401, 403, 404, 409, 422 |
| GET | `/members/{id}/books` | any role | 200 | 401, 404, 422 |
| POST | `/books` | admin | 201 | 401, 403, 404, 409, 422 |
| GET | `/books` | any role | 200 | 401 |
| GET | `/books/{id}` | any role | 200 | 401, 404, 422 |
| PUT | `/books/{id}` | admin | 200 | 401, 403, 404, 409, 422 |
| DELETE | `/books/{id}` | admin | 204 | 401, 403, 404, 422 |

## Sample requests

Replace the token values with the ones in your `.env`.

Read books as a member:

```bash
curl http://127.0.0.1:8000/books \
  -H "Authorization: Bearer <DEMO_MEMBER_TOKEN>"
```

Create a member as an administrator:

```bash
curl -X POST http://127.0.0.1:8000/members \
  -H "Authorization: Bearer <DEMO_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Ada Lovelace", "email": "ada@example.com", "membership_id": "M-1001", "phone": "555-123-4567"}'
```

Create a book borrowed by that member (use the `id` returned above as `member_id`):

```bash
curl -X POST http://127.0.0.1:8000/books \
  -H "Authorization: Bearer <DEMO_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441172719", "published_year": 1965, "member_id": 1}'
```

A member token on a write returns `403`; no token returns `401`:

```bash
curl -i -X DELETE http://127.0.0.1:8000/books/1 \
  -H "Authorization: Bearer <DEMO_MEMBER_TOKEN>"
```

## Testing

```bash
uv run pytest                      # full suite
uv run pytest tests/unit           # unit tests only
uv run pytest tests/integration    # repository and API integration tests
uv run pytest tests/conformance    # OpenAPI, Schemathesis, negative, and security contract tests
```

**Docker is required** for integration and conformance tests. They use [Testcontainers](https://testcontainers.com/) to start a disposable PostgreSQL container for the test session and remove it afterwards. Start Docker before running them; the first run pulls the PostgreSQL image. The tests never touch your local `library` database and do not need your `.env`.

| Folder | Responsibility |
|---|---|
| `tests/unit/schemas` | Pydantic rules for Book and Member (required fields, boundaries, email/phone, trimming, unknown fields) |
| `tests/unit/services` | Service rules for both backends; database services use test doubles, no PostgreSQL |
| `tests/unit/auth` | Token-to-role mapping and role-check dependencies |
| `tests/integration/repositories` | Repositories against real PostgreSQL: generated IDs, unique constraints, Member-to-Book foreign key |
| `tests/integration/routers` | Full workflows through `TestClient` on the database and in-memory backends |
| `tests/conformance` | `/openapi.json` validation, Schemathesis on safe GET operations, negative requests, 401/403 and security-scheme contract |

Each test gets independent state: the database is reset between tests, and the in-memory store is rebuilt per test.

## Business rules and behavior

- A book must reference an existing member (404 otherwise).
- ISBN, member email, and membership ID must each be unique (409 on duplicates).
- A member who still has books cannot be deleted (409). The database also enforces this with a foreign key (`ON DELETE RESTRICT`).
- Deleting a book or member returns 204 with no body.
- Unknown or invalid fields are rejected with 422.
- Rejected requests (401, 403, 404, 409, 422) never change stored data.

### Change from Assignment 1

A duplicate ISBN now returns **409 Conflict** (it was 400). On book update, checks run in the same order as create: book 404, member 404, ISBN 409.

## Design overview

- **Routers** are thin HTTP handlers. They call a service and return the result.
- **Auth dependencies** (`app/auth/`) authenticate the Bearer token and enforce roles at the HTTP boundary. Routers declare which role each operation needs.
- **Services** hold business rules and raise `NotFoundError` or `ConflictError`, never HTTP errors. `main.py` maps these to 404 and 409.
- **Service abstraction**: `BookService` and `MemberService` have database and in-memory implementations. The active one is created once at startup and injected with FastAPI dependencies.
- **Transactions**: each database operation uses one session and one transaction, which commits on success and rolls back on any exception. Repositories only query and flush.
- **Integrity**: database `IntegrityError`s are translated to `ConflictError` without leaking database details. The in-memory backend uses a lock around every operation.

## Project structure

```
library-management-system-api/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── users.py
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
├── tests/
│   ├── unit/
│   │   ├── auth/
│   │   │   ├── fakes.py
│   │   │   ├── test_dependencies.py
│   │   │   └── test_users.py
│   │   ├── schemas/
│   │   │   ├── test_books.py
│   │   │   └── test_members.py
│   │   └── services/
│   │       ├── books/
│   │       │   ├── test_database.py
│   │       │   └── test_in_memory.py
│   │       ├── members/
│   │       │   ├── test_database.py
│   │       │   └── test_in_memory.py
│   │       └── fakes.py
│   ├── integration/
│   │   ├── repositories/
│   │   │   ├── test_books.py
│   │   │   └── test_members.py
│   │   └── routers/
│   │       ├── database/
│   │       │   └── test_database_backend.py
│   │       ├── memory/
│   │       │   └── test_memory_backend.py
│   │       ├── conftest.py
│   │       ├── test_book_workflows.py
│   │       └── test_member_workflows.py
│   ├── conformance/
│   │   ├── conftest.py
│   │   ├── test_authentication_authorization_contract.py
│   │   ├── test_negative_requests.py
│   │   └── test_openapi_contract.py
│   └── conftest.py
├── docs/
│   └── notes.md
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```
(`__init__.py` files in test folders are omitted for brevity.)