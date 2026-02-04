"""
Compliance tests: verify the codebase adheres to extending checklists and docs.

These tests map to documented requirements. When updating:
- cyberedu-client/docs/extending.md (Checklist for New Endpoints)
- docs/extending.md (Checklist for New Tools, Security)

Update the corresponding test when changing a checklist item.
"""

import inspect
import json
from typing import get_type_hints

import pytest

from cyberedu_client import CyberEduClient
from cyberedu_mcp.server import CUSTOM_TOOLS, handle_call_tool
from cyberedu_mcp.tool_registry import ToolRegistry

# =============================================================================
# Client: cyberedu-client/docs/extending.md - Checklist for New Endpoints
# =============================================================================


class TestClientExtendingChecklist:
    """
    Validates CyberEduClient complies with extending.md checklist.

    Checklist: Method has docstring with Args/Returns, uses _make_request or
    explains why not, handles 400 for flags, returns dict for MCP.
    """

    def test_public_methods_with_params_have_args_section(self):
        """
        Checklist: Method has docstring with Args/Returns (extending.md).
        Methods with parameters must document them for MCP tool discovery.
        """
        registry = ToolRegistry()
        registry.discover_from_class(CyberEduClient)
        missing = []
        for meta in registry.list_methods():
            method = getattr(CyberEduClient, meta.name, None)
            if method is None:
                continue
            doc = inspect.getdoc(method)
            assert doc, f"{meta.name} must have a docstring"
            sig = inspect.signature(method)
            params = [p for p in sig.parameters if p != "self"]
            if not params:
                continue
            doc_lower = doc.lower()
            if "args:" not in doc_lower and "parameters:" not in doc_lower:
                missing.append(meta.name)
        assert not missing, (
            f"Per extending.md checklist, these methods need Args: section: "
            f"{', '.join(missing)}. See cyberedu-client/docs/extending.md"
        )

    def test_public_methods_return_dict_or_bytes(self):
        """Checklist: Returns dict (not custom objects) for MCP compatibility."""
        registry = ToolRegistry()
        registry.discover_from_class(CyberEduClient)
        for meta in registry.list_methods():
            method = getattr(CyberEduClient, meta.name, None)
            if method is None:
                continue
            hints = get_type_hints(method) if hasattr(method, "__annotations__") else {}
            return_hint = hints.get("return", None)
            if return_hint is None:
                continue
            hint_str = str(return_hint)
            # Allow Dict, dict, List (for list_contests), Union[bytes, Dict] (download)
            assert (
                "dict" in hint_str.lower()
                or "bytes" in hint_str.lower()
                or "list" in hint_str.lower()
            ), f"{meta.name} should return Dict/bytes/List for MCP (got {return_hint})"

    def test_flag_submission_handles_400(self):
        """Checklist: Handles expected error codes (like 400 for wrong flags)."""
        client = CyberEduClient(tenant="cyberedu")
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"status": "failed", "solved": False}
        result = client._parse_flag_submission_response(mock_resp)
        assert isinstance(result, dict)
        assert "status" in result

    def test_client_methods_have_type_hints(self):
        """Checklist: Type hints on all parameters (docs/extending.md)."""
        registry = ToolRegistry()
        registry.discover_from_class(CyberEduClient)
        for meta in registry.list_methods():
            method = getattr(CyberEduClient, meta.name, None)
            if method is None:
                continue
            sig = inspect.signature(method)
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                if param.annotation == inspect.Parameter.empty:
                    pytest.fail(f"{meta.name}({name}) should have type hint (extending checklist)")


# =============================================================================
# Server: docs/extending.md — Security & Custom Tools
# =============================================================================


class TestSessionStatusSecurity:
    """Security: Never return session_cookie in get_session_status."""

    @pytest.mark.asyncio
    async def test_get_session_status_never_returns_cookie_value(self, isolated_session_for_server):
        """Security rule: Never return session_cookie in API responses."""
        await handle_call_tool("cyberedu_set_session_cookie", {"session_cookie": "secret123"})
        result = await handle_call_tool("cyberedu_get_session_status", {})
        parsed = json.loads(result[0].text)
        assert "session_cookie" not in parsed
        assert "secret" not in str(parsed).lower()


class TestCustomToolsChecklist:
    """Checklist for New Tools: Returns JSON-serializable dict, structured errors."""

    def test_custom_tools_return_json_serializable(self, isolated_session_for_server):
        """Checklist: Returns JSON-serializable dict."""
        for name, info in CUSTOM_TOOLS.items():
            func = info["function"]
            if name == "get_session_status":
                result = func()
            elif name == "clear_session":
                result = func()
            elif name == "set_session_cookie":
                result = func("test-value")
            elif name == "switch_tenant":
                result = func("cyberedu")
            else:
                continue
            json_str = json.dumps(result, default=str)
            assert isinstance(json.loads(json_str), dict)

    def test_custom_tools_have_required_schema(self):
        """Checklist: parameters schema has type, properties, required."""
        for name, info in CUSTOM_TOOLS.items():
            params = info["parameters"]
            assert params.get("type") == "object"
            assert "properties" in params
            assert "required" in params


# =============================================================================
# Doc compliance: list_tools script runs (docs/extending.md - Testing Changes)
# =============================================================================


class TestDocInstructionsWork:
    """Verify documented commands and patterns actually work."""

    def test_list_tools_script_imports(self):
        """Docs: 'python list_tools.py' - verify imports work."""
        from cyberedu_mcp.server import CUSTOM_TOOLS
        from cyberedu_mcp.tool_registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_from_class(CyberEduClient)
        tools = list(CUSTOM_TOOLS.keys()) + [m.name for m in registry.list_methods()]
        assert len(tools) > 0
