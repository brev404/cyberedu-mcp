# CyberEdu MCP Server Documentation

This documentation covers the CyberEdu MCP server internals, design decisions, and extension guidelines.

## Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | Server design, tool discovery, and session management |
| [Extending the Server](./extending.md) | How to add custom tools and modify behavior |

## Quick Reference

### Installation

The `cyberedu-client` is included as a git submodule:

```bash
git clone --recursive https://github.com/CyberEDU-Cyber-Range/cyberedu-mcp.git
cd cyberedu-mcp

# Install both packages
pip install -e ./cyberedu-client
pip install -e .
```

### Running the Server

```bash
source venv/bin/activate
python -m cyberedu_mcp
```

### MCP Client Configuration

Use the full path to the venv Python in your MCP config:

**Cursor IDE / Claude Desktop:**
```json
{
  "mcpServers": {
    "cyberedu": {
      "command": "/path/to/cyberedu-mcp/venv/bin/python3",
      "args": ["-m", "cyberedu_mcp"]
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "cyberedu": {
      "type": "stdio",
      "command": "/path/to/cyberedu-mcp/venv/bin/python3",
      "args": ["-m", "cyberedu_mcp"]
    }
  }
}
```

**Antigravity / Windsurf** (`mcp_config.json`):
```json
{
  "mcpServers": {
    "cyberedu": {
      "command": "/path/to/cyberedu-mcp/venv/bin/python3",
      "args": ["-m", "cyberedu_mcp"],
      "env": {}
    }
  }
}
```

Session credentials are persisted to `~/.cyberedu-mcp/session.json` after first authentication.

## Core Concepts

1. **Dynamic Tool Discovery**: All `CyberEduClient` public methods are automatically exposed as MCP tools
2. **Zero Configuration**: Adding methods to the client automatically makes them available as tools
3. **Session Persistence**: Credentials are stored in `~/.cyberedu-mcp/session.json`
4. **Prefix Convention**: All tools are prefixed with `cyberedu_` to avoid conflicts

> **Note**: The MCP server should not require modifications when extending functionality. If the `CyberEduClient` is properly developed with type hints and docstrings, new methods are automatically discovered and exposed as tools. See [Extending the Server](./extending.md) for edge cases where modifications might be desired.

### Tool Categories

| Category | Examples |
|----------|----------|
| Session Management | `get_session_status`, `set_session_cookie`, `switch_tenant` |
| Authentication | `check_auth`, `list_tenants`, `get_user_info` |
| Challenges | `list_challenges`, `get_challenge`, `subscribe_to_challenge` |
| Trainings | `list_trainings`, `get_training`, `subscribe_to_training`, `start_training_service` |
| Flags | `get_flag`, `submit_flag` |
| Files | `download_file`, `download_contest_file`, `download_training_file` |
| Services | `start_service`, `get_service_status`, `extend_service` |
| Contests | `list_contests`, `get_contest`, `get_contest_ranks` |

### Credential Priority

The server loads credentials in this order:
1. Persisted storage (`~/.cyberedu-mcp/session.json`)
2. Environment variables (`CYBEREDU_SESSION_COOKIE`, `CYBEREDU_TENANT`)
3. Defaults (tenant: `cyberedu`)

## Project Structure

```
cyberedu-mcp/
├── cyberedu-client/        # Git submodule (CyberEdu API client)
├── src/cyberedu_mcp/
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point for `python -m cyberedu_mcp`
│   ├── server.py          # Main MCP server, tool handlers, custom tools
│   ├── tool_registry.py   # Dynamic method discovery and registration
│   └── session_store.py   # Persistent session storage
├── docs/                   # This documentation
├── list_tools.py          # Utility to list available tools
└── README.md              # Usage guide
```

## Relationship to CyberEdu Client

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                             │
│  ┌───────────────┐    ┌──────────────────────────────────┐  │
│  │ Custom Tools  │    │       Tool Registry              │  │
│  │ (session mgmt)│    │  ┌─────────────────────────────┐ │  │
│  └───────┬───────┘    │  │ Discovered from CyberEduClient │ │
│          │            │  │ - list_challenges            │ │  │
│          │            │  │ - get_challenge              │ │  │
│          │            │  │ - submit_flag                │ │  │
│          │            │  │ - ...                        │ │  │
│          │            │  └─────────────────────────────┘ │  │
│          │            └──────────────┬───────────────────┘  │
│          │                           │                      │
│          ▼                           ▼                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              CyberEduClient Instance                  │  │
│  │         (from cyberedu-client package)                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

The MCP server is a thin wrapper that:
- Discovers methods from `CyberEduClient`
- Exposes them as MCP tools
- Manages session state and authentication
- Handles request/response serialization
