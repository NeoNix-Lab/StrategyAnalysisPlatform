#!/usr/bin/env python3
"""
Minimal CLI to inspect and update a GitHub Projects (Beta) board.

The script assumes the project exists in the target repository and that the
supplied `GITHUB_TOKEN` has `repo` and `project` permissions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

PROJECT_METADATA_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    projectV2(number: $number) {
      id
      title
      fields(first: 50) {
        nodes {
          id
          name
          dataType
        }
      }
    }
  }
}
"""

PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 50, after: $after) {
        nodes {
          id
          note
          type
          content {
            __typename
            ... on Issue {
              id
              number
              title
              state
              url
            }
          }
          fieldValues(first: 50) {
            nodes {
              field {
                id
                name
                dataType
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
              }
              value
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""

ISSUE_NODE_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      number
      title
      state
      url
    }
  }
}
"""

MUTATION_ADD_ISSUE = """
mutation($projectId: ID!, $contentId: ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item {
      id
    }
  }
}
"""

MUTATION_ADD_NOTE = """
mutation($projectId: ID!, $note: String!) {
  addProjectV2Item(input: {projectId: $projectId, content: {note: $note}}) {
    item {
      id
    }
  }
}
"""

MUTATION_UPDATE_FIELD = """
mutation($itemId: ID!, $fieldId: ID!, $value: ProjectV2ItemFieldValueInput!) {
  updateProjectV2ItemFieldValue(input: {itemId: $itemId, fieldId: $fieldId, value: $value}) {
    item {
      id
    }
  }
}
"""


class GitHubProjectManager:
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required to speak with GitHub APIs.")
        self.headers = {
            "Authorization": f"bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.project_id: Optional[str] = None
        self.project_title: Optional[str] = None
        self.fields: Dict[str, Dict[str, Any]] = {}

    def _load_config(self, path: Path) -> Dict[str, Any]:
        template = path.with_suffix(".template.json")
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}. Copy {template} -> {path}")
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        raw.setdefault("items_page_size", 50)
        raw.setdefault("record_dir", "Issues/records")
        return raw

    def _graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers=self.headers,
            json={"query": query, "variables": variables},
        )
        if response.status_code != 200:
            raise RuntimeError(f"GitHub API returned {response.status_code}: {response.text}")
        payload = response.json()
        if errors := payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {errors}")
        return payload["data"]

    def ensure_project(self) -> None:
        if self.project_id:
            return
        variables = {
            "owner": self.config["owner"],
            "name": self.config["repo"],
            "number": int(self.config["project_number"]),
        }
        data = self._graphql(PROJECT_METADATA_QUERY, variables)
        project = data["repository"]["projectV2"]
        self.project_id = project["id"]
        self.project_title = project["title"]
        self.fields = {
            field["name"].lower(): field
            for field in project["fields"]["nodes"]
        }

    def list_items(self) -> List[Dict[str, Any]]:
        self.ensure_project()
        items: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            data = self._graphql(PROJECT_ITEMS_QUERY, {"projectId": self.project_id, "after": cursor})
            node = data.get("node")
            if not node:
                break
            payload = node["items"]
            for raw_item in payload["nodes"]:
                items.append(self._normalize_item(raw_item))
            page_info = payload["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        return items

    def _normalize_item(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        content = raw_item.get("content") or {}
        field_values = []
        for fv in raw_item.get("fieldValues", {}).get("nodes", []):
            field = fv["field"]
            field_values.append(
                {
                    "id": field["id"],
                    "name": field["name"],
                    "dataType": field["dataType"],
                    "value": fv.get("value"),
                    "singleSelect": fv.get("name"),
                }
            )
        return {
            "id": raw_item["id"],
            "note": raw_item.get("note"),
            "type": raw_item.get("type"),
            "content": {
                "typename": content.get("__typename"),
                "issue": {
                    "id": content.get("id"),
                    "number": content.get("number"),
                    "title": content.get("title"),
                    "state": content.get("state"),
                    "url": content.get("url"),
                }
                if content.get("__typename") == "Issue"
                else None,
            },
            "fields": field_values,
        }

    def add_issue(self, issue_number: int) -> Dict[str, Any]:
        self.ensure_project()
        issue = self._get_issue_node(issue_number)
        variables = {
            "projectId": self.project_id,
            "contentId": issue["id"],
        }
        data = self._graphql(MUTATION_ADD_ISSUE, variables)
        return data["addProjectV2ItemById"]["item"]

    def add_note(self, note: str) -> Dict[str, Any]:
        self.ensure_project()
        variables = {"projectId": self.project_id, "note": note}
        data = self._graphql(MUTATION_ADD_NOTE, variables)
        return data["addProjectV2Item"]["item"]

    def update_field(self, item_id: str, field_name: str, value: str) -> Dict[str, Any]:
        self.ensure_project()
        field = self.fields.get(field_name.lower())
        if not field:
            raise KeyError(f"Field '{field_name}' not found on project {self.project_title}")
        payload = self._build_field_payload(field, value)
        variables = {"itemId": item_id, "fieldId": field["id"], "value": payload}
        data = self._graphql(MUTATION_UPDATE_FIELD, variables)
        return data["updateProjectV2ItemFieldValue"]["item"]

    def _build_field_payload(self, field: Dict[str, Any], value: str) -> Any:
        data_type = field["dataType"]
        if data_type == "SINGLE_SELECT":
            return {"name": value}
        if data_type == "NUMBER":
            return float(value)
        if data_type == "DATE":
            return value
        return value

    def sync_issue_record(self, issue_number: int) -> Optional[str]:
        self.ensure_project()
        records_dir = Path(self.config["record_dir"])
        record_path = records_dir / f"issue-{issue_number}.json"
        if not record_path.exists():
            raise FileNotFoundError(f"Issue record not found: {record_path}")
        items = self.list_items()
        for item in items:
            content = item["content"]
            if content["issue"] and content["issue"]["number"] == issue_number:
                return item["id"]
        self.add_issue(issue_number)
        return None

    def _get_issue_node(self, issue_number: int) -> Dict[str, Any]:
        data = self._graphql(
            ISSUE_NODE_QUERY,
            {
                "owner": self.config["owner"],
                "name": self.config["repo"],
                "number": issue_number,
            },
        )
        issue = data["repository"]["issue"]
        if not issue:
            raise ValueError(f"Issue #{issue_number} not found in {self.config['repo']}")
        return issue


def _load_manager(config: Path) -> GitHubProjectManager:
    return GitHubProjectManager(config)


def _print_items(manager: GitHubProjectManager) -> None:
    items = manager.list_items()
    for item in items:
        line = f"{item['id']}:"
        issue = item["content"]["issue"]
        if issue:
            line += f" issue #{issue['number']} ({issue['title']})"
        elif item["note"]:
            line += f" note: {item['note'][:40]}"
        else:
            line += " empty"
        if item["fields"]:
            fields = ", ".join(f"{f['name']}={f['singleSelect'] or f['value']}" for f in item["fields"])
            line += f" | {fields}"
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage a GitHub Projects (Beta) board via GraphQL."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("GitHubProject/config.json"),
        help="Path to the project configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List the first page of project items.")

    add_issue = subparsers.add_parser("add-issue", help="Add an issue to the project.")
    add_issue.add_argument("--issue", type=int, required=True, help="GitHub issue number.")

    add_note = subparsers.add_parser("add-note", help="Create a note item.")
    add_note.add_argument("--note", required=True, help="Text content for the note.")

    update = subparsers.add_parser("update-field", help="Update a field value on an item.")
    update.add_argument("--item-id", required=True, help="Project item ID.")
    update.add_argument("--field", required=True, help="Field name (case insensitive).")
    update.add_argument("--value", required=True, help="New value for the field.")

    sync = subparsers.add_parser("sync-record", help="Ensure a local issue record is on the board.")
    sync.add_argument("--issue", type=int, required=True, help="Issue number that must exist at Issues/records.")

    args = parser.parse_args()
    try:
        manager = _load_manager(args.config)
        if args.command == "list":
            _print_items(manager)
        elif args.command == "add-issue":
            item = manager.add_issue(args.issue)
            print(json.dumps(item, indent=2))
        elif args.command == "add-note":
            item = manager.add_note(args.note)
            print(json.dumps(item, indent=2))
        elif args.command == "update-field":
            item = manager.update_field(args.item_id, args.field, args.value)
            print(json.dumps(item, indent=2))
        elif args.command == "sync-record":
            found = manager.sync_issue_record(args.issue)
            if found:
                print(f"Issue #{args.issue} already exists as item {found}")
            else:
                print(f"Issue #{args.issue} added to project.")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
