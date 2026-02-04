"""
Dynamic MCP Server for CyberEdu Client

This server automatically discovers all public methods from CyberEduClient
and exposes them as MCP tools. New methods can be added to CyberEduClient
without modifying this MCP server code.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import the CyberEduClient
# Try to import from installed package first, then fall back to submodule path
try:
    from cyberedu_client import CyberEduClient
except ImportError:
    # Try alternative import path for development (submodule location)
    # Go up from src/cyberedu_mcp/ to project root, then to cyberedu-client/src
    client_path = Path(__file__).parent.parent.parent / "cyberedu-client" / "src"
    if str(client_path) not in sys.path:
        sys.path.insert(0, str(client_path))
    from cyberedu_client import CyberEduClient

from .tool_registry import ToolRegistry
from .session_store import get_session_store

# =============================================================================
# MCP Server Instructions
# =============================================================================
# These instructions help AI models understand what this server does and how
# to use it effectively.

SERVER_INSTRUCTIONS = """
CyberEdu MCP Server - CTF Platform Integration

This server provides tools to interact with the CyberEdu CTF (Capture The Flag) platform.
You can browse challenges, download files, submit flags, and manage challenge services.

## IMPORTANT: Before Any Action
ALWAYS call `cyberedu_get_session_status` FIRST before using any other CyberEdu tools. This will tell you:
1. Whether you are authenticated (have a valid session cookie)
2. Which tenant/organization is currently selected
3. Whether credentials are persisted to disk

If not authenticated, ask the user for their session cookie and use `cyberedu_set_session_cookie`.
The session cookie can be obtained from browser dev tools after logging into https://app.cyber-edu.co

## Session Expired (401/403 errors)
When any API call returns HTTP 401 or 403, the session cookie has likely expired. Tell the user to:
1. Log in again at https://app.cyber-edu.co
2. Open Developer Tools (F12) > Application > Cookies > cyberedu_session
3. Copy the cookie value and provide it to you
4. You then call `cyberedu_set_session_cookie` with the new value

Session credentials are persisted to disk, so once set, they will be available in future sessions.

## Common Workflows

### Exploring Challenges (Educational Archive)
1. `cyberedu_list_challenges` - Browse all available challenges (can filter by category/difficulty)
2. `cyberedu_list_top_challenges` - Get top N most solved/attempted challenges for current tenant.
   Use for "top 10 solved", leaderboard-style queries. Call cyberedu_switch_tenant first for
   a specific org (e.g., unbreakable). Params: limit (default 10), sort_by (solves/attempts/points)
3. `cyberedu_get_challenge` - Get details including description, files, and flags
4. `cyberedu_download_file` - Download challenge files (use `save_path` param to save to disk)
5. `cyberedu_start_service` - Start the challenge instance if it requires a running service
6. `cyberedu_submit_flag` - Submit your solution

### Trainings (Structured Courses)
Trainings are courses with modules (text, images, files, deployments). Same flow as challenges:
list → get details → subscribe → download → deployment. Tenant applies: use cyberedu_switch_tenant first.
1. `cyberedu_list_trainings` - List trainings for current tenant (courses like HeapVault)
2. `cyberedu_get_training` - Get full training with modules (content_html, media, files, deployment).
   Accepts training_id (UUID) or slug (e.g. 'heapvault-training').
3. `cyberedu_subscribe_to_training` - Unlock the training (required before content/deployment)
4. `cyberedu_download_training_file` - Download module files. file_id comes from module's files/media.
   Use training_id (UUID), not slug.
5. `cyberedu_start_training_service` - Start the training deployment (lab instance)
6. `cyberedu_get_training_service_status` - Check deployment status
7. `cyberedu_wait_for_training_service` - Poll until deployment is ready (optional convenience)
8. `cyberedu_extend_training_service` / `cyberedu_restart_training_service` - Manage deployment

If a module has a challenge_id (in its deployment/challenge field), use cyberedu_start_service
with that challenge_id for module-level lab instances.

### Working with Contests/Events
1. `cyberedu_list_contests` - See available contests
2. `cyberedu_get_contest` - Get contest details and challenges
3. `cyberedu_get_contest_challenge` - Get specific challenge in a contest
4. `cyberedu_get_contest_ranks` - View the leaderboard
5. `cyberedu_submit_contest_flag` - Submit flags for contest challenges

