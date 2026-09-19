# Library Management System API

A REST API for managing library books and members, built with FastAPI and Pydantic. This is Assignment 1 for SDEV 3310 (API Design and Development).

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

TBD
