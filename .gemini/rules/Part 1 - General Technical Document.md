# Curio
## Software Requirements Specification (SRS) and Technical Design Document

**Document Version:** 1.0
**Project:** Curio
**Document Type:** Software Requirements Specification and Technical Design
**Development Approach:** Incremental, stage-based development
**Backend:** Python + FastAPI
**Frontend:** React + TypeScript
**Database:** PostgreSQL

---

# 1. Project Overview

## 1.1 Project Description

Curio is an AI-powered developer tool discovery and repository intelligence platform designed to help developers discover, understand and explore interesting open-source GitHub repositories.

The platform will collect repository information from GitHub, evaluate repositories using a custom ranking algorithm, identify trending projects, and provide AI-generated explanations to help developers understand unfamiliar repositories.

Additionally, users will be able to interact with an AI assistant to ask questions about individual repositories.

The application will combine conventional software engineering techniques, data processing and Large Language Models (LLMs) to deliver an intelligent repository discovery experience.

## 1.2 Problem Statement

Developers face several challenges when exploring open-source projects:

- GitHub contains millions of repositories, making discovery difficult.
- Star counts alone are insufficient to determine whether a repository is interesting.
- Developers struggle to identify emerging technologies and projects.
- Understanding unfamiliar repositories requires considerable time.
- Repository information is distributed across descriptions, README files and metadata.
- Developers lack a convenient way to ask questions about unfamiliar repositories.

Curio addresses these challenges through repository discovery, algorithmic ranking, historical trend analysis and LLM-powered repository understanding.

## 1.3 Project Objectives

The primary objectives are:

1. Discover GitHub repositories using configurable search criteria.
2. Collect and maintain repository metadata.
3. Rank repositories using a custom scoring algorithm.
4. Identify trending repositories using historical popularity metrics.
5. Display recently discovered repositories.
6. Generate AI-powered repository explanations.
7. Allow users to ask questions about a specific repository using its available information.

## 1.4 Project Scope

The initial release will contain seven development stages.

| Stage | Module | Primary objective |
|---|---|---|
| 1 | Project Foundation | Python, FastAPI, architecture and LLM fundamentals |
| 2 | GitHub Integration | Repository discovery and data collection |
| 3 | Database Design | Repository persistence and historical data |
| 4 | Ranking Engine | Algorithmic repository ranking |
| 5 | Trend Intelligence | Trending and latest discoveries |
| 6 | LLM Integration | AI-powered repository analysis |
| 7 | Repository AI Chat | Context-aware repository conversations |

## 1.5 Target Users

- Software developers.
- Computer science students.
- Backend and frontend engineers.
- Open-source contributors.
- Developers exploring new technologies.
- Engineers interested in understanding software architecture and implementation.

---

# 2. Technology Stack

## 2.1 Backend Technology Stack

| Technology | Purpose | Justification |
|---|---|---|
| Python 3.12+ | Backend programming language | Strong ecosystem for AI and data processing |
| FastAPI | Backend framework | Asynchronous API development and automatic API documentation |
| Pydantic v2 | Data validation | Request, response and LLM output validation |
| SQLAlchemy 2.x | ORM | Database interaction |
| Alembic | Database migrations | Version-controlled schema changes |
| httpx | HTTP client | Asynchronous GitHub and LLM API requests |
| OpenAI Python SDK | LLM integration | Repository analysis and conversational AI |
| tiktoken | Token counting | Token estimation for compatible models |
| pytest | Testing | Unit and integration testing |
| APScheduler | Scheduled jobs | Periodic repository synchronization in the initial deployment |

Python dependencies should be pinned to compatible versions and maintained through a dependency lock file.

## 2.2 Database

**PostgreSQL**

Responsibilities:

- Store repository metadata.
- Store historical repository metrics.
- Store ranking-related information where required.
- Store AI-generated repository analyses.
- Store chat conversations and messages.
- Support repository search and retrieval.

PostgreSQL will serve as the primary persistent data store.

Initially, PostgreSQL full-text search will be sufficient for basic text retrieval.

