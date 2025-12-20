# GitHub Project Utilities

This folder collects helpers that interact with a GitHub **Projects (Beta)** board tied to this repository. The goal is to keep a remote project in sync with `Issues/` and to expose simple CLI utilities for common maintenance tasks.

## Setup

1. Copy `GitHubProject/config.template.json` to `GitHubProject/config.json` and fill in:
   * `owner`, `repo`: the repository owner/name.
   * `project_number`: the number of the Projects (Beta) board you want to manage.
   * `record_dir`: local path to `Issues/records` if you plan to sync issue snapshots.
2. Export a GitHub token in your shell with sufficient `repo` and `project` scopes:

   ```bash
   export GITHUB_TOKEN="ghp_..."
   ```

3. Install Python dependencies:

   ```bash
   pip install requests
   ```

## Available Commands

`manage_project.py` exposes the following actions:

| Command | Description |
| --- | --- |
| `list` | Lists the project id, title, columns, and the first page of items with their fields/content. |
| `add-issue --issue <number>` | Adds an existing GitHub issue to the project as a linked content card. |
| `add-note --note "<text>"` | Creates a new note item on the board (useful for quick reminders). |
| `sync-record --issue <number>` | Checks `Issues/records/issue-<number>.json` and, if not already present, adds it to the project. |
| `update-field --item-id <id> --field "<name>" --value "<value>"` | Updates a specific project field for an item (experimental for single-select/text fields). |

Each command prints JSON-friendly summaries so you can embed it in scripts or CI.

## Integration Notes

- The `sync-record` command makes `GitHubProject` aware of the local issue snapshots; you can call it from workflows after `issue-tracking.yml` runs to keep the board in sync.
- The utilities assume a Projects (Beta) board; the GraphQL endpoint used is `https://api.github.com/graphql`.
- If you prefer the classic GitHub Projects UI, you can adapt the script to use the REST v3 API by modifying the GraphQL queries.
