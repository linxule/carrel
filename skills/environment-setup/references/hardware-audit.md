# Hardware & Tools Audit

Run silently during setup. The researcher should NOT see raw terminal output.

## What to Check

### System Info
```bash
# OS and architecture
uname -s        # Darwin, Linux, MINGW (Windows)
uname -m        # arm64 (Apple Silicon), x86_64 (Intel)

# macOS specific
sw_vers         # macOS version
sysctl -n hw.memsize   # RAM in bytes (divide by 1073741824 for GB)
system_profiler SPDisplaysDataType 2>/dev/null | grep "Chipset Model"  # GPU

# Disk space
df -h .         # Available space in project directory
```

### Installed Tools
```bash
# Core dependencies
which node && node --version      # Node.js (needed for MCPs)
which python3 && python3 --version  # Python (needed for some tools)
which uv && uv --version          # uv package manager
which bun && bun --version        # Bun runtime

# Conversion tools
which pandoc && pandoc --version  # Document conversion
which ffmpeg && ffmpeg -version   # Audio/video processing

# Research tools
which zotero                      # Zotero desktop app
mdfind "kMDItemCFBundleIdentifier == 'md.obsidian'" 2>/dev/null  # Obsidian app (macOS)

# Brew (macOS)
which brew && brew --version      # Homebrew available?
```

### Existing MCP Configuration
```bash
# Claude Desktop MCPs
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json 2>/dev/null

# Claude Code MCPs (user-level)
cat ~/.claude/settings.json 2>/dev/null | grep -A5 mcpServers

# Project-level MCPs
cat .mcp.json 2>/dev/null
```

## Output Format

`carrel env doctor --format json` serializes the `AuditResult` Pydantic model, not `environment.json`.

```json
{
  "os": "macOS",
  "arch": "arm64",
  "os_version": "15.4",
  "ram_gb": 36,
  "disk_free": "120Gi",
  "hardware_capability": "high",
  "tools": {
    "binaries": {
      "node": {
        "installed": true,
        "version": "v22.1.0",
        "path": "/opt/homebrew/bin/node"
      },
      "ffmpeg": {
        "installed": false,
        "version": null,
        "path": null
      },
      "obsidian": {
        "installed": true,
        "version": null,
        "path": "/Applications/Obsidian.app"
      }
    },
    "api_keys": {
      "mineru": {
        "configured": false,
        "env_var": "MINERU_API_KEY"
      },
      "groq": {
        "configured": true,
        "env_var": "GROQ_API_KEY"
      }
    },
    "mcp_servers": ["zotero", "vox"]
  }
}
```

Notes:
- `hardware_capability` is one of `high`, `medium`, or `low`.
- `tools.binaries` is a dictionary keyed by tool name (`git`, `gh`, `node`, `bun`, `python`, `uv`, `brew`, `lit`, `coli`, `defuddle`, `gws`, `markitdown`, `ffmpeg`, `pandoc`, `obsidian`, `zotero` when detected).
- Each binary entry uses the `BinaryInfo` shape: `installed`, optional `version`, optional `path`.
- `tools.api_keys` is a dictionary keyed by supported cloud tool name and uses the `ApiKeyStatus` shape: `configured`, `env_var`.
- `tools.mcp_servers` is the sorted list of project MCP server names from `.mcp.json`.

## How to Present

Never dump this on the researcher. Summarize conversationally:

**Good:** "You're running a Mac with Apple Silicon and 36 GB of RAM — that's great, it means we can run most tools locally without any cloud services. I found Node.js and Pandoc already installed, so document conversion will work right away."

**Bad:** "System audit complete. Darwin arm64, 36864 MB RAM, node v22.1.0 detected..."

If something important is missing (like Node.js), explain what it means and offer to install it:

"I notice Node.js isn't installed yet — that's a small program that some of our tools need to run. I can install it for you now if you'd like. It takes about a minute."
