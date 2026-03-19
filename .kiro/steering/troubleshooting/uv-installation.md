---
inclusion: manual
---

# UV Package Manager Installation

## Context
UV is required for MCP server installation. This guide helps resolve UV installation issues.

## Diagnostic Steps
1. Check if UV is installed: `uv --version`
2. Check PATH: `which uv` (macOS/Linux) or `where uv` (Windows)

## Installation Instructions

### macOS and Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If curl is unavailable:
```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Post-Installation: IDE Restart Required

**CRITICAL**: After installation, the IDE must be fully restarted to pick up PATH changes. "Reload Window" does NOT work because the extension host inherits the environment from when the IDE was originally launched.

### How to Restart

Quit the IDE completely and relaunch:
- **macOS**: Press `Cmd+Q` to quit, then reopen
- **Windows**: Press `Alt+F4` to quit, then reopen
- **Linux**: Press `Ctrl+Q` to quit, then reopen

### MCP Server Connection Note

After restart, MCP servers will attempt to connect automatically. On first-time setup, some servers may timeout while installing dependencies (this can take longer than the default 1-minute timeout). If you see connection failures:

1. Check the MCP Server panel in the IDE sidebar
2. Click "Retry" on any failed servers
3. If problems persist after retry, describe the issue in chat and I can help troubleshoot

## Verification
After restart, verify installation:
```bash
uv --version
```

## Common Issues
- **"command not found"**: PATH not updated - restart IDE completely
- **Permission denied**: Run installer with appropriate permissions
- **Network error**: Check internet connectivity, try wget if curl fails

## Reference
- [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
