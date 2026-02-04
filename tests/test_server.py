"""
Tests for MCP server - tool listing and tool calls.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cyberedu_mcp.server import (
    _format_tool_result_as_json,
    handle_call_tool,
    handle_list_tools,
)


class TestHandleListTools:
    """MCP tool listing."""

    @pytest.mark.asyncio
    async def test_returns_tools_with_cyberedu_prefix(self):
        tools = await handle_list_tools()
        assert len(tools) > 0
        names = [t.name for t in tools]
        assert all(n.startswith("cyberedu_") for n in names)

    @pytest.mark.asyncio
    async def test_includes_session_management_tools(self):
        tools = await handle_list_tools()
        names = [t.name for t in tools]
        assert "cyberedu_get_session_status" in names
        assert "cyberedu_set_session_cookie" in names
        assert "cyberedu_switch_tenant" in names

    @pytest.mark.asyncio
    async def test_includes_client_tools(self):
        tools = await handle_list_tools()
        names = [t.name for t in tools]
        assert "cyberedu_list_challenges" in names
        assert "cyberedu_list_trainings" in names


class TestHandleCallTool:
    """MCP tool invocation."""

    @pytest.mark.asyncio
    async def test_get_session_status_returns_valid_json(self, isolated_session_for_server):
        result = await handle_call_tool("cyberedu_get_session_status", {})
        assert len(result) == 1
        text = result[0].text
        parsed = json.loads(text)
        assert "authenticated" in parsed
        assert "tenant" in parsed
        assert "persisted" in parsed

    @pytest.mark.asyncio
    async def test_switch_tenant_updates_session(self, isolated_session_for_server):
        result = await handle_call_tool("cyberedu_switch_tenant", {"tenant": "unbreakable"})
        assert len(result) == 1
        parsed = json.loads(result[0].text)
        assert parsed.get("status") == "success"
        assert parsed.get("current_tenant") == "unbreakable"

        # Verify get_session_status reflects the switch
        status_result = await handle_call_tool("cyberedu_get_session_status", {})
        status_parsed = json.loads(status_result[0].text)
        assert status_parsed.get("tenant") == "unbreakable"

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error_json(self):
        result = await handle_call_tool("cyberedu_nonexistent_tool", {})
        assert len(result) == 1
        parsed = json.loads(result[0].text)
        assert parsed.get("error") == "ValueError"
        assert "not found" in parsed.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_set_session_cookie_persists(self, isolated_session_for_server):
        result = await handle_call_tool(
            "cyberedu_set_session_cookie", {"session_cookie": "test-cookie-123"}
        )
        parsed = json.loads(result[0].text)
        assert parsed.get("status") == "success"
        assert parsed.get("persisted") is True

        status_result = await handle_call_tool("cyberedu_get_session_status", {})
        status_parsed = json.loads(status_result[0].text)
        assert status_parsed.get("authenticated") is True

    @pytest.mark.asyncio
    async def test_clear_session_removes_credentials(self, isolated_session_for_server):
        # First set a cookie
        await handle_call_tool("cyberedu_set_session_cookie", {"session_cookie": "to-be-cleared"})
        # Then clear
        result = await handle_call_tool("cyberedu_clear_session", {})
        parsed = json.loads(result[0].text)
        assert parsed.get("status") == "success"

    @pytest.mark.asyncio
    async def test_http_401_returns_error_without_response_body(self):
        """Security: 401/403 must not leak API response body."""
        mock_client = MagicMock()
        mock_client.list_challenges.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(
                status_code=401,
                text="sensitive internal error details",
            ),
        )

        with patch("cyberedu_mcp.server.get_client", return_value=mock_client):
            result = await handle_call_tool("cyberedu_list_challenges", {})

        parsed = json.loads(result[0].text)
        assert parsed["error"] == "HTTP Error"
        assert parsed["status_code"] == 401
        assert parsed.get("session_expired") is True
        assert "remedy" in parsed
        # Must NOT include response body (security)
        assert "sensitive" not in parsed.get("message", "")
        assert "response" not in parsed

    @pytest.mark.asyncio
    async def test_value_error_auth_includes_remedy(self):
        """ValueError for auth should include remedy for user."""
        with patch(
            "cyberedu_mcp.server.get_client",
            side_effect=ValueError("Not authenticated. Please use session cookie."),
        ):
            result = await handle_call_tool("cyberedu_list_challenges", {})

        parsed = json.loads(result[0].text)
        assert parsed["error"] == "ValueError"
        assert "remedy" in parsed
        assert "cyberedu_set_session_cookie" in parsed["remedy"]


class TestFormatToolResultAsJson:
    """_format_tool_result_as_json."""

    def test_formats_dict(self):
        result = _format_tool_result_as_json({"key": "value"})
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_formats_bytes_as_file_download(self):
        result = _format_tool_result_as_json(b"file content")
        parsed = json.loads(result)
        assert parsed["type"] == "file_download"
        assert parsed["size_bytes"] == 12

    def test_formats_file_saved_dict(self):
        result = _format_tool_result_as_json(
            {"success": True, "path": "/tmp/file.txt", "size": 100}
        )
        parsed = json.loads(result)
        assert parsed["type"] == "file_saved"
        assert parsed["path"] == "/tmp/file.txt"
        assert parsed["size_bytes"] == 100