pgvector may be introduced later if semantic retrieval becomes necessary.

## 2.3 Frontend Technology Stack

| Technology | Purpose |
|---|---|
| React | Frontend application |
| TypeScript | Type safety |
| Vite | Development and build tooling |
| Tailwind CSS | Styling |
| TanStack Query | Server-state management |
| React Router | Navigation |
| Fetch API or Axios | Backend communication |

## 2.4 Code Quality and Developer Productivity Tools

Code quality must be enforced from the beginning rather than introduced after the application becomes large.

### Python development tools

| Tool | Purpose | Usage |
|---|---|---|
| Ruff | Linting and formatting | Detect code issues and enforce formatting |
| Mypy | Static type checking | Identify type-related errors |
| Pytest | Automated testing | Test services and API behavior |
| pytest-cov | Test coverage | Measure tested code |
| Pre-commit | Git hooks | Run quality checks before commits |
| Bandit | Security linting | Detect common Python security problems |
| pip-audit | Dependency security | Identify vulnerable dependencies |

Recommended approach:

- Use Ruff for linting and formatting instead of maintaining separate Black and isort configurations.
- Use type hints throughout the backend.
- Use Mypy selectively for important modules and expand strictness as the codebase matures.
- Use pytest for automated testing.
- Run quality checks before merging changes.

### IDE extensions

Recommended VS Code extensions:

- Python
- Pylance
- Ruff
- Mypy Type Checker
- Even Better TOML
- Docker
- GitLens
- REST Client
- PostgreSQL

These are development extensions, not runtime dependencies.

### Frontend quality tools

| Tool | Purpose |
|---|---|
| ESLint | JavaScript/TypeScript linting |
| Prettier | Code formatting |
| TypeScript compiler | Static type checking |
| Vitest | Frontend unit testing |
| Playwright | End-to-end testing |

## 2.5 Infrastructure and Deployment Tools

| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Docker Compose | Local development environment |
| Git | Version control |
| GitHub Actions | CI/CD automation |
| Environment variables | External configuration and secrets |

Redis, Celery, Kafka and microservices are not required for the initial implementation.

The initial system will use a modular monolithic architecture.

---

# 3. System Architecture

## 3.1 Architectural Approach

Curio will initially follow a modular monolithic architecture.

The backend will be a single FastAPI application containing independently organized modules responsible for:

- GitHub integration.
- Repository ingestion.
- Repository persistence.
- Ranking.
- Trending calculations.
- LLM analysis.
- Conversational AI.

Each module will have clearly defined responsibilities.

The modules should communicate through service interfaces rather than accessing each other's internal implementation directly.

## 3.2 High-Level Architecture

```text
                    USER
                      |
                      v
              REACT FRONTEND
                      |
                      v
               FASTAPI BACKEND
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
   DISCOVERY       RANKING       AI MODULE
    MODULE         MODULE            |
        |             |         +----+-----+
        v             v         |          |
   GITHUB API      SCORING       v          v
                    LOGIC      LLM API   CHAT SERVICE
        |             |         |          |
        +-------------+---------+----------+
                      |
                      v
                 POSTGRESQL
```

## 3.3 External Integrations

### GitHub REST API

Used for:

- Repository search.
- Repository metadata.
- README retrieval.
- Repository statistics.

### LLM Provider

Initially, OpenAI API will be used for:

- Repository explanation generation.
- Structured information extraction.
- Natural-language question understanding.
- Repository-specific conversational responses.

The LLM provider must be accessed through a dedicated service abstraction so that a different provider can be introduced later without rewriting business logic.

---



# 11. API Design Summary

The following API structure represents the expected Stage 1 backend interface.

