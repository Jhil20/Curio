# 10. Stage 7 — Repository-Specific AI Chat

## 10.1 Objective

Develop a conversational AI feature that allows users to ask questions about a specific repository.

The AI assistant shall use repository metadata, README content and stored AI analysis as its knowledge source.

The initial implementation shall be repository-specific rather than a general-purpose chatbot.

## 10.2 Core Functional Requirements

**FR-013: Repository Chat Session**

Users shall be able to initiate a conversation associated with a selected repository.

**FR-014: Natural-Language Questions**

Users shall be able to ask questions using natural language.

Examples:

- What problem does this repository solve?
- Which technologies does it use?
- How is its architecture organized?
- What should I understand before exploring this project?
- Is this repository suitable for learning database internals?
- Explain its indexing implementation.

**FR-015: Context-Aware Responses**

The assistant shall use repository-specific information when generating answers.

**FR-016: Conversation History**

The application shall maintain conversation history within a chat session.

**FR-017: Follow-up Questions**

The assistant shall use relevant previous messages to understand follow-up questions.

**FR-018: Streaming Responses**

The application shall support incremental response delivery using Server-Sent Events (SSE).

**FR-019: Grounded Responses**

The assistant shall not invent repository features when the available information does not support an answer.

## 10.3 AI Architecture

The initial chat implementation shall use a basic RAG architecture.

Components:

1. Query processing.
2. Repository context retrieval.
3. Context construction.
4. Prompt construction.
5. LLM generation.
6. Response delivery.

## 10.4 Chat Processing Logic

```text
User Opens Repository
          |
          v
Starts Chat Session
          |
          v
User Submits Question
          |
          v
Retrieve Conversation History
          |
          v
Retrieve Repository Context
          |
          v
Prepare Relevant Information
          |
          v
Construct Prompt
          |
          v
Send Request to LLM
          |
          v
Receive Generated Response
          |
          v
Stream Response to Frontend
          |
          v
Persist Conversation Messages
```

## 10.5 Context Sources

The initial repository-specific assistant shall use:

- Repository description.
- Repository metadata.
- README content.
- Stored AI-generated repository analysis.
- Relevant previous conversation messages.

The application shall avoid sending unnecessary information to the LLM.

## 10.6 Query Understanding

The system should identify the user's intent.

Example:

User question:

"Explain how this project handles indexing."

Expected interpretation:

```json
{
  "intent": "technical_explanation",
  "topic": "indexing",
  "repository_specific": true
}
```

Query understanding may be performed using an LLM.

The system shall retrieve relevant repository information before generating its response.

For the initial implementation, the retrieval mechanism may use repository-specific context and PostgreSQL full-text search.

## 10.7 RAG Implementation

The initial implementation shall use conventional database retrieval.

```text
Question
   |
   v
Identify Relevant Context
   |
   v
Retrieve Repository Information
   |
   v
Construct Context
   |
   v
LLM Generation
   |
   v
Grounded Response
```

Vector embeddings and semantic search are optional future enhancements, not mandatory requirements for the first version.

## 10.8 Conversation History Management

Each conversation shall have:

- A unique conversation ID.
- An associated repository ID.
- A collection of user messages.
- A collection of assistant messages.
- Message timestamps.

The application shall maintain a configurable history window to prevent unnecessary token consumption.

If history becomes too large, older messages may be summarized or excluded according to the configured context strategy.

## 10.9 Streaming

The backend shall support SSE for streaming LLM output.

The frontend shall display generated text incrementally.

The application shall also handle:

- Client disconnection.
- LLM timeout.
- Stream interruption.
- Provider errors.
- Message persistence after successful generation.

The streaming protocol shall define a completion event and an error event.

## 10.10 API Requirements

Create the following endpoints:

```http
POST /api/v1/repositories/{id}/chat

GET /api/v1/conversations/{conversation_id}

GET /api/v1/conversations/{conversation_id}/messages

POST /api/v1/repositories/{id}/chat/stream
```

Example request:

```json
{
  "conversation_id": null,
  "message": "Explain the indexing implementation."
}
```

Example response:

```json
{
  "conversation_id": "8c9d-1234",
  "repository_id": 101,
  "answer": "The repository implements...",
  "status": "completed"
}
```

The example response is illustrative.

## 10.11 Acceptance Criteria

- Users can start a chat session for a repository.
- Chat sessions are associated with repository IDs.
- Natural-language questions are accepted.
- Repository context is supplied to the LLM.
- Previous conversation messages are available for follow-up questions.
- Responses are streamed successfully.
- Messages are persisted.
- Conversation history can be retrieved.
- The assistant handles insufficient repository information appropriately.
- Unsupported claims are not presented as verified repository facts.
- The assistant cannot access unrelated repositories unless explicitly supported by the retrieval design.

---
