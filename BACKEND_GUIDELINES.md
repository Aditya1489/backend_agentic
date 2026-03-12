# Backend Development Guidelines

This document outlines the architectural patterns and coding standards for the Python/FastAPI backend.

## 1. Architectural Patterns

We follow a clean separation of concerns using the **Router -> Service -> Repository** pattern.

### Repository Layer (`app/repositories/`)
- **Purpose**: Handles all direct database operations (SQLAlchemy queries).
- **Rule**: Only repository files should interact with `db: Session`.
- **Example**: `UserRepository` handles fetching, creating, and updating user records.

### Service Layer (`app/services/`)
- **Purpose**: Contains business logic, validation, and orchestration.
- **Rule**: Routers should call services, and services should call repositories.
- **Validation**: Complex validation and business rules (e.g., checking password strength, processing payments) belong here.

### API Layer (`app/api/`)
- **Purpose**: Defines endpoints, handles request parsing, and returns responses.
- **Rule**: Routers should be "thin". They should only handle HTTP-related logic (parsing body, headers, status codes) and delegate everything else to services.

---

## 2. Coding Standards

### No Hardcoded Values
- **Rule**: Sensitive information (passwords, keys) and environment-specific settings (database URLs, ports) MUST be stored in the `.env` file.
- **Access**: Access these values only through the `app.core.config` module.
- **Example**: Use `config.DATABASE_URL` instead of a literal string.

### Absolute Imports
- **Rule**: Always use absolute imports starting from the `app` package.
- **Example**: `from app.models.user import User` instead of `from ..models.user import User`.

### Typing
- **Rule**: Use Python type hints for all function arguments and return values.
- **Pydantic**: Use Pydantic schemas (in `app/schemas/`) for data validation and serialization in API requests and responses.

### Environmental Stability
- **Rule**: Prefer pure Python or widely compatible libraries (like `sha256_crypt`) over those requiring complex binary compilations (like `bcrypt`) if the target environment is experimental or restricted.

---

## 3. Database Management
- **Initialization**: Use `app.db.init_db.py` for setting up tables and initial seeding.
- **Seeding**: Always use `INITIAL_USER_EMAIL` and `INITIAL_USER_PASSWORD` from `.env` for the seed user.