| Module | Endpoint | Method | Description |
|---|---|---|---|
| Health | /health | GET | Health check |
| Repository | /api/v1/repositories | GET | List repositories |
| Repository | /api/v1/repositories/{id} | GET | Repository details |
| Discovery | /api/v1/discover/top | GET | Top 20 repositories |
| Discovery | /api/v1/discover/trending | GET | Trending repositories |
| Discovery | /api/v1/discover/latest | GET | Latest discoveries |
| Analysis | /api/v1/repositories/{id}/analysis | GET | Repository analysis |
| Chat | /api/v1/repositories/{id}/chat | POST | Send repository question |
| Chat | /api/v1/repositories/{id}/chat/stream | POST | Stream response |
| Chat | /api/v1/conversations/{id} | GET | Retrieve conversation |
| Chat | /api/v1/conversations/{id}/messages | GET | Retrieve messages |

Additional ingestion and administrative endpoints shall be implemented for repository synchronization.

All endpoints shall use consistent response schemas and error formats.

---

# 12. Non-Functional Requirements

## 12.1 Performance

- Database queries shall use appropriate indexes.
- API pagination shall be supported.
- Repository search should avoid unnecessary external API calls.
- LLM calls shall have configurable timeouts.
- Repository analysis shall be cached.
- Expensive operations shall not block unrelated API requests.

## 12.2 Scalability

- The backend shall use modular service boundaries.
- External API clients shall be reusable.
- LLM provider integration shall be abstracted.
- Background execution shall be introduced for long-running ingestion and analysis tasks when necessary.
- The architecture should allow independent scaling of workers in future releases.

## 12.3 Reliability

- External API failures shall not crash the entire application.
- Transient errors shall support controlled retries.
- Database transactions shall protect data consistency.
- Failed ingestion runs shall be recorded.
- Failed AI generations shall not overwrite valid analyses.

## 12.4 Security

- GitHub and LLM API credentials shall be stored in environment configuration or a secrets manager.
- Credentials shall never be exposed to the frontend.
- External repository content shall be considered untrusted.
- Inputs shall be validated.
- API endpoints shall have appropriate request limits.
- Chat access shall be scoped to the associated repository.
- Prompt injection risks shall be considered.
- Dependencies shall be regularly checked for vulnerabilities.

Authentication and multi-user authorization are outside the initial scope, but the architecture should not prevent their future introduction.

## 12.5 Maintainability

- Modules shall have clearly defined responsibilities.
- Business logic shall remain separate from API route handlers.
- Type hints shall be used.
- Code formatting and linting shall be automated.
- Unit and integration tests shall be maintained.
- Database changes shall be managed through migrations.
- Prompt templates shall be version-controlled.
- Important architectural decisions shall be documented.

## 12.6 Observability

The application shall record:

- API request duration.
- GitHub API failures.
- Ingestion execution status.
- Ranking execution details.
- LLM request duration.
- Token usage.
- LLM provider errors.
- Chat generation failures.

Sensitive credentials and private user information shall not be written into logs.

---

# 13. Testing Strategy

Testing shall be performed at multiple levels.

## 13.1 Unit Testing

Test individual business components.

Examples:

- GitHub response mapping.
- Repository normalization.
- Popularity calculation.
- Growth calculation.
- Ranking score calculation.
- Trending score calculation.
- Prompt construction.
- Pydantic response validation.

## 13.2 Integration Testing

Test communication between application components.

Examples:

- FastAPI and PostgreSQL.
- GitHub client and response mapper.
- Repository service and database.
- Analysis service and LLM provider.
- Chat service and repository retrieval.

External API tests should use mocked responses or controlled test environments.

## 13.3 End-to-End Testing

Test the complete user workflow.

Example:

```text
Discover Java Repositories
          |
          v
Collect Repository Metadata
          |
          v
Persist in PostgreSQL
          |
          v
Calculate Ranking
          |
          v
Display Top 20
          |
          v
Open Repository
          |
          v
Generate AI Analysis
          |
          v
Ask AI Question
          |
          v
Receive Context-Aware Answer
```

## 13.4 AI-Specific Testing

AI output testing shall include:

- Structured response validity.
- Accuracy against repository evidence.
- Relevance to user questions.
- Hallucination checks.
- Prompt injection scenarios.
- Token usage.
- Response latency.
- Model failure handling.

AI quality shall be evaluated using a manually reviewed set of representative repositories and questions.

---

# 14. Global Stage Completion Criteria

