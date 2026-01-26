# Quick Start Guide

## Installation

### Clone the Repository

The `cyberedu-client` is included as a git submodule:

```bash
git clone --recursive https://github.com/CyberEDU-Cyber-Range/cyberedu-mcp.git
cd cyberedu-mcp
```

If you already cloned without `--recursive`:

```bash
git submodule update --init --recursive
```

### Install Packages

**macOS/Linux:**
```bash
python3 -m venv venv  
source venv/bin/activate
pip install -e ./cyberedu-client
pip install -e .
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ./cyberedu-client
pip install -e .
```

## Configuration

### Option 1: Session Persistence (Recommended)

No configuration needed! Once the server is running, use the `cyberedu_set_session_cookie` tool to authenticate. Your credentials are saved and persist across sessions.

**Session file location:**
- macOS/Linux: `~/.cyberedu-mcp/session.json`
- Windows: `%USERPROFILE%\.cyberedu-mcp\session.json`

### Option 2: Environment Variables

Alternatively, set environment variables:

```bash
export CYBEREDU_SESSION_COOKIE="your_session_cookie_here"
export CYBEREDU_TENANT="cyberedu"  # optional
```

## Running the Server

```bash
python -m cyberedu_mcp
```

## Using with MCP Clients

### Cursor IDE

Cursor supports MCP servers through its settings. To configure the CyberEdu MCP server:

1. **Open Cursor Settings**:
   - Go to **Cursor Settings** → **Features** → **MCP**
   - Or use `Cmd+,` (macOS) / `Ctrl+,` (Windows/Linux) and search for "MCP"

2. **Add New MCP Server**:
   - Click **"+ Add New MCP Server"**
   - Fill in the following:
     - **Name**: `cyberedu` (or any name you prefer)
     - **Type**: Select `stdio`
     - **Command**: Full path to the venv Python (e.g., `/path/to/cyberedu-mcp/venv/bin/python3`)
     - **Arguments**: `-m cyberedu_mcp`

   **Important**: Use the full path to the Python executable in your venv. Cursor runs MCP servers externally and won't have access to an activated virtual environment.

3. **Example MCP Configuration**:
   
   macOS/Linux (`~/.cursor/mcp.json`):
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
   
   Windows (`%APPDATA%\Cursor\User\mcp.json`):
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

4. **Using MCP Tools in Cursor**:
   - MCP tools are available in **Composer** (Cursor's agent feature)
   - Open Composer with `Cmd+I` (macOS) / `Ctrl+I` (Windows/Linux)
   - The agent will automatically use relevant CyberEdu tools when appropriate
   - You'll see tool call requests that you can approve before execution

5. **Example Usage in Composer**:
   ```
   List all available challenges on CyberEdu
   ```
   The agent will automatically use the `cyberedu_list_challenges` tool.

**Note**: Session credentials are persisted to disk (`~/.cyberedu-mcp/session.json`), so no environment variables are needed after the first authentication.

### Claude Desktop

**macOS** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

**Windows** (`%APPDATA%\Claude\claude_desktop_config.json`):
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

### VS Code

Add to `.vscode/mcp.json` in your workspace:

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

### Antigravity / Windsurf

Access via MCP store → Manage MCP Servers → View raw config, then add to `mcp_config.json`:

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

## Available Tools

All public methods from `CyberEduClient` are automatically available as MCP tools with the `cyberedu_` prefix. For example:

### Session Management (new!)
- `cyberedu_get_session_status` - Check if you're authenticated
- `cyberedu_set_session_cookie` - Set your session cookie without restarting
- `cyberedu_switch_tenant` - Switch to a different tenant

### Challenge & Contest Tools
- `cyberedu_list_challenges` - List all challenges
- `cyberedu_get_challenge` - Get challenge details
- `cyberedu_submit_flag` - Submit a flag
- `cyberedu_start_service` - Start a challenge service
- `cyberedu_get_contest_ranks` - Get contest leaderboard
- And many more...

See the full README.md for a complete list.

## Session Management

You can now manage your session directly via MCP tools:

### Setting Session Cookie
If you're not logged in or your session expired:
```
Set my CyberEdu session cookie to eyJpdiI6...
```

### Switching Tenants
To switch to a different organization:
```
List my available CyberEdu tenants
```
Then:
```
Switch to CyberEdu tenant myorg
```

### Checking Status
```
What's my CyberEdu session status?
```

## Troubleshooting

### MCP Server Not Appearing in Cursor

1. **Verify Installation**: Make sure both packages are installed in the venv:
   
   macOS/Linux:
   ```bash
   cd cyberedu-mcp
   source venv/bin/activate
   pip install -e ./cyberedu-client
   pip install -e .
   ```
   
   Windows:
   ```powershell
   cd cyberedu-mcp
   .\venv\Scripts\Activate.ps1
   pip install -e ./cyberedu-client
   pip install -e .
   ```

2. **Check Python Path**: Use the full path to the venv Python in Cursor's MCP config:
   
   macOS/Linux:
   ```bash
   echo "$(pwd)/venv/bin/python3"
   ```
   
   Windows (PowerShell):
   ```powershell
   Write-Output "$PWD\venv\Scripts\python.exe"
   ```

3. **Test Server Manually**: Run the server directly to check for errors:
   
   macOS/Linux:
   ```bash
   source venv/bin/activate
   python -m cyberedu_mcp
   ```
   
   Windows:
   ```powershell
   .\venv\Scripts\Activate.ps1
   python -m cyberedu_mcp
   ```

4. **Verify MCP Config**: Check your MCP config uses the correct venv path:
   - macOS/Linux: `~/.cursor/mcp.json`
   - Windows: `%APPDATA%\Cursor\User\mcp.json`

### Session Cookie Expired

If you get authentication errors, your session cookie may have expired:
1. Log in to https://app.cyber-edu.co in your browser
2. Get a fresh `cyberedu_session` cookie from developer tools
3. Use `cyberedu_set_session_cookie` to update (persists automatically)
   - Or update the `CYBEREDU_SESSION_COOKIE` environment variable in Cursor's MCP settings
