# GitHub Project Setup & Management Guide

This guide describes how to initialize the remote repository, set up the GitHub Project (V2/Beta) board, and configure the integrated tooling for issue tracking.

## 1. Repository Initialization

If you have not yet pushed this code to GitHub:

1.  **Create a New Repository** on [GitHub](https://github.com/new).
    *   Do *not* verify "Initialize with README" (you already have one).
2.  **Push Local Code**:
    ```bash
    git init
    # Ensure .gitignore is set up correctly
    git add .
    git commit -m "Initial commit: Strategy Analysis Platform V2"
    git branch -M main
    git remote add origin https://github.com/<YOUR_USER>/<YOUR_REPO>.git
    git push -u origin main
    ```

## 2. GitHub Actions Permissions

To allow the **Issue Tracking Automation** (`issue-tracking.yml`) to work (which saves issue snapshots back to the repo):

1.  Go to **Settings** > **Actions** > **General**.
2.  Under **Workflow permissions**, select **"Read and write permissions"**.
3.  (Optional) Check "Allow GitHub Actions to create and approve pull requests".
4.  Click **Save**.

*Note: This allows the `github-actions[bot]` to commit JSON records to the `Issues/` folder whenever an issue is created or updated.*

## 3. GitHub Projects (Beta) Setup

This project contains tooling (`GitHubProject/manage_project.py`) to interact with a GitHub Project V2 board. This is useful for Kanban management triggered by scripts.

### Step A: Create the Board
1.  Go to your GitHub Profile or Organization -> **Projects**.
2.  Click **New Project** and select **Table** or **Board** (Beta/V2).
3.  Title it "Strategy Platform Tasks".
4.  Note the **Project Number**. You can find this in the URL (e.g., `.../projects/1` -> Number is `1`).

### Step B: Configure Local Tooling
1.  Copy the template config:
    ```bash
    cp GitHubProject/config.template.json GitHubProject/config.json
    ```
    *If no template exists, create `GitHubProject/config.json` with:*
    ```json
    {
      "owner": "<YOUR_GITHUB_USERNAME>",
      "repo": "<YOUR_REPO_NAME>",
      "project_number": 1,
      "items_page_size": 50,
      "record_dir": "Issues/records"
    }
    ```
2.  **Do NOT commit** your `config.json` if it contains private data (though `owner/repo` are usually public). Ideally, add `GitHubProject/config.json` to `.gitignore` to be safe.

### Step C: Generate a Personal Access Token (PAT)
The `manage_project.py` script requires a token to talk to the GitHub GraphQL API. The default `GITHUB_TOKEN` in CI works for repo contents but may need extra scopes for Projects.

1.  Go to **Settings** > **Developer settings** > **Personal access tokens**.
2.  **Fine-grained tokens (Recommended)**:
    *   Target: Your user/org.
    *   Repository access: Select the repo.
    *   Permissions:
        *   `Issues` (Read/Write)
        *   `Projects` (Read/Write) - *Crucial for the script*
3.  Copy the token string.

## 4. Using the Project Manager Tool

You can now use the helper script to sync issues or manage cards from your terminal.

```bash
# 1. Set the Token (PowerShell)
$env:GITHUB_TOKEN="your_token_here"

# 2. Add an Issue to the Board
python GitHubProject/manage_project.py add-issue --issue 12

# 3. Add a Custom Note
python GitHubProject/manage_project.py add-note --note "Review Architecture for Sprint 5"

# 4. List Items
python GitHubProject/manage_project.py list
```

## 5. Workflow Summary

1.  **Create Issue on GitHub**: You (or CI) open an issue.
2.  **Auto-Persist**: The `issue-tracking` workflow runs, parsing the issue and saving `Issues/records/issue-123.json`.
3.  **Local Sync**: When you `git pull`, you get the latest JSON record of that issue locally.
4.  **(Optional) Project Sync**: You run `manage_project.py sync-record --issue 123` to force that issue onto your specific Project Board if it isn't there already.

This setup ensures your code and your task tracking are tightly coupled and version-controlled.