The complete Stage 1 implementation shall be considered successful when all the following conditions are satisfied.

### Repository Discovery

- GitHub API integration works.
- Multiple repository queries are supported.
- Repository metadata is collected and normalized.
- Repository data is stored in PostgreSQL.

### Ranking and Discovery Intelligence

- Top 20 repositories are calculated using the custom scoring algorithm.
- Trending repositories are calculated using historical data.
- Latest discoveries are based on discovery timestamps.
- Ranking and trending results are independently calculated.

### AI Repository Analysis

- The LLM analyzes repository metadata and README content.
- All required explanation fields are generated.
- Structured output is validated.
- AI analysis is stored and reused.
- Token usage and model information are tracked.

### Repository Chat

- Users can ask questions about a selected repository.
- The assistant retrieves repository-specific context.
- Conversation history is maintained.
- Responses support streaming.
- Unsupported information is handled appropriately.

### Engineering Quality

- Backend follows the defined architecture.
- Database migrations are available.
- Automated tests pass.
- Code quality checks pass.
- Secrets are protected.
- Error handling is implemented.
- API documentation is available.

---

# 15. Out of Scope for Initial Release

The following features shall not be implemented in the current seven stages.

| Feature | Reason for exclusion |
|---|---|
| User authentication | Not necessary for initial discovery functionality |
| Personalized user profiles | Reserved for a later personalization stage |
| AI-based ranking | Ranking initially uses a custom deterministic algorithm |
| Autonomous AI agents | No agentic workflow is required |
| Multi-agent architecture | Adds unnecessary complexity |
| Vector database | Initial retrieval uses PostgreSQL |
| Advanced semantic search | Can be introduced as a future enhancement |
| Reddit integration | Initial data source is GitHub |
| Hacker News integration | Multi-source discovery is deferred |
| Automatic codebase analysis | Initial analysis uses metadata and README |
| User notifications | Not required for initial functionality |
| Social features | Outside the initial product scope |

---

# 16. Future Extension Points

The architecture should allow future stages to introduce:

1. Personalized repository recommendations.
2. Developer interest profiles.
3. Skill-level-aware discovery.
4. Semantic repository search using embeddings.
5. Hybrid retrieval combining keyword and vector search.
6. Multi-source ingestion from Reddit, Hacker News and technical blogs.
7. Technology trend analysis.
8. Advanced repository comparison.
9. Agentic AI workflows for multi-step technology exploration.
10. Autonomous research and recommendation workflows.

These are future capabilities and must not be treated as current Stage 1 acceptance requirements.

---

# 17. Architectural Decision Principles

The following principles shall guide implementation decisions.

**1. Separation of concerns**

Repository discovery, ranking and AI analysis must remain independent modules.

**2. Conventional ranking first**

The initial ranking engine must use measurable and explainable signals rather than LLM-generated judgments.

**3. Data persistence before intelligence**

Historical repository information must be collected before accurate trend analysis is attempted.

**4. LLMs as information interpreters**

The LLM should explain and interpret repository information, not replace the application's data collection or deterministic business logic.

**5. Structured AI responses**

AI-generated data must be validated before persistence.

**6. Context-grounded chat**

Repository-specific responses must be generated using the selected repository's available information.

**7. Incremental architecture**

New technologies should be introduced only when justified by actual functional requirements.

**8. Testability**

Every major service should be testable independently.

---

# 18. Final Project Deliverable

At the completion of all seven stages, Curio shall provide a functional developer discovery platform with the following capabilities:

- Discover open-source GitHub repositories.
- Search using programming languages and topics.
- Collect and maintain repository information.
- Rank the top 20 interesting repositories using a custom algorithm.
- Identify trending repositories.
- Display latest discoveries.
- Generate AI-powered repository explanations.
- Allow users to chat about individual repositories.
- Maintain conversation history.
- Deliver context-aware and streaming AI responses.

The initial release shall establish a reliable foundation for subsequent development of personalized discovery, semantic search and agentic AI capabilities.

**End of Document — Curio SRS v1.0**
