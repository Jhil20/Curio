# 6. Stage 3 — Database Design and Repository Persistence

## 6.1 Objective

Design and implement a relational database capable of storing repository metadata, historical metrics and future AI-generated information.

## 6.2 Database Technology

PostgreSQL will be used as the primary database.

SQLAlchemy 2.x will provide ORM functionality.

Alembic will manage database schema migrations.

## 6.3 Database Entities

The initial database shall contain the following entities.

### Entity 1: repositories

Purpose: Store the latest known metadata of each discovered repository.

| Column | Data type | Description |
|---|---|---|
| id | BIGINT | Internal primary key |
| github_id | BIGINT | Unique GitHub repository ID |
| name | VARCHAR | Repository name |
| full_name | VARCHAR | Owner/repository |
| owner_login | VARCHAR | Owner username |
| description | TEXT | Repository description |
| html_url | TEXT | GitHub URL |
| language | VARCHAR | Primary language |
| topics | JSONB | Repository topics |
| stars | INTEGER | Current stars |
| forks | INTEGER | Current forks |
| open_issues | INTEGER | Open issue count |
| created_at | TIMESTAMPTZ | GitHub creation date |
| github_updated_at | TIMESTAMPTZ | GitHub updated date |
| pushed_at | TIMESTAMPTZ | Last push date |
| discovered_at | TIMESTAMPTZ | First discovery date |
| last_synced_at | TIMESTAMPTZ | Last synchronization date |
| readme_content | TEXT | Retrieved README content |

Constraints:

- `github_id` must be unique.
- Required fields must not be null.
- Internal IDs shall be primary keys.

### Entity 2: repository_snapshots

Purpose: Maintain historical repository statistics.

| Column | Data type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| repository_id | BIGINT | Foreign key |
| stars | INTEGER | Recorded stars |
| forks | INTEGER | Recorded forks |
| recorded_at | TIMESTAMPTZ | Snapshot timestamp |

A repository can have multiple snapshots.

Relationship:

```text
repositories 1 -------- N repository_snapshots
```

### Entity 3: repository_analyses

Purpose: Store LLM-generated repository explanations.

| Column | Data type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| repository_id | BIGINT | Foreign key |
| problem_solved | TEXT | Problem description |
| functionality | TEXT | Repository functionality |
| technologies | JSONB | Identified technologies |
| target_audience | JSONB | Intended audience |
| interesting_points | JSONB | Interesting aspects |
| learning_outcomes | JSONB | Learning opportunities |
| model_name | VARCHAR | LLM model |
| prompt_version | VARCHAR | Prompt version |
| analyzed_at | TIMESTAMPTZ | Analysis timestamp |

A repository may have multiple historical analysis versions, but the application should identify which analysis is currently active.

### Entity 4: chat_conversations

Purpose: Store repository-specific chat sessions.

| Column | Data type | Description |
|---|---|---|
| id | UUID | Primary key |
| repository_id | BIGINT | Related repository |
| created_at | TIMESTAMPTZ | Conversation creation date |
| updated_at | TIMESTAMPTZ | Last message timestamp |

### Entity 5: chat_messages

Purpose: Store conversation messages.

| Column | Data type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| conversation_id | UUID | Foreign key |
| role | VARCHAR | User or assistant |
| content | TEXT | Message content |
| created_at | TIMESTAMPTZ | Message timestamp |

### Entity 6: discovery_runs

Purpose: Track discovery executions.

| Column | Data type | Description |
|---|---|---|
| id | BIGINT | Primary key |
| query | TEXT | Executed query |
| status | VARCHAR | Execution status |
| repositories_found | INTEGER | Results count |
| started_at | TIMESTAMPTZ | Start timestamp |
| completed_at | TIMESTAMPTZ | Completion timestamp |
| error_message | TEXT | Failure details |

## 6.4 Database Relationships

```text
repositories
    |
    |---- repository_snapshots
    |
    |---- repository_analyses
    |
    |---- chat_conversations
                |
                |---- chat_messages

discovery_runs
```

## 6.5 Repository Persistence Logic

The application shall implement an upsert-based persistence mechanism.

```text
Normalized Repository
         |
         v
Check github_id
         |
     +---+---+
     |       |
   Exists  New
     |       |
     v       v
  Update   Insert
     |       |
     +---+---+
         |
         v
   Persist Changes
```

The system shall preserve `discovered_at` when updating an existing repository.

Historical snapshots shall be inserted separately when metrics are collected.

## 6.6 Acceptance Criteria

- PostgreSQL connection works.
- All defined tables are created through migrations.
- Repository metadata can be persisted.
- Duplicate GitHub IDs are prevented.
- Repository updates do not create duplicate records.
- Historical snapshots are stored.
- Repository analysis can be associated with a repository.
- Chat conversations and messages can be persisted.
- Foreign-key constraints work correctly.
- Database transactions handle failed operations safely.

---
