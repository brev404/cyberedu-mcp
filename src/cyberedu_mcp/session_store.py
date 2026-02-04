"""
Session persistence for CyberEdu MCP Server.

Stores session state (cookie, tenant) to disk so it persists across MCP sessions.
The state is saved to:
- Unix/macOS: ~/.cyberedu-mcp/session.json
- Windows: %USERPROFILE%\\.cyberedu-mcp\\session.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Default location for session storage
# Path.home() works cross-platform:
# - Unix/macOS: /home/user or /Users/user
# - Windows: C:\\Users\\username
# Override with CYBEREDU_SESSION_FILE env var if needed (e.g. for MCP sandbox)
def _get_session_file() -> Path:
    if path := os.environ.get("CYBEREDU_SESSION_FILE"):
        return Path(path)
    return Path.home() / ".cyberedu-mcp" / "session.json"


DEFAULT_SESSION_FILE = _get_session_file()


class SessionStore:
    """
    Manages persistent session storage for the CyberEdu MCP server.
    
    Session state is saved to disk and loaded on startup, allowing the
    session cookie and tenant selection to persist across MCP sessions.
    """
    
    def __init__(self, session_file: Optional[Path] = None):
        """
        Initialize the session store.
        
        Args:
            session_file: Optional custom path for session file.
                         Defaults to ~/.cyberedu-mcp/session.json
        """
        self.session_file = session_file or _get_session_file()
        self._ensure_dir()
    
    def _ensure_dir(self) -> None:
        """Ensure the session directory exists."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """
        Load session state from disk.
        
        Returns:
            Dict with session state (session_cookie, tenant, etc.)
            Returns empty dict if file doesn't exist or is invalid.
        """
        if not self.session_file.exists():
            return {}
        
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate it's a dict
                if isinstance(data, dict):
                    return data
                return {}
        except (json.JSONDecodeError, IOError, OSError):
            # Return empty state on any read/parse error
            return {}
    
    def save(self, state: Dict[str, Any]) -> bool:
        """
        Save session state to disk.
        
        Args:
            state: Dict with session state to persist
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            self._ensure_dir()
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            # Set restrictive permissions (owner read/write only) for security
            # On Windows, os.chmod only supports read-only flag, so we skip it
            if sys.platform != "win32":
                os.chmod(self.session_file, 0o600)
            return True
        except (IOError, OSError):
            return False
    
    def clear(self) -> bool:
        """
        Clear stored session (delete session file).
        
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            return True
        except OSError:
            return False
    
    def get_session_cookie(self) -> Optional[str]:
        """Get stored session cookie, or None if not set."""
        state = self.load()
        return state.get("session_cookie")
    
    def get_tenant(self) -> str:
        """Get stored tenant, defaults to 'cyberedu'."""
        state = self.load()
        return state.get("tenant", "cyberedu")
    
    def update(self, **kwargs) -> bool:
        """
        Update specific fields in the session state.
        
        Args:
            **kwargs: Fields to update (session_cookie, tenant, etc.)
            
        Returns:
            True if update was successful
        """
        state = self.load()
        state.update(kwargs)
        return self.save(state)


# Global session store instance
_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create the global session store instance."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
