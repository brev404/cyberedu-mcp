# Server Architecture

This document explains the internal design of the CyberEdu MCP server.

## Design Principles

1. **Dynamic Discovery**: Tools are discovered from `CyberEduClient` at startup, not hardcoded
2. **Separation of Concerns**: Server logic, tool discovery, and session storage are separate modules
3. **Lazy Client Initialization**: `CyberEduClient` is created on first tool call, not at startup
4. **Persistence**: Session credentials survive server restarts
5. **Zero-Maintenance**: The server should not need updates when new API methods are added to the client

The key design goal is that developers only need to modify `CyberEduClient` to add new functionality. The MCP server automatically discovers and exposes new methods without code changes.

## Module Structure

```
server.py          - MCP server, request handling, custom tools
tool_registry.py   - Method discovery and schema generation
session_store.py   - Persistent session storage
```

## Request Flow

```
MCP Client
    │
    ▼
handle_call_tool(name, arguments)
    │
    ├─► Is custom tool? (session management)
    │       └─► Call CUSTOM_TOOLS[name]["function"](**args)
    │
    └─► Is discovered tool?
            │
            ├─► get_client() → creates/returns CyberEduClient
            │
            └─► getattr(client, method_name)(**args)
                    │
                    ▼
              httpx.Response → JSON → TextContent
```

## Tool Discovery Process

The `ToolRegistry` scans `CyberEduClient` using Python introspection:

```python
# In tool_registry.py
def discover_from_class(cls, prefix=""):
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith('_') or name in excluded_methods:
            continue
        
        sig = inspect.signature(method)
        hints = get_type_hints(method)
        
        # Build JSON schema from signature
        parameters = build_parameter_schema(sig, hints)
        
        # Extract description from docstring
        description = extract_description(method.__doc__)
        
        # Register the method
        registry._methods[name] = MethodMetadata(...)
```

### Excluded Methods

These methods are not exposed as tools:
- Private methods (`_*`)
- Helper methods (`_get_headers`, `_make_request`, etc.)
- Context manager methods (`__enter__`, `__exit__`, `close`)
- `set_session_cookie` (custom tool handles this with persistence)

### Schema Generation

Python types are mapped to JSON schema:

| Python Type | JSON Schema |
|-------------|-------------|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list`, `List[T]` | `{"type": "array"}` |
| `dict`, `Dict[K,V]` | `{"type": "object"}` |
| `Optional[T]` | Type of `T` (not required) |

## Session Management

### SessionStore

Manages persistent storage at `~/.cyberedu-mcp/session.json`:

```python
class SessionStore:
    def load() -> Dict        # Load from disk
    def save(state: Dict)     # Save to disk
    def update(**kwargs)      # Partial update
    def clear()               # Delete session file
```

The file has restrictive permissions (`0o600`) for security.

### Session State Flow

```
Startup:
    1. Load from ~/.cyberedu-mcp/session.json
    2. Fall back to environment variables
    3. Default tenant: "cyberedu"

set_session_cookie() call:
    1. Update in-memory state
    2. Persist to disk
    3. Reset CyberEduClient instance

switch_tenant() call:
    1. Update in-memory state
    2. Persist to disk
    3. Reset CyberEduClient instance
```

### Client Lifecycle

```python
_client: Optional[CyberEduClient] = None

def get_client(require_auth=True):
    global _client
    
    # Check if tenant/cookie changed → reset client
    if _client and (tenant_changed or cookie_changed):
        _client.close()
        _client = None
    
    # Create new client if needed
    if _client is None:
        _client = CyberEduClient(tenant, session_cookie)
    
    return _client
```

## Custom Tools

Session management tools are defined separately from discovered tools:

```python
CUSTOM_TOOLS = {
    "get_session_status": {
        "function": get_session_status,
        "description": "...",
        "parameters": {"type": "object", "properties": {...}}
    },
    "set_session_cookie": {...},
    "switch_tenant": {...},
    "clear_session": {...}
}
```

These have enhanced descriptions with examples and workflow hints.

## Tool Listing

When `list_tools` is called:

```python
@server.list_tools()
async def handle_list_tools():
    tools = []
    
    # Add custom tools first (session management)
    for name, info in CUSTOM_TOOLS.items():
        tools.append(Tool(name=f"cyberedu_{name}", ...))
    
    # Add discovered tools from registry
    for metadata in registry.list_methods():
        tools.append(Tool(name=f"cyberedu_{metadata.name}", ...))
    
    return tools
```

## Error Handling

The server provides structured error responses:

```python
# HTTP errors (from CyberEduClient)
except httpx.HTTPStatusError as e:
    return {"error": "HTTP Error", "status_code": e.response.status_code, ...}

# All other errors
except Exception as e:
    return {"error": type(e).__name__, "message": str(e)}
```

## Server Instructions

The server provides instructions to help AI models use it effectively:

```python
SERVER_INSTRUCTIONS = """
CyberEdu MCP Server - CTF Platform Integration
...
## IMPORTANT: Before Any Action
ALWAYS call `cyberedu_get_session_status` FIRST...
...
"""
```

These instructions are included in the MCP server metadata.
