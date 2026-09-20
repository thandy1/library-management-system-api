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
- **Python 3.9+**

## Installation

### 1. Clone the repository
Run these commands in your terminal:
```bash
git clone <your-repo-url>
cd library-management-system-api
git switch assignment-<assignment-number>
```

### 2. Install project dependencies   
From the `library-management-system-api` folder, run:
```bash
uv sync
```
This installs dependencies from `uv.lock`. (Alternatively, `uv run` will automatically install dependencies when you start the server.)

### 3. Running the project
Start the API server:
```bash
uv run uvicorn app.main:app --reload
```

The development server will be available at `http://localhost:8000`.

Access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Test all endpoints and business logic directly in Swagger UI.