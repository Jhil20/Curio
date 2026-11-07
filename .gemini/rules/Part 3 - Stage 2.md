# 5. Stage 2 — GitHub Repository Discovery and Integration

## 5.1 Objective

Implement a GitHub integration module capable of discovering repositories based on different search criteria and collecting their metadata.

This stage establishes the application's external repository data source.

## 5.2 Functional Requirements

**FR-006: GitHub Authentication**

The application shall support authenticated GitHub API requests using a configured access token.

**FR-007: Repository Search**

The application shall support repository discovery using GitHub search parameters.

Supported parameters:

| Parameter | Description |
|---|---|
| language | Programming language |
| topic | Repository topic |
| min_stars | Minimum star count |
| min_forks | Minimum fork count |
| created_after | Repository creation date |
| updated_after | Last updated date |
| sort | Supported GitHub sorting option |
| order | Ascending or descending |
| page | Pagination page |
| per_page | Number of results |

**FR-008: Repository Metadata Collection**

The application shall retrieve the following information:

- GitHub repository ID.
- Repository name.
- Full repository name.
- Owner information.
- Description.
- HTML URL.
- Programming language.
- Topics.
- Stars.
- Forks.
- Open issues.
- Creation date.
- Last updated date.
- Last push date.

**FR-009: README Retrieval**

The application shall be capable of retrieving README content for repositories selected for further analysis.

**FR-010: Pagination**

The application shall support pagination within GitHub API limits.

**FR-011: API Rate Limit Handling**

The application shall monitor rate-limit headers and handle exhausted quotas appropriately.

**FR-012: Error Handling**

The application shall handle:

- Authentication failures.
- Rate-limit responses.
- Network timeouts.
- Server errors.
- Invalid search queries.
- Missing repository information.

## 5.3 Repository Discovery Logic

The discovery workflow shall operate as follows:

```text
Discovery Request
       |
       v
Validate Search Parameters
       |
       v
Construct GitHub Query
       |
       v
Send Request to GitHub
       |
       v
Receive Repository Results
       |
       v
Parse Response
       |
       v
Normalize Metadata
       |
       v
Validate Required Fields
       |
       v
Return Normalized Repository Data
```

Example query:

```text
language:Java topic:database stars:>100
```

The system shall allow multiple discovery queries to be executed independently.

Example:

```text
Query 1: language:Java topic:database

Query 2: language:Python topic:machine-learning

Query 3: language:Go topic:distributed-systems
```

## 5.4 Data Normalization

GitHub responses shall be transformed into a consistent internal repository representation.

The internal representation must not depend directly on the complete GitHub response structure.

Missing optional values shall be handled safely.

Repository identity shall be based on GitHub's unique repository ID rather than repository name.

## 5.5 Data Ingestion Strategy

For the initial implementation:

1. Discovery can be triggered manually through a protected administrative operation.
2. GitHub results are fetched.
3. Results are normalized.
4. Duplicate repository IDs are identified.
5. Repository information is prepared for persistence in Stage 3.

Historical snapshots and production persistence are implemented in Stage 3.

## 5.6 Acceptance Criteria

- The system successfully authenticates with GitHub.
- Repositories can be discovered using programming languages.
- Repositories can be discovered using topics.
- Multiple search parameters can be combined.
- Repository metadata is normalized correctly.
- Pagination works within configured limits.
- API rate-limit responses are handled.
- Network errors do not crash the application.
- Duplicate repositories can be identified using GitHub IDs.
- README retrieval works for supported repositories.

---
