# 9. Stage 6 — LLM-Powered Repository Analysis

## 9.1 Objective

Integrate a Large Language Model to understand repository metadata and README content and generate meaningful explanations.

The LLM shall be used for repository understanding and explanation, not for conventional repository ranking.

## 9.2 AI Technology Stack

| Technology | Purpose |
|---|---|
| OpenAI API | LLM inference |
| OpenAI Python SDK | Provider integration |
| Pydantic | Structured output validation |
| JSON Schema | Output structure definition |
| tiktoken | Token estimation for compatible models |
| httpx | README and external data retrieval |

The selected LLM model shall be configurable.

The system should not hardcode model-specific assumptions throughout the business logic.

## 9.3 Repository Analysis Requirements

For every supported repository, the LLM shall generate:

1. Problem solved.
2. Repository functionality.
3. Technologies used.
4. Intended audience.
5. Interesting technical aspects.
6. Learning outcomes.

## 9.4 Repository Analysis Input

The analysis engine shall receive:

- Repository name.
- Description.
- Primary programming language.
- Topics.
- Repository metadata.
- README content.

Additional metadata may be incorporated when available.

## 9.5 Context Preparation Logic

Before calling the LLM, the application shall prepare the repository context.

```text
Repository Metadata
        |
        +
        |
README Content
        |
        v
Context Preparation
        |
        v
Content Cleaning
        |
        v
Token Estimation
        |
        v
Context Length Validation
        |
        v
Prompt Construction
        |
        v
LLM Request
```

If the README exceeds the configured context budget, the system shall apply a controlled truncation or section-selection strategy.

Chunking can be introduced for larger documents.

Repository content must be treated as untrusted input.

## 9.6 Prompt Engineering Requirements

The analysis prompt shall:

- Define the model as a software repository analyst.
- Specify the expected analysis fields.
- Require evidence-based explanations.
- Prohibit unsupported feature claims.
- Allow unknown information to be explicitly identified.
- Treat README instructions as data rather than system instructions.

Prompt templates shall be version-controlled.

## 9.7 Structured Output

The LLM shall generate an output conforming to a defined Pydantic schema.

Example:

```json
{
  "problem_solved": "Explains the problem...",
  "functionality": "Describes the implementation...",
  "technologies": [
    "Java",
    "PostgreSQL"
  ],
  "target_audience": [
    "Backend developers",
    "Database enthusiasts"
  ],
  "interesting_points": [
    "Custom indexing implementation"
  ],
  "learning_outcomes": [
    "Database internals",
    "Indexing"
  ]
}
```

The actual output must be validated before persistence.

Invalid or incomplete responses shall be handled through controlled validation and retry logic.

## 9.8 Analysis Caching

The system shall avoid generating the same analysis repeatedly.

Processing logic:

```text
User Requests Repository Analysis
              |
              v
Check Existing Analysis
              |
        +-----+-----+
        |           |
      Exists      Missing
        |           |
        v           v
  Return Cached   Call LLM
     Analysis        |
                     v
                Validate JSON
                     |
                     v
                Store Analysis
                     |
                     v
                Return Result
```

Analysis records shall include:

- Model name.
- Prompt version.
- Generation timestamp.
- Input token usage where available.
- Output token usage where available.
- Processing status.

A new analysis may be generated when the source content changes significantly or the prompt version is updated.

## 9.9 API Requirements

```http
GET /api/v1/repositories/{id}/analysis
```

The endpoint shall return the latest available analysis.

If an analysis does not exist, the application shall initiate analysis generation and provide an appropriate processing status.

## 9.10 Error Handling

The application shall handle:

- LLM API timeouts.
- Rate-limit errors.
- Provider errors.
- Invalid structured responses.
- Context length errors.
- Empty README content.
- Missing repository metadata.
- Unsupported repository content.

The application must not present a failed or unvalidated analysis as successful.

## 9.11 Acceptance Criteria

- LLM API integration works.
- Repository metadata is supplied to the model.
- README content is incorporated into the context.
- Analysis contains all six required fields.
- Structured output is validated.
- Invalid responses are handled.
- Analysis is stored in PostgreSQL.
- Existing analysis is reused when valid.
- Model and prompt versions are recorded.
- Token usage is tracked where supported.
- Unsupported claims are discouraged through evidence-based prompting.
- External repository content is treated as untrusted input.

---
