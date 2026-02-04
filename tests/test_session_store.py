"""
Tests for SessionStore - session persistence.
"""

from cyberedu_mcp.session_store import SessionStore, _resolve_session_file_path


class TestSessionStore:
    """SessionStore load, save, clear, update."""

    def test_load_returns_empty_when_file_missing(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        # File was created empty by NamedTemporaryFile - clear it or use fresh path
        if store.session_file.exists():
            store.session_file.unlink()
        assert store.load() == {}

    def test_save_and_load_roundtrip(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        state = {"session_cookie": "test-cookie", "tenant": "myorg"}
        assert store.save(state) is True
        assert store.load() == state

    def test_update_merges_and_persists(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        store.save({"session_cookie": "old", "tenant": "cyberedu"})
        assert store.update(tenant="unbreakable") is True
        loaded = store.load()
        assert loaded["tenant"] == "unbreakable"
        assert loaded["session_cookie"] == "old"

    def test_clear_removes_file(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        store.save({"session_cookie": "x", "tenant": "y"})
        assert store.session_file.exists()
        assert store.clear() is True
        assert not store.session_file.exists()

    def test_get_session_cookie_returns_stored_value(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        store.save({"session_cookie": "abc123", "tenant": "cyberedu"})
        assert store.get_session_cookie() == "abc123"

    def test_get_session_cookie_returns_none_when_empty(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        store.save({"tenant": "cyberedu"})
        assert store.get_session_cookie() is None

    def test_get_tenant_returns_default_when_empty(self, session_store_with_temp_file):
        store = session_store_with_temp_file
        assert store.get_tenant() == "cyberedu"

    def test_load_returns_empty_on_invalid_json(self, temp_session_file):
        temp_session_file.write_text("not valid json {")
        store = SessionStore(session_file=temp_session_file)
        assert store.load() == {}


class TestSessionFileResolution:
    """Session file path resolution."""

    def test_cyberedu_session_file_env_override(self, monkeypatch):
        """CYBEREDU_SESSION_FILE env var overrides default path."""
        custom_path = "/custom/session.json"
        monkeypatch.setenv("CYBEREDU_SESSION_FILE", custom_path)
        resolved = _resolve_session_file_path()
        assert resolved.name == "session.json"
        assert "custom" in str(resolved)
