# CyberEdu MCP Server

This is the Oficial Model Context Protocol (MCP) server for the CyberEdu CTF platform ([https://cyber-edu.co](https://cyber-edu.co) / [https://cyberedu.ro](https://cyberedu.ro)). This server automatically discovers and exposes all methods from the `CyberEduClient` as MCP tools, making it easy to interact with the CyberEdu platform through MCP-compatible clients.

## Features

- **Dynamic Tool Discovery**: Automatically discovers all public methods from `CyberEduClient` and exposes them as MCP tools
- **Zero Configuration for New Methods**: When new methods are added to `CyberEduClient`, they automatically become available as MCP tools without any code changes
- **Type-Safe**: Automatically generates JSON schemas from method signatures and type hints
- **Error Handling**: Comprehensive error handling with detailed error messages

## CyberEDU Platform Overview

CyberEDU is a cybersecurity training platform that provides hands-on labs, realistic simulations, and competitive environments. It’s designed for enterprise security teams, academic institutions, government agencies, and
individual learners.

### Core Description

CyberEDU is a comprehensive cybersecurity training platform that provides hands-on labs, realistic simulations, and competitive environments. It's designed for enterprise security teams, academic institutions, government 
agencies, and individual learners who want to develop practical cybersecurity skills through real-world scenarios.

### Key Differentiators

- Hands-on approach: Interactive cyber ranges where users attack and defend real infrastructure (not just videos or theory)
- MITRE ATT&CK mapping: Scenarios mapped to MITRE ATT&CK, using real malware samples (safely contained)
- Better retention: 3.5x better skill retention compared to passive learning
- Real-world scenarios: Simulates actual adversary techniques and attack patterns


### Platform Components

1. Cyber Range — Enterprise-scale cyber warfare simulation with complex network topologies
2. Cyber Labs — 650+ hands-on labs mapped to MITRE ATT&CK, browser-based and auto-graded
3. Tournament Suite — Gamified competitions (CTFs, Red vs Blue, war games)


### Key Statistics

- 30,000+ active users worldwide
- 650+ hands-on labs
- 1,400+ simulation profiles
- 500+ events hosted
- 45+ countries served
- 250+ hours of training content


### Target Audiences

- Students: Career-focused training with CTF challenges and leaderboards
- Academia: Curriculum with LMS integration and auto-grading
- Enterprise: Technical hiring assessments, team training, compliance mapping
- Government: Air-gapped deployments, OT/SCADA simulation, critical infrastructure defense


### Deployment Options

- Cloud-hosted SaaS (browser-based, no installation)
- On-premise (VMware, Proxmox, bare-metal)
- Air-gapped deployments for classified environments



## Installation

### Clone the Repository

The `cyberedu-client` is included as a git submodule. Clone with `--recursive` to get everything:

```bash
git clone --recursive https://github.com/CyberEDU-Cyber-Range/cyberedu-mcp.git
cd cyberedu-mcp
```

If you already cloned without `--recursive`, initialize the submodule:

```bash
git submodule update --init --recursive
```

### Install Packages

Install both packages (client and MCP server):

**macOS/Linux:**
```bash
python3 -m venv venv  
source venv/bin/activate
pip install -e ".[local]"      # Installs with local cyberedu-client submodule
# Or for development:
# pip install -e ".[local,dev]"
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[local]"      # Installs with local cyberedu-client submodule
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -e ".[local]"
```

> **Alternative**: Install packages separately:
> ```bash
> pip install -e ./cyberedu-client
> pip install -e .
> ```

## Configuration

### Session Persistence (Recommended)

The MCP server automatically persists session credentials to disk. This means:

- **Set your cookie once** using the `cyberedu_set_session_cookie` tool, and it will be remembered across MCP sessions
- **No environment variables needed** after the first authentication
- **Tenant selection is preserved** when you switch tenants

**Session file location:**
- macOS/Linux: `~/.cyberedu-mcp/session.json`
- Windows: `%USERPROFILE%\.cyberedu-mcp\session.json` (e.g., `C:\Users\YourName\.cyberedu-mcp\session.json`)

The file has restricted permissions (owner read/write only) for security on Unix systems.

### Environment Variables (Alternative)

You can also use environment variables. The server loads credentials in this priority order:
1. Persisted credentials from disk (highest priority)
2. Environment variables
3. Defaults

Environment variables:
- `CYBEREDU_SESSION_COOKIE`: Your CyberEdu session cookie
  - Get this from your browser's developer tools after logging in to https://app.cyber-edu.co
  - Look for the `cyberedu_session` cookie value
- `CYBEREDU_TENANT`: Your tenant identifier (optional, defaults to "cyberedu")

### Getting Your Session Cookie

**Chrome/Edge:**
1. Open Developer Tools (F12)
2. Go to Application/Storage tab
3. Navigate to Cookies → `https://app.cyber-edu.co`
4. Find `cyberedu_session` and copy its value

**Firefox:**
1. Open Developer Tools (F12)
2. Go to Storage tab
3. Navigate to Cookies → `https://app.cyber-edu.co`
4. Find `cyberedu_session` and copy its value

## Usage

### Running the MCP Server

The server can be run directly (for testing):

**macOS/Linux:**
```bash
python3 -m venv venv

source venv/bin/activate
python -m cyberedu_mcp
```

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m cyberedu_mcp
```

### MCP Client Configuration

To use this server with an MCP client (Cursor IDE or Claude Desktop), add it to your MCP configuration.

**Important**: Use the full path to the Python executable in your venv. MCP clients run servers externally and won't have access to an activated virtual environment.

#### macOS/Linux Examples

**Cursor IDE** (`~/.cursor/mcp.json`):
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

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

#### Windows Examples

**Cursor IDE** (`%APPDATA%\Cursor\User\mcp.json` or `C:\Users\YourName\.cursor\mcp.json`):
```json
{
  "mcpServers": {
    "cyberedu": {
      "command": "C:\\path\\to\\cyberedu-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "cyberedu_mcp"]
    }
  }
}
```

**Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "cyberedu": {
      "command": "C:\\path\\to\\cyberedu-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "cyberedu_mcp"]
    }
  }
}
```

#### Cross-Platform Examples

**VS Code** (`.vscode/mcp.json` in your workspace):
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
*Windows: Use `C:\\path\\to\\cyberedu-mcp\\venv\\Scripts\\python.exe`*

**Antigravity / Windsurf** (`mcp_config.json` - access via MCP store → Manage MCP Servers → View raw config):
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
*Windows: Use `C:\\path\\to\\cyberedu-mcp\\venv\\Scripts\\python.exe`*

**Note**: Session credentials are persisted to `~/.cyberedu-mcp/session.json`, so no environment variables are needed after the first authentication via the `cyberedu_set_session_cookie` tool.

## Available Tools

The server automatically exposes all public methods from [https://cyber-edu.co](https://github.com/CyberEDU-Cyber-Range/cyberedu-client.git)](CyberEduClient) as MCP tools. Tools are prefixed with `cyberedu_` to avoid naming conflicts.

### Session Management Tools
These tools allow you to manage authentication and tenant switching without restarting the MCP server. Credentials are automatically persisted to `~/.cyberedu-mcp/session.json`:

- `cyberedu_get_session_status` - Check if authenticated, which tenant is selected, and if credentials are persisted
- `cyberedu_set_session_cookie` - Set/update the session cookie for authentication (persists to disk)
- `cyberedu_switch_tenant` - Switch to a different tenant/organization (persists to disk)
- `cyberedu_clear_session` - Clear stored credentials from disk and memory

**Example usage:**
1. Check status: "What's my CyberEdu session status?"
2. Set cookie: "Set my CyberEdu session cookie to `eyJ...`" (only needed once, persists!)
3. Switch tenant: "Switch to tenant `myorg`"
4. Clear credentials: "Clear my CyberEdu session"

### Authentication & User Tools
- `cyberedu_check_auth` - Verify authentication and get user info
- `cyberedu_get_user_info` - Get full user information
- `cyberedu_list_tenants` - List all available tenants
- `cyberedu_get_current_tenant_info` - Get current tenant information
- `cyberedu_get_user` - Get user information by ID

### Challenge Tools (Archive)
- `cyberedu_list_challenges` - List all challenges (with optional filters)
- `cyberedu_get_challenge` - Get challenge details
- `cyberedu_get_challenge_difficulties` - Get available difficulty levels
- `cyberedu_get_challenge_tags` - Get available challenge tags
- `cyberedu_subscribe_to_challenge` - Subscribe to a challenge

### Flag & Submission Tools (Archive)
- `cyberedu_get_flag` - Get flag/question information
- `cyberedu_submit_flag` - Submit a flag/answer

### File Tools (Archive)
- `cyberedu_download_file` - Download a challenge file (use optional `save_path` param to save directly to disk)

### Service Tools (Archive)
- `cyberedu_start_service` - Start a challenge service
- `cyberedu_get_service_status` - Get service status
- `cyberedu_extend_service` - Extend service time
- `cyberedu_restart_service` - Restart service

### Contest Tools
- `cyberedu_list_contests` - List all available contests
- `cyberedu_get_contest` - Get contest details
- `cyberedu_get_contest_ranks` - Get contest leaderboard
- `cyberedu_get_contest_challenge` - Get challenge details within a contest
- `cyberedu_subscribe_to_contest_challenge` - Subscribe to a contest challenge

### Contest Flag & Submission Tools
- `cyberedu_get_contest_flag` - Get flag information within a contest
- `cyberedu_submit_contest_flag` - Submit a flag within a contest

### Contest File Tools
- `cyberedu_download_contest_file` - Download a file from a contest challenge (use optional `save_path` param to save directly to disk)

### Contest Service Tools
- `cyberedu_start_contest_service` - Start a service within a contest
- `cyberedu_get_contest_service_status` - Get service status within a contest
- `cyberedu_extend_contest_service` - Extend service time within a contest
- `cyberedu_restart_contest_service` - Restart service within a contest

## Usage Examples & Prompts

Example prompts for interacting with the CyberEdu MCP server:

### Session & Authentication
```
"Check my CyberEdu session status"
"Set my CyberEdu session cookie to eyJpdiI6Ik..."
"Switch to tenant 'mycompany'"
```

### Challenges (Archive)
```
"List all web security challenges"
"Show me the easiest challenges from tenant unbreakable/rocsc"
"Show me hard difficulty forensics challenges"
"Get details for challenge abc123"
"Subscribe me to this challenge and start the service"
"Download challenge files to ./downloads/"
"Submit flag 'CTF{i-like-web-security-ctf-challenges}' for this challenge"
```

### Contests
```
"List available CTF contests"
"Show leaderboard for contest 'defcamp ctf quals 2025'"
"Get challenge abc123 from contest 'rocsc26-quals'"
"Start service for this contest challenge"
"Submit flag 'FLAG{solved}' for contest challenge"
```

### Workflow Example
```
1. "List easy web challenges from tenant rocsc"
2. "Subscribe to 'why-xor' and start the service"
3. "Download the challenge files"
4. [Solve...]
5. "Submit flag 'CTF{xor-is-not-safe}'"
```

## Architecture

### Dynamic Tool Discovery

The server uses Python's `inspect` module to automatically discover all public methods from the [https://cyber-edu.co](https://github.com/CyberEDU-Cyber-Range/cyberedu-client.git)](CyberEduClient) class. For each method:

1. **Method Discovery**: Scans the class for public methods (excluding private methods and helpers)
2. **Schema Generation**: Automatically generates JSON schema from method signatures and type hints
3. **Tool Registration**: Registers each method as an MCP tool with appropriate metadata

### Tool Registry

The `ToolRegistry` class provides a flexible system for managing tools:

- **Automatic Discovery**: Discovers methods from classes using introspection
- **Manual Registration**: Allows manual registration of custom methods
- **Category Organization**: Automatically categorizes methods (auth, challenges, contests, services, etc.)

### Extensibility

To add new functionality:

1. **Add methods to CyberEduClient**: Simply add new public methods to the [https://cyber-edu.co](https://github.com/CyberEDU-Cyber-Range/cyberedu-client.git)](CyberEduClient) class
2. **Automatic Exposure**: The MCP server will automatically discover and expose the new methods
3. **No MCP Code Changes**: No changes needed to the MCP server code

For custom tools that don't map directly to client methods:

```python
from cyberedu_mcp.tool_registry import ToolRegistry

registry = ToolRegistry()

def custom_tool(param1: str, param2: int) -> dict:
    """Custom tool description."""
    return {"result": f"{param1}: {param2}"}

registry.register_method(
    name="custom_tool",
    method=custom_tool,
    description="A custom tool",
    category="custom"
)
```

## Error Handling

The server provides comprehensive error handling:

- **HTTP Errors**: Returns detailed HTTP error information including status codes and response bodies
- **Validation Errors**: Returns clear error messages for missing or invalid parameters
- **Client Errors**: Returns structured error information for all exceptions

## Documentation

Additional documentation is available in the `docs/` folder:

- **[docs/index.md](docs/index.md)** - Documentation overview and quick reference
- **[docs/architecture.md](docs/architecture.md)** - Server design, tool discovery, and session management
- **[docs/extending.md](docs/extending.md)** - How to add custom tools and modify behavior


## License

MIT
