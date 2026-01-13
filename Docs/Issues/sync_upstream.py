#!/usr/bin/env python3
"""
Sync local issue files to GitHub.
Usage: python3 sync_upstream.py [files...]

If no files are provided, it can optionally scan for everything (not implemented for safety).
Designed to be called with a list of changed files from the git commit.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # e.g. "owner/repo"
API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}" if GITHUB_REPOSITORY else None

def get_headers() -> Dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

def create_issue(title: str, body: Optional[str], labels: List[str], assignees: List[str]) -> Dict[str, Any]:
    url = f"{API_URL}/issues"
    payload = {
        "title": title,
        "body": body or "",
        "labels": labels,
        "assignees": assignees
    }
    resp = requests.post(url, headers=get_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

def update_issue(number: int, title: Optional[str], body: Optional[str], state: Optional[str], labels: Optional[List[str]], assignees: Optional[List[str]]) -> Dict[str, Any]:
    url = f"{API_URL}/issues/{number}"
    payload: Dict[str, Any] = {}
    if title: payload["title"] = title
    if body: payload["body"] = body
    if state: payload["state"] = state
    if labels is not None: payload["labels"] = labels
    if assignees is not None: payload["assignees"] = assignees
    
    resp = requests.patch(url, headers=get_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

def process_file(file_path: Path) -> None:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        return

    # Normalize data
    # The record format is: { "issue": { "title": ..., "body": ... } }
    # OR simpler format if user just wrote a JSON. We support the schema from update_issue_record.py
    
    issue_data = data.get("issue", data) # Support both wrapped and unwrapped
    
    # Validation
    title = issue_data.get("title")
    if not title:
        print(f"Skipping {file_path}: No title found.")
        return

    body = issue_data.get("body")
    labels = issue_data.get("labels", [])
    # Normalize labels: if they are objects {"name": "bug"}, extract names
    labels = [l["name"] if isinstance(l, dict) else l for l in labels]
    
    assignees = issue_data.get("assignees", [])
    assignees = [a["login"] if isinstance(a, dict) else a for a in assignees]
    
    state = issue_data.get("state") # open/closed

    number = issue_data.get("number")
    
    if number:
        print(f"Updating Issue #{number} from {file_path}")
        update_issue(number, title, body, state, labels, assignees)
    else:
        print(f"Creating New Issue from {file_path}")
        new_issue = create_issue(title, body, labels, assignees)
        new_number = new_issue["number"]
        print(f"Created Issue #{new_number}")
        
        # Rewrite the file with the new complete record to allow renaming
        # We fetch the full record structure equivalent to what update_issue_record.py produces
        # But here valid JSON is enough. The 'download' workflow will clean it up later.
        # Ideally, we rename it NOW so the workflow can commit the rename.
        
        # Let's inject the number back into the file so the next step (renaming) knows what to do
        # Or better: rename it right here? 
        # The script is running in the runner. If we rename here, we must rely on 'git add' later finding it.
        
        # Strategy: Write a fully compliant record back
        full_record = {
            "event": "manual_push",
            "action": "created",
            "repository": GITHUB_REPOSITORY,
            "issue": new_issue # This comes straight from GitHub API, matches schema
        }
        
        # Determine new filename, enforcing the records/ directory
        img_dir = file_path.parent
        # If the script is run from root, file_path might be Issues/foo.json.
        # We want Issues/records/issue-{number}.json
        # We assume the structure is standard.
        records_dir = file_path.parent / "records"
        if not records_dir.exists():
            # Fallback if we are already inside records or looking at a flat structure?
            # Ideally we look for the 'records' sibling or child.
            # But simpler: if file_path is "Issues/draft.json", parent is "Issues". "Issues/records" exists.
            if (file_path.parent.name == "Issues"):
                 records_dir = file_path.parent / "records"
            else:
                 # If we are somehow elsewhere, just default to same dir for safety, or try to find ROOT.
                 records_dir = file_path.parent
        
        # Hardcode convention: The standard location is Issues/records/
        # We can find the root "Issues" by looking at the known structure or imports.
        # Let's rely on relative path if we know where we run.
        # But safest is:
        
        new_filename = records_dir / f"issue-{new_number}.json"
        
        # Write new file
        with new_filename.open("w", encoding="utf-8") as f:
            json.dump(full_record, f, indent=2, ensure_ascii=False)
            
        # Delete old file
        file_path.unlink()
        print(f"Renamed {file_path} -> {new_filename}")


def main():
    if not API_URL:
        print("GITHUB_REPOSITORY not set, skipping sync.")
        return

    files = sys.argv[1:]
    if not files:
        print("No files provided to sync.")
        return

    for f in files:
        path = Path(f)
        if path.suffix == ".json" and path.exists():
            print(f"Processing {path}...")
            process_file(path)

if __name__ == "__main__":
    main()