### Managing Services/Deployments
- `cyberedu_start_service` / `cyberedu_start_contest_service` - Start a challenge instance
- `cyberedu_get_service_status` / `cyberedu_get_contest_service_status` - Check if running
- `cyberedu_extend_service` - Extend the running time before it expires
- `cyberedu_restart_service` - Restart if something went wrong

### Multi-Tenant Support
- `cyberedu_list_tenants` - See available organizations
- `cyberedu_switch_tenant` - Switch to a different organization

**Important Notes on Tenant Behavior:**
- Use `cyberedu_switch_tenant` first to select organization (e.g., unbreakable, cyberedu)
- All challenge and training tools use the current tenant
- Challenge count, solve counts (counts.owned), and tenant field are tenant-specific
- Training availability varies by tenant (unbreakable often has more; cyberedu may have fewer)

## Important Notes
- Challenge IDs and file IDs are UUIDs (e.g., '9fcc0a82-40bb-4073-9bd3-bb993823ab70')
- Contest slugs are URL-friendly names (e.g., 'unr24-echipe-final')
- Flags are typically in format CTF{...} or similar
- Services have time limits and need to be extended or restarted
"""

# Create server instance
server = Server("cyberedu-mcp")

# Global registry and client
registry = ToolRegistry()
_client: Optional[CyberEduClient] = None

# Initialize session store for persistence
_session_store = get_session_store()

# Session state - loads from persistent storage, then env vars as fallback
# Priority: 1) Persistent storage, 2) Environment variables, 3) Defaults
_stored_state = _session_store.load()
_session_state = {
    "session_cookie": _stored_state.get("session_cookie") or os.getenv("CYBEREDU_SESSION_COOKIE"),
    "tenant": _stored_state.get("tenant") or os.getenv("CYBEREDU_TENANT", "cyberedu"),
}


def get_client(require_auth: bool = True) -> CyberEduClient:
    """Get or create the CyberEduClient instance."""
    global _client

    # Reload session from disk to ensure we use latest persisted tenant/cookie
    stored = _session_store.load()
    if stored:
        if "session_cookie" in stored:
            _session_state["session_cookie"] = stored["session_cookie"]
        if "tenant" in stored:
            _session_state["tenant"] = stored["tenant"]

    session_cookie = _session_state.get("session_cookie")
    tenant = _session_state.get("tenant", "cyberedu")

    # Check if we need to recreate the client (tenant or cookie changed)
    if _client is not None:
        if _client.tenant != tenant or _client.session_cookie != session_cookie:
            _client.close()
            _client = None

    if _client is None:
        if require_auth and not session_cookie:
            raise ValueError(
                "Not authenticated. Please use 'cyberedu_set_session_cookie' to set your session cookie. "
                "Get it from your browser's developer tools after logging in to "
                "https://app.cyber-edu.co and copy the 'cyberedu_session' cookie value."
            )

        _client = CyberEduClient(tenant=tenant, session_cookie=session_cookie or "")

    return _client


def set_session_cookie(session_cookie: str) -> Dict[str, Any]:
    """
    Set the session cookie for authentication.

    This allows you to authenticate without restarting the MCP server.
    The cookie is persisted to disk (~/.cyberedu-mcp/session.json) and will
    be automatically loaded in future sessions.

    Get your session cookie from browser developer tools after logging in
    to https://app.cyber-edu.co (look for the 'cyberedu_session' cookie).

    Args:
        session_cookie: The cyberedu_session cookie value from your browser

    Returns:
        Status message indicating success
    """
    global _client

    _session_state["session_cookie"] = session_cookie

    # Persist to disk for future sessions
    _session_store.update(session_cookie=session_cookie, tenant=_session_state["tenant"])

    # Reset client so it will be recreated with new cookie
    if _client is not None:
        _client.close()
        _client = None

    return {
        "status": "success",
        "message": "Session cookie updated and persisted to disk. You can now use CyberEdu API tools.",
        "tenant": _session_state["tenant"],
        "persisted": True,
    }


def switch_tenant(tenant: str) -> Dict[str, Any]:
    """
    Switch to a different tenant.

    Use this to change which tenant/organization you're working with.
    The tenant selection is persisted to disk for future sessions.
    You can list available tenants using 'cyberedu_list_tenants'.

    Args:
        tenant: The tenant slug/identifier to switch to (e.g., 'cyberedu', 'myorg')

    Returns:
        Status message indicating the tenant switch
    """
    global _client

    old_tenant = _session_state["tenant"]
    _session_state["tenant"] = tenant

    # Persist to disk for future sessions
    _session_store.update(tenant=tenant)

    # Reset client so it will be recreated with new tenant
    if _client is not None:
        _client.close()
        _client = None

    return {
        "status": "success",
        "message": f"Switched tenant from '{old_tenant}' to '{tenant}'",
        "previous_tenant": old_tenant,
        "current_tenant": tenant,
        "persisted": True,
    }


def get_session_status() -> Dict[str, Any]:
    """
    Get current session status.

    Shows whether you're authenticated, which tenant is selected, and
    whether credentials are persisted to disk.

    Returns:
        Current session status including authentication state, tenant, and persistence info
    """
    # Reload from disk to ensure we report actual persisted state
    stored = _session_store.load()
    if stored:
        if "session_cookie" in stored:
            _session_state["session_cookie"] = stored["session_cookie"]
        if "tenant" in stored:
            _session_state["tenant"] = stored["tenant"]

    has_cookie = bool(_session_state.get("session_cookie"))
    tenant = _session_state.get("tenant", "cyberedu")
    has_persisted_cookie = bool(stored.get("session_cookie"))

    return {
        "authenticated": has_cookie,
        "tenant": tenant,
        "persisted": has_persisted_cookie,
        "session_file": str(_session_store.session_file),
        "message": (
            "Authenticated"
            if has_cookie
            else "Not authenticated. Use 'cyberedu_set_session_cookie' to authenticate."
        ),
    }


def clear_session() -> Dict[str, Any]:
    """
    Clear stored session credentials from disk.

    This removes the persisted session cookie and tenant from disk.
    The current in-memory session remains active until the MCP server restarts.
    Use this when you want to remove stored credentials for security.

    Returns:
        Status message indicating success
    """
    global _client

    success = _session_store.clear()

    # Also clear in-memory state
    _session_state["session_cookie"] = None
    _session_state["tenant"] = "cyberedu"

    # Reset client
    if _client is not None:
        _client.close()
        _client = None

    return {
        "status": "success" if success else "error",
        "message": (
            "Session credentials cleared from disk and memory."
            if success
            else "Failed to clear session file."
        ),
        "session_file": str(_session_store.session_file),
    }


# =============================================================================
# Custom MCP Tools with Enhanced Descriptions
# =============================================================================
# These tools have detailed descriptions with examples and workflow hints
# to help AI models understand how to use them effectively.

CUSTOM_TOOLS = {
    "get_session_status": {
        "function": get_session_status,
        "description": (
            "Check authentication and tenant. ALWAYS call this FIRST before other CyberEdu tools. "
            "Returns: authenticated (bool), tenant (string), persisted (bool). "
            "If authenticated=false, use cyberedu_set_session_cookie (user provides cookie from browser). "
            "If API calls return 401/403 later, session expired - ask user for new cookie, then set_session_cookie."
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "set_session_cookie": {
        "function": set_session_cookie,
        "description": (
            "Set the session cookie for authentication. Use when: (1) not authenticated, or (2) any API call "
            "returns 401/403 (session expired). Ask the user to get the cookie from their browser: "
            "Developer Tools (F12) > Application > Cookies > app.cyber-edu.co > cyberedu_session. "
            "Then call this with the value. Persists to disk for future sessions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "session_cookie": {
                    "type": "string",
                    "description": "The cyberedu_session cookie value from browser dev tools after logging into https://app.cyber-edu.co",
                }
            },
            "required": ["session_cookie"],
        },
    },
    "switch_tenant": {
        "function": switch_tenant,
        "description": (
            "Switch to a different tenant/organization. "
            "First use 'cyberedu_list_tenants' to see available options with their slugs. "
            "Example: switch_tenant(tenant='myorg')"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tenant": {
                    "type": "string",
                    "description": "The tenant slug/identifier (e.g., 'cyberedu', 'myorg'). Get available slugs from list_tenants.",
                }
            },
            "required": ["tenant"],
        },
    },
    "clear_session": {
        "function": clear_session,
        "description": (
            "Clear stored session credentials from disk and memory. "
            "Use this to remove persisted authentication for security. "
            "After clearing, you'll need to re-authenticate with 'cyberedu_set_session_cookie'."
        ),
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


# Discover tools from CyberEduClient
registry.discover_from_class(CyberEduClient, prefix="")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List all available tools (discovered from CyberEduClient methods + custom tools).

    Returns:
        List of Tool objects
    """
    tools = []

    # Add custom tools first (session management)
    for name, tool_info in CUSTOM_TOOLS.items():
        tool = Tool(
            name=f"cyberedu_{name}",
            description=tool_info["description"],
            inputSchema=tool_info["parameters"],
        )
        tools.append(tool)

    # Add discovered tools from CyberEduClient
    for metadata in registry.list_methods():
        tool = Tool(
            name=f"cyberedu_{metadata.name}",
            description=metadata.description,
            inputSchema=metadata.parameters,
        )
        tools.append(tool)

    return tools


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[Dict[str, Any]] = None
) -> List[TextContent]:
    """
    Call a tool by name with the provided arguments.

    Args:
        name: Tool name (prefixed with 'cyberedu_')
        arguments: Tool arguments (optional, defaults to empty dict)

    Returns:
        List of TextContent with the result
    """
    if arguments is None:
        arguments = {}

    # Remove prefix
    if name.startswith("cyberedu_"):
        method_name = name[len("cyberedu_") :]
    else:
        method_name = name

    try:
        # Check if it's a custom tool first
        if method_name in CUSTOM_TOOLS:
            custom_func = CUSTOM_TOOLS[method_name]["function"]
            result = custom_func(**arguments)
            result_str = json.dumps(result, indent=2, default=str)
            return [TextContent(type="text", text=result_str)]

        # Check if it's a discovered method from CyberEduClient
        metadata = registry.get_method(method_name)
        if not metadata:
            available = list(CUSTOM_TOOLS.keys()) + [m.name for m in registry.list_methods()]
            raise ValueError(
                f"Tool {name} not found. Available tools: {['cyberedu_' + t for t in available]}"
            )

        # Get client instance (this will fail gracefully if not authenticated)
        client = get_client()

        # Get the method from the instance (bound method)
        instance_method = getattr(client, method_name)
        result = instance_method(**arguments)

        # Convert result to JSON string
        if isinstance(result, bytes):
            # For file downloads returned as bytes (no save_path specified)
            result_str = json.dumps(
                {
                    "type": "file_download",
                    "size_bytes": len(result),
                    "message": "File downloaded successfully. Use the 'save_path' parameter to save directly to disk.",
                },
                indent=2,
            )
        elif isinstance(result, dict) and result.get("success") and "path" in result:
            # For file downloads saved to disk (save_path was specified)
            result_str = json.dumps(
                {
                    "type": "file_saved",
                    "path": result["path"],
                    "size_bytes": result.get("size", 0),
                    "message": f"File saved successfully to: {result['path']}",
                },
                indent=2,
            )
        else:
            result_str = json.dumps(result, indent=2, default=str)

        return [TextContent(type="text", text=result_str)]

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        error_msg: Dict[str, Any] = {
            "error": "HTTP Error",
            "status_code": status,
            "message": str(e),
        }
        # Do not include API response body for auth errors (401/403) to avoid
        # leaking any sensitive info the API might return
        if status not in (401, 403) and e.response.text:
            error_msg["response"] = e.response.text[:500]
        if status in (401, 403):
            error_msg["session_expired"] = True
            error_msg["remedy"] = (
                "Session cookie likely expired. Ask user to log in at https://app.cyber-edu.co, "
                "get cyberedu_session cookie from Developer Tools > Application > Cookies, "
                "then call cyberedu_set_session_cookie with the new value."
            )
        return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]

    except ValueError as e:
        msg = str(e)
        error_msg = {"error": "ValueError", "message": msg}
        if "not authenticated" in msg.lower() or "session" in msg.lower():
            error_msg["remedy"] = (
                "Ask user for cyberedu_session cookie from https://app.cyber-edu.co "
                "(Developer Tools > Application > Cookies), then call cyberedu_set_session_cookie."
            )
        return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]
    except Exception as e:
        error_msg = {"error": type(e).__name__, "message": str(e)}
        return [TextContent(type="text", text=json.dumps(error_msg, indent=2))]


async def main():
    """Main entry point for the MCP server."""
    init_options = server.create_initialization_options()
    init_options = init_options.model_copy(update={"instructions": SERVER_INSTRUCTIONS.strip()})
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
