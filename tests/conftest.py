"""
Pytest configuration and fixtures for cyberedu-mcp tests.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_session_file():
    """Provide a temporary session file path for isolated tests."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink(missing_ok=True)


@pytest.fixture
def session_store_with_temp_file(temp_session_file):
    """Provide a SessionStore instance using a temporary file."""
    from cyberedu_mcp.session_store import SessionStore

    return SessionStore(session_file=temp_session_file)


@pytest.fixture
def isolated_session_for_server(temp_session_file):
    """
    Isolate server tests with a temp session file.
    Resets session store singleton so server uses the temp file.
    """
    # Write initial valid session so get_session_status works
    temp_session_file.write_text('{"tenant": "cyberedu"}')

    old_env = os.environ.get("CYBEREDU_SESSION_FILE")
    os.environ["CYBEREDU_SESSION_FILE"] = str(temp_session_file)

    import cyberedu_mcp.session_store as session_store_module

    session_store_module._session_store_instance = None

    yield temp_session_file

    if old_env is not None:
        os.environ["CYBEREDU_SESSION_FILE"] = old_env
    elif "CYBEREDU_SESSION_FILE" in os.environ:
        del os.environ["CYBEREDU_SESSION_FILE"]
    session_store_module._session_store_instance = None
