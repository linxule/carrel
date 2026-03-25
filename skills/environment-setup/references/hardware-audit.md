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

Structure results as JSON for environment.json:

```json
{
  "system": {
    "os": "macOS",
    "os_version": "15.4",
    "arch": "arm64",
    "ram_gb": 36,
    "disk_free_gb": 120,
    "gpu": "Apple M3 Max"
  },
  "tools": {
    "node": { "installed": true, "version": "22.1.0" },
    "python": { "installed": true, "version": "3.12.4" },
    "pandoc": { "installed": true, "version": "3.1.12" },
    "ffmpeg": { "installed": false },
    "obsidian": { "installed": true },
    "zotero": { "installed": false },
    "brew": { "installed": true }
  },
  "existing_mcps": {
    "claude_desktop": [],
    "claude_code_user": [],
    "project": []
  }
}
```

## How to Present

Never dump this on the researcher. Summarize conversationally:

**Good:** "You're running a Mac with Apple Silicon and 36 GB of RAM — that's great, it means we can run most tools locally without any cloud services. I found Node.js and Pandoc already installed, so document conversion will work right away."

**Bad:** "System audit complete. Darwin arm64, 36864 MB RAM, node v22.1.0 detected..."

If something important is missing (like Node.js), explain what it means and offer to install it:

"I notice Node.js isn't installed yet — that's a small program that some of our tools need to run. I can install it for you now if you'd like. It takes about a minute."
