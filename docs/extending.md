# Extending the MCP Server

## Important: You Probably Don't Need to Modify This

The MCP server is designed to be **zero-maintenance**. If the `CyberEduClient` is properly developed:

- **New methods are automatically discovered** at startup via introspection
- **JSON schemas are auto-generated** from type hints and docstrings
- **No MCP code changes required** when adding client functionality

**When to modify the MCP server:**
- Adding session/state management tools (not related to API calls)
- Customizing tool descriptions for better AI guidance
- Changing discovery behavior (excluding methods, custom categories)

For most use cases, just add methods to `CyberEduClient` and restart the MCP server.

---

## Adding Tools via CyberEduClient (Recommended)

The easiest way to add new tools is to add methods to `CyberEduClient` in the `cyberedu-client` package:

```python
# In cyberedu_client/cyberedu_client.py
def new_feature(self, param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Description of the new feature.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        
    Returns:
        Result dictionary
    """
    response = self._make_request('GET', f'/v1/new-endpoint/{param1}')
    response.raise_for_status()
    return response.json()
```

The MCP server will automatically:
- Discover the method at startup
- Generate JSON schema from signature and type hints
- Extract description from docstring
- Expose it as `cyberedu_new_feature`

## Adding Custom MCP Tools

For tools that don't map to client methods (e.g., session management):

### Step 1: Define the Function

```python
# In server.py
def my_custom_tool(param1: str) -> Dict[str, Any]:
    """
    Tool description for AI models.
    
    Args:
        param1: Parameter description
        
    Returns:
        Result dictionary
    """
    # Implementation
    return {"result": "success", "data": param1}
```

### Step 2: Register in CUSTOM_TOOLS

```python
CUSTOM_TOOLS = {
    # ... existing tools ...
    "my_custom_tool": {
        "function": my_custom_tool,
        "description": (
            "Detailed description with examples and usage hints. "
            "This helps AI models understand when and how to use the tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "What this parameter does"
                }
            },
            "required": ["param1"]
        }
    }
}
```

### Step 3: Tool is Automatically Available

The tool will be listed as `cyberedu_my_custom_tool` and handled in `handle_call_tool`.

## Using the Tool Registry Directly

For more advanced use cases, register tools directly with the registry:

```python
from cyberedu_mcp.tool_registry import ToolRegistry

registry = ToolRegistry()

def advanced_tool(data: dict, options: list) -> dict:
    """Advanced tool with complex parameters."""
    return {"processed": True}

registry.register_method(
    name="advanced_tool",
    method=advanced_tool,
    description="An advanced tool",
    parameters={
        "type": "object",
        "properties": {
            "data": {"type": "object", "description": "Input data"},
            "options": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["data"]
    },
    category="custom"
)
```

## Modifying Tool Discovery

### Excluding Methods

Add method names to `_excluded_methods` in `ToolRegistry`:

```python
class ToolRegistry:
    def __init__(self):
        self._excluded_methods = {
            # ... existing exclusions ...
            'method_to_hide',
        }
```

### Custom Category Logic

Modify `_determine_category` to change how tools are categorized:

```python
def _determine_category(self, method_name: str) -> str:
    if 'my_feature' in method_name:
        return 'my_category'
    # ... rest of logic ...
```

## Modifying Session Persistence

### Custom Storage Location

```python
from cyberedu_mcp.session_store import SessionStore
from pathlib import Path

# Use custom location
store = SessionStore(session_file=Path("/custom/path/session.json"))
```

### Adding Session Fields

To persist additional state:

```python
# When updating
_session_store.update(
    session_cookie=cookie,
    tenant=tenant,
    custom_field="value"  # New field
)

# When loading
stored = _session_store.load()
custom_value = stored.get("custom_field")
```

## Best Practices

### Tool Descriptions

Write descriptions that help AI models:

```python
# Good: Specific, actionable, includes context
"description": (
    "Submit a flag/answer for an archive challenge. "
    "Use challenge_id and flag_id from get_challenge response. "
    "Returns {status: 'success'|'failed', solved: bool}. "
    "Example: submit_flag(challenge_id='abc', flag_id='123', flag_value='CTF{...}')"
)

# Bad: Vague, no context
"description": "Submit a flag"
```

### Parameter Descriptions

Provide context for each parameter:

```python
"properties": {
    "challenge_id": {
        "type": "string",
        "description": "Challenge ID (UUID format, get from list_challenges or get_challenge)"
    },
    "save_path": {
        "type": "string",
        "description": "Optional path to save file. If directory, uses original filename."
    }
}
```

### Error Returns

Return structured errors with actionable information:

```python
def my_tool(...):
    if not valid_input:
        return {
            "error": "InvalidInput",
            "message": "Param must be X format",
            "hint": "Try using Y instead"
        }
```

## Testing Changes

### List Available Tools

```bash
python list_tools.py
```

### Test Tool Execution

Create a test script:

```python
from cyberedu_mcp.server import handle_call_tool
import asyncio

async def test():
    result = await handle_call_tool("cyberedu_my_custom_tool", {"param1": "test"})
    print(result[0].text)

asyncio.run(test())
```

## Checklist for New Tools

- [ ] Method has docstring with Args/Returns
- [ ] Type hints on all parameters
- [ ] Description is detailed and includes examples
- [ ] Returns JSON-serializable dict
- [ ] Error cases return structured error dicts
- [ ] Added to README.md tool list
- [ ] Tested with MCP client
