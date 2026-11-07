# Curio

Curio is an AI-powered developer tool discovery and repository intelligence platform. It collects open-source repositories from GitHub, ranks them using a custom multi-factor scoring engine, identifies trending projects, and provides AI-powered explanations and conversational interactions.

---

## Architecture Overview

Curio is built as a modular monolithic system:
- **Backend:** Python 3.12+, FastAPI (ASGI), Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Uvicorn.
- **Package & Environment Management:** `uv` (fast Rust-based package installer and resolver).
- **Database:** PostgreSQL 16 (relational persistence with async connection pooling via `asyncpg`).
- **Containerization:** Docker & Docker Compose (`db` + `backend` services).
- **Quality & Standards:** Ruff (formatting and linting), Mypy (strict static typing), Pytest (unit and integration tests), Pre-commit.

---

## Project Structure

```text
curio/
│
├── .gitignore                    # Comprehensive root git exclusions
├── .gitattributes                # LF line ending normalization
├── .editorconfig                 # Multi-editor indentation and charset standards
├── .env.example                  # Environment configuration template
├── docker-compose.yml            # Multi-container orchestration (db + backend)
├── README.md                     # Project documentation
│
├── backend/                      # Backend application root
│   ├── pyproject.toml            # Dependencies and tool configurations
│   ├── Dockerfile                # Multi-stage production container build
│   ├── .dockerignore             # Docker build context exclusions
│   ├── .pre-commit-config.yaml   # Pre-commit hooks for Ruff and code checks
│   ├── alembic.ini               # Alembic database migration config
│   │
│   ├── alembic/                  # Database migration scripts
│   │   ├── env.py                # Async Alembic runner
│   │   ├── script.py.mako        # Migration template
│   │   └── versions/             # Migration revision versions
│   │
│   ├── app/                      # Application source code
│   │   ├── main.py               # FastAPI entrypoint, lifespan, CORS, middleware
│   │   ├── core/                 # Config, logging, exceptions
│   │   ├── db/                   # Async engine, session, DeclarativeBase
│   │   ├── api/v1/               # API routes and endpoints
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── models/               # SQLAlchemy ORM models (Stage 3+)
│   │   ├── services/             # Domain business logic (Stage 2+)
│   │   ├── integrations/         # GitHub & OpenAI clients (Stage 2 & 6)
│   │   └── utils/                # Shared utilities
│   │
│   └── tests/                    # Automated test suite
│       ├── conftest.py           # Async test fixtures
│       ├── test_health.py        # Health and readiness tests
│       └── test_config.py        # Configuration and error tests
│
└── frontend/                     # React + TypeScript frontend (Stage 1.5/Stage 2)
```

---

## Getting Started

### Prerequisites
- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (v0.13+)
- [Docker Desktop](https://www.docker.com/) (for containerized PostgreSQL and full stack)
- [Git](https://git-scm.com/)

---

### Option 1: Local Development with `uv`

1. **Clone the repository and enter workspace:**
   ```bash
   cd D:\Curio
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

3. **Start PostgreSQL via Docker:**
   ```bash
   docker compose up -d db
   ```

4. **Initialize Python environment and install dependencies:**
   ```bash
   cd backend
   uv venv --python 3.12
   uv sync --extra dev
   ```

5. **Start the FastAPI backend with live reload:**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access Interactive API Documentation:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - Liveness Health Check: [http://localhost:8000/health](http://localhost:8000/health)
   - Readiness Health Check: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)

---

### Option 2: Full Stack via Docker Compose

To run both PostgreSQL and the FastAPI backend in Docker containers:

```bash
cd D:\Curio
docker compose up -d --build
```

View container logs:
```bash
docker compose logs -f backend
```

Stop containers:
```bash
docker compose down
```

---

## Code Quality & Testing

All testing and linting tools run through `uv`:

### Run Automated Tests
```bash
cd backend
uv run pytest --cov=app --cov-report=term-missing
```

### Static Type Checking
```bash
cd backend
uv run mypy app
```

### Code Formatting and Linting
```bash
cd backend
uv run ruff check app tests
uv run ruff format --check app tests
```

To automatically format code:
```bash
uv run ruff format app tests
uv run ruff check --fix app tests
```

### Pre-commit Hooks
Install git hooks to run formatting and linting automatically before each commit:
```bash
cd backend
uv run pre-commit install
```
