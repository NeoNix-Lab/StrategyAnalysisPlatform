# Issue Record Benchmark

This document describes the expected schema and example values for files under `Issues/records/`. The goal is to provide a quick verification checklist that workflows can reuse to ensure issue snapshots stay consistent over time.

## Schema Expectations

| Field | Description |
| --- | --- |
| `event` | Always `issues` for the GitHub `issues` webhook. |
| `action` | The event action (`opened`, `edited`, `closed`, etc.). |
| `repository` | Full repository name (e.g., `NeoNix-Lab/StrategyAnalysisPlatform`). |
| `sender` | GitHub login of the actor who triggered the event. |
| `event_timestamp` | UTC timestamp when the workflow processed the payload. |
| `issue.number` | Numeric GitHub issue number. |
| `issue.title` | Issue title string. |
| `issue.body` | Issue body text (Multiline/Markdown). |
| `issue.state` | Current issue state (`open` or `closed`). |
| `issue.html_url` | Canonical link back to GitHub. |
| `issue.labels` | List of label strings. |
| `issue.assignees` | List of assignee logins. |
| `issue.created_at` / `issue.updated_at` / `issue.closed_at` | Timestamps from the GitHub API. |

## Verification Checklist

1. The JSON file must be valid UTF-8 and indented with two spaces.
2. `issue.number` should match the filename (`issue-<number>.json`).
3. `issue.labels` can mix label names and objects; the benchmark script normalizes both.
4. Whenever `action` changes (e.g., `reopened`), the workflow should update both the record file and `Issues/index.json`.
5. `Issues/workflows/issue-events.log` should append a line for each processed payload in the format: `<timestamp> | issue #<number> | <action> | <sender>`.

## Sample Record (used as guardrail)

```jsonc
{
  "event": "issues",
  "action": "opened",
  "repository": "NeoNix-Lab/StrategyAnalysisPlatform",
  "sender": "backend-maintainer",
  "event_timestamp": "2025-12-14T18:45:00Z",
  "issue": {
    "number": 1,
    "title": "Run stop does not update run state or series closure",
    "body": "Durante lo stop della strategia via API `/api/runs/{run_id}/stop` non viene aggiornato lo stato della run (rimane `RUNNING`) e neanche `RunSeries.end_utc` viene scritto; la serie temporale continua ad accumulare dati non chiusi. L'exporter Quantower segnala l'ordine di stop ma il backend non chiude neanche `strategy_runs.end_utc`.",
    "state": "open",
    "html_url": "https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/issues/1",
    "labels": ["backend", "export", "bug"],
    "assignees": ["backend-team"],
    "created_at": "2025-12-14T18:44:00Z",
    "updated_at": "2025-12-14T18:44:00Z",
    "closed_at": null
  }
}
```
