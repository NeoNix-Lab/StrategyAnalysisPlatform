
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from Issues.sync_upstream import process_file, create_issue, update_issue

# --- Fixtures ---

@pytest.fixture
def mock_env():
    # Patch the module-level variables
    with patch("Issues.sync_upstream.GITHUB_TOKEN", "fake-token"), \
         patch("Issues.sync_upstream.GITHUB_REPOSITORY", "owner/repo"), \
         patch("Issues.sync_upstream.API_URL", "https://api.github.com/repos/owner/repo"):
        yield

@pytest.fixture
def mock_requests():
    with patch("Issues.sync_upstream.requests") as m:
        yield m

# --- Tests for API calls ---

def test_create_issue_call(mock_env, mock_requests):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 101, "title": "New"}
    mock_requests.post.return_value = mock_response

    res = create_issue("Title", "Body", ["bug"], ["dev"])
    
    assert res["number"] == 101
    mock_requests.post.assert_called_once()
    args, kwargs = mock_requests.post.call_args
    assert kwargs["json"]["title"] == "Title"
    assert kwargs["json"]["body"] == "Body"
    assert kwargs["json"]["labels"] == ["bug"]

def test_update_issue_call(mock_env, mock_requests):
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 101, "title": "Updated"}
    mock_requests.patch.return_value = mock_response

    update_issue(101, "New Title", None, "closed", None, None)
    
    mock_requests.patch.assert_called_once()
    assert "manual_push" not in str(mock_requests.patch.call_args) # just checking something random? no, check payload
    args, kwargs = mock_requests.patch.call_args
    assert kwargs["json"]["title"] == "New Title"
    assert "body" not in kwargs["json"] # Should be omitted if None
    assert kwargs["json"]["state"] == "closed"


# --- Tests for File Processing ---

def test_process_file_existing_issue(mock_env, mock_requests):
    # Setup
    mock_response = MagicMock()
    mock_response.json.return_value = {"number": 55}
    mock_requests.patch.return_value = mock_response
    
    file_content = json.dumps({
        "issue": {
            "number": 55,
            "title": "Existing Issue",
            "body": "Body content",
            "state": "open"
        }
    })
    
    with patch("pathlib.Path.open", mock_open(read_data=file_content)):
        with patch("pathlib.Path.exists", return_value=True):
            p = Path("Issues/issue-55.json")
            process_file(p)
    
    mock_requests.patch.assert_called_once()
    # Confirm it extracted the number 55
    assert "issues/55" in mock_requests.patch.call_args[0][0]

def test_process_file_new_issue_renames_file(mock_env, mock_requests):
    # Setup
    mock_response = MagicMock()
    # Return what GitHub would return
    mock_response.json.return_value = {
        "number": 999, 
        "title": "New Draft",
        "html_url": "http://github.com/owner/repo/issues/999"
    }
    mock_requests.post.return_value = mock_response
    
    file_content = json.dumps({
        "title": "New Draft",
        "body": "I found a bug",
        "labels": ["triage"]
    })
    
    # We need to mock unlink and writing to new file
    with patch("pathlib.Path.open", mock_open(read_data=file_content)) as m_open:
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.unlink") as m_unlink:
                p = Path("Issues/draft.json")
                process_file(p)
                
    # 1. Check API call
    mock_requests.post.assert_called_once()
    
    # 2. Check File Renaming Logic
    # Should have opened a new file for writing
    # m_open is called for read first, then for write on the NEW path
    # But m_open is the mock object for ALL opens.
    
    # Verify unlink of old file
    m_unlink.assert_called_once()
    
    # Verify write (we can't easily check the path on the mock_open context manager result, 
    # but we can check the calls to the Path constructor or assume logic flow).
    # Actually, `new_filename.open("w", ...)` generates a call.
    # Since we patched Path.open on the class, any instance calls it.
    
    # Let's verify that we wrote the JSON with the new number
    handle = m_open()
    written_data = "".join(call.args[0] for call in handle.write.call_args_list)
    assert '"number": 999' in written_data
    assert '"event": "manual_push"' in written_data
