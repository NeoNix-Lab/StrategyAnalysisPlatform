#!/usr/bin/env python3
"""
Serialize GitHub issue event payloads into the Issues/ directory so the workflows
can treat it as a lightweight issue database.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Iterable


ROOT = Path(__file__).resolve().parent
RECORDS_DIR = ROOT / "records"
WORKFLOW_DIR = ROOT / "workflows"
INDEX_FILE = ROOT / "index.json"
LOG_FILE = WORKFLOW_DIR / "issue-events.log"


def load_event() -> Dict[str, Any]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is not set")

    event_path = Path(event_path)
    if not event_path.exists():
        raise FileNotFoundError(f"GitHub event payload not found at {event_path}")

    with event_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def extract_labels(labels_payload: Iterable[Any]) -> List[str]:
    labels: List[str] = []
    for entry in labels_payload:
        if isinstance(entry, str):
            labels.append(entry)
        elif isinstance(entry, Mapping):
            name = entry.get("name")
            if name:
                labels.append(name)
    return labels


def build_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    issue = payload.get("issue")
    action = payload.get("action")
    sender = payload.get("sender", {}).get("login")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "issues")
    repository = payload.get("repository", {}).get("full_name")

    record: Dict[str, Any] = {
        "event": event_name,
        "action": action,
        "repository": repository,
        "sender": sender,
        "event_timestamp": datetime.utcnow().isoformat() + "Z",
        "issue": {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "body": issue.get("body"),
            "state": issue.get("state"),
            "html_url": issue.get("html_url"),
            "labels": extract_labels(issue.get("labels", [])),
            "assignees": [
                assignee.get("login")
                for assignee in issue.get("assignees", [])
                if assignee.get("login")
            ],
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "closed_at": issue.get("closed_at"),
        },
    }

    return record


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def update_index(record: Dict[str, Any]) -> None:
    index_data: Dict[str, Any] = {}
    if INDEX_FILE.exists():
        with INDEX_FILE.open("r", encoding="utf-8") as fh:
            index_data = json.load(fh)

    issue = record["issue"]
    issue_number = issue.get("number")
    if issue_number is None:
        return

    index_data[str(issue_number)] = {
        "title": issue.get("title"),
        "state": issue.get("state"),
        "labels": issue.get("labels"),
        "assignees": issue.get("assignees"),
        "last_action": record.get("action"),
        "last_updated": record.get("event_timestamp"),
        "html_url": issue.get("html_url"),
    }

    write_json(INDEX_FILE, index_data)


def append_log(record: Dict[str, Any]) -> None:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = record["event_timestamp"]
    issue_number = record["issue"].get("number")
    line = f"{timestamp} | issue #{issue_number} | {record.get('action')} | {record.get('sender')}\n"
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line)


def main() -> None:
    payload = load_event()
    issue = payload.get("issue")
    if not issue:
        print("Issue payload missing, nothing to persist.")
        return

    record = build_record(payload)

    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    issue_path = RECORDS_DIR / f"issue-{issue.get('number')}.json"
    write_json(issue_path, record)

    update_index(record)
    append_log(record)


if __name__ == "__main__":
    main()
