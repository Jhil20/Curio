# 7. Stage 4 — Conventional Repository Ranking Engine

## 7.1 Objective

Develop a custom scoring algorithm to identify interesting repositories.

The initial ranking mechanism shall not use an LLM or AI-generated quality judgment.

Ranking shall be based on measurable repository signals and configurable weights.

## 7.2 Ranking Factors

The initial scoring engine shall consider five factors.

| Factor | Description |
|---|---|
| Popularity | Existing stars and forks |
| Growth | Increase in stars over time |
| Activity | Recent repository development activity |
| Maintenance | Maintenance-related signals |
| Relevance | Match with discovery criteria |

## 7.3 Ranking Algorithm

The initial ranking formula:

```text
Score =
    0.25 * Popularity +
    0.30 * Growth +
    0.20 * Activity +
    0.10 * Maintenance +
    0.15 * Relevance
```

All individual components shall be normalized between 0 and 1.

Final scores shall also be within the range 0–1.

Weights must be configurable.

## 7.4 Scoring Logic

### A. Popularity Score

Inputs:

- Current stars.
- Current forks.

Use logarithmic normalization to reduce the impact of extremely popular repositories.

Example:

```text
Star Score =
log(1 + repository_stars)
/
log(1 + maximum_stars)
```

Forks can be incorporated using a similar normalized measure.

### B. Growth Score

Calculate star growth over a defined historical period.

```text
Growth =
Current Stars - Previous Stars
```

Use the historical snapshots collected in Stage 3.

The scoring logic should support seven-day and thirty-day windows.

### C. Activity Score

Consider:

- Last push date.
- Recent development activity.
- Recent commits where available.

Do not treat `updated_at` alone as a reliable development activity metric.

### D. Maintenance Score

Consider:

- Recent releases.
- Repository maintenance signals.
- Issue activity where available.
- Recent project updates.

Missing information should not automatically mean poor maintenance.

### E. Relevance Score

Compare:

- Programming language.
- Repository topics.
- Selected discovery criteria.

The score should increase when a repository closely matches the requested discovery category.

## 7.5 Ranking Workflow

```text
Repository Dataset
        |
        v
Fetch Ranking Signals
        |
        v
Calculate Popularity
        |
        v
Calculate Growth
        |
        v
Calculate Activity
        |
        v
Calculate Maintenance
        |
        v
Calculate Relevance
        |
        v
Normalize Components
        |
        v
Apply Configurable Weights
        |
        v
Calculate Final Score
        |
        v
Sort Descending
        |
        v
Select Top 20
```

## 7.6 Ranking Output

Each ranked repository should expose:

```json
{
  "repository_id": 101,
  "full_name": "developer/project",
  "ranking_score": 0.87,
  "ranking_components": {
    "popularity": 0.85,
    "growth": 0.95,
    "activity": 0.90,
    "maintenance": 0.80,
    "relevance": 0.85
  }
}
```

The values are illustrative.

## 7.7 Acceptance Criteria

- Ranking scores are calculated using the configured formula.
- Every component is normalized.
- Final scores are between 0 and 1.
- Weights are configurable.
- Repositories are sorted by final score.
- Top 20 results are returned.
- Ranking results are deterministic for identical input datasets and configuration.
- Missing signals are handled using documented fallback rules.
- Unit tests cover normal and edge cases.
- Ranking is independent of LLM output.

---
