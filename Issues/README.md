# Issues Directory

This folder now acts as a lightweight issue database that GitHub workflows can append to when issues are created or updated. The automation keeps the contents in-sync with the repository so the CI/CD system can reason over issue history without reaching outside the repo.

## Structure
1. `Issues/update_issue_record.py` – Python helper that converts each `issues` event payload into a structured JSON record, updates a summary index, and appends a log quote.
2. `Issues/records/issue-<number>.json` – One file per issue that contains the latest metadata (title, body, labels, assignees, state, timestamps, origin event).
3. `Issues/index.json` – A quick lookup table keyed by issue number to read status/labels/assignee summary without opening the full record.
4. `Issues/workflows/issue-events.log` – Append-only log of the `issues` events the workflow has processed, useful for tracing timing or retry loops.

## Automation Flow
1. `.github/workflows/issue-tracking.yml` is triggered on every `issues` event (opened/edited/closed/labeled/assigned, etc.).
2. The workflow checks out the repo, runs `python Issues/update_issue_record.py`, and commits `Issues/` if anything changed.
3. `update_issue_record.py` relies on `GITHUB_EVENT_PATH` to read the GitHub payload (provided automatically by Actions), writes the updated record, and keeps the index and log aligned.
4. Versions of CI run failures (Backend CI, Frontend CI, .NET CI) already open GitHub issues with `dacbd/create-issue-action`. When those issues fire their events, the tracking workflow ensures a copy appears under `Issues/`.

## Usage Notes
- Avoid manual edits unless you know what you are doing, as the workflow will keep overwriting the per-issue files.
- If you need to inspect state in automation, rely on `Issues/index.json` to avoid opening large bodies.
- Workflows can consume `Issues/records` or `Issues/index.json` as a source-of-truth for triage status or to drive downstream releases.
- Use `GitHubProject/manage_project.py` to mirror these snapshots into a GitHub Projects (Beta) board, add note cards, or drive automation gates without leaving the repository context.
