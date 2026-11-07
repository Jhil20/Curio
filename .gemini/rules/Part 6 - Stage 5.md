# 8. Stage 5 — Trending Repositories and Latest Discoveries

## 8.1 Objective

Implement two discovery capabilities:

1. Trending repositories.
2. Latest discovered repositories.

These features shall operate independently of the Top 20 ranking mechanism.

## 8.2 Trending Repositories

Trending repositories shall be identified using historical growth and activity.

The initial trending formula:

```text
Trending Score =
    0.65 * Seven-Day Growth +
    0.20 * Thirty-Day Growth +
    0.15 * Activity
```

All components shall be normalized.

### Trending Processing Logic

```text
Repository Snapshots
        |
        v
Select Current Snapshot
        |
        v
Find Previous Snapshot
        |
        v
Calculate 7-Day Growth
        |
        v
Calculate 30-Day Growth
        |
        v
Calculate Activity
        |
        v
Normalize Metrics
        |
        v
Calculate Trending Score
        |
        v
Sort Descending
        |
        v
Return Trending Repositories
```

The system must ensure that snapshots are sufficiently close to the requested comparison windows.

If historical data is insufficient, the repository shall be marked as having insufficient trend data or excluded from the trending results.

Negative growth shall be represented correctly.

## 8.3 Latest Discoveries

Latest Discoveries shall identify repositories recently added to DevRadar.

The primary ordering field shall be `discovered_at`.

Repository creation date shall be exposed separately.

This distinction is necessary because a repository might have existed for years before DevRadar discovered it.

### Latest Discovery Logic

```text
Repository Database
        |
        v
Filter Recently Discovered
        |
        v
Apply Optional Filters
        |
        v
Sort by discovered_at DESC
        |
        v
Return Latest Repositories
```

Optional filters:

- Programming language.
- Topics.
- Creation date.
- Minimum stars.

## 8.4 API Requirements

```http
GET /api/v1/discover/trending
GET /api/v1/discover/latest
```

Trending endpoint parameters:

- window: 7d or 30d.
- language.
- topic.
- limit.
- offset.

Latest endpoint parameters:

- language.
- topic.
- created_after.
- limit.
- offset.

## 8.5 Acceptance Criteria

- Trending repositories are calculated using historical snapshots.
- Seven-day and thirty-day windows are supported.
- Trending scores are normalized.
- Insufficient historical information is handled correctly.
- Latest discoveries are sorted by discovery timestamp.
- Creation date and discovery date are distinct.
- Language and topic filtering work.
- Results are paginated.
- Trending and latest results do not depend on LLM-generated scores.

---
