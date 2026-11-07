# 4. Stage 1 — Project Foundation

## 4.1 Objective

Establish the backend development environment, project structure and initial FastAPI application.

This stage also includes learning the LLM fundamentals required for later AI implementation.

No production repository ingestion or AI analysis functionality is required at this stage.

## 4.2 Functional Requirements

**FR-001: Backend Initialization**

The system shall provide a working FastAPI backend application.

**FR-002: Project Structure**

The backend shall follow a modular structure separating:

- API routes.
- Business logic.
- Database models.
- Request and response schemas.
- External integrations.
- Shared configuration.

**FR-003: Health Check**

The application shall expose a health-check endpoint.

`GET /health`

Expected response:

```json
{
  "status": "healthy"
}
```

**FR-004: API Documentation**

FastAPI shall automatically expose OpenAPI documentation through Swagger UI.

**FR-005: Configuration Management**

The application shall load external configuration and credentials through environment variables.

## 4.3 Initial Backend Structure

```text
curio/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── services/
│   │   │
│   │   ├── integrations/
│   │   │
│   │   └── utils/
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

Directories shall be expanded as new modules are introduced.

## 4.4 Learning Requirements

The development team should understand:

- Python fundamentals.
- Python asynchronous programming.
- FastAPI fundamentals.
- REST API development.
- Pydantic validation.
- Dependency injection.
- Environment configuration.
- LLM fundamentals.
- Transformers and attention at a conceptual level.
- Tokens and context windows.
- LLM inference.

## 4.5 Acceptance Criteria

- FastAPI application starts successfully.
- Health-check endpoint returns HTTP 200.
- Swagger documentation is accessible.
- Configuration is loaded externally.
- No API credentials are committed to Git.
- Project structure follows the defined organization.
- Ruff and pytest are configured.
- Initial tests pass.

---
