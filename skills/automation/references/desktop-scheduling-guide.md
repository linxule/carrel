# Desktop App Scheduling Guide

Step-by-step instructions for setting up Carrel's overnight agent via Claude Desktop App local scheduled tasks.

## Primary Path: Desktop App Local Tasks

### Prerequisites
- Claude Desktop App installed and running
- Carrel plugin installed
- Automation configured via `/carrel-automate` (prompt saved to `_meta/automation-prompt.md`)

### Setup Steps

1. Open **Claude Desktop**
2. Navigate to the **Schedule** tab (sidebar or menu)
3. Click **New local task**
4. Open `_meta/automation-prompt.md` in your text editor or Obsidian
5. Copy the entire prompt content
6. Paste into the task prompt field in Claude Desktop
7. Set the schedule:
   - **Daily**: choose a time (e.g., 2:00 AM)
   - **Weekdays**: Monday-Friday at chosen time
   - **Weekly**: choose a day and time
8. Set the model: **Sonnet** (default) or **Opus** (if chosen during `/carrel-automate`)
9. Save the task

### Behavior Notes

- The Desktop App must be running for scheduled tasks to fire
- Set the app to **launch on login** for reliability
- If the machine is off when a task is scheduled, the app runs **one catch-up** when it next opens
- Each scheduled run creates a new session with its own checkpoint history (important for trust levels 3-4 undo)

### Updating the Schedule

When you change preferences via `/carrel-automate`:
1. The prompt at `_meta/automation-prompt.md` is regenerated
2. Open Claude Desktop → Schedule tab → find your Carrel task
3. Replace the prompt with the new content from `_meta/automation-prompt.md`
4. Adjust schedule/model if needed

## Fallback: `claude -p` + Cron

For power users who prefer terminal-based automation.

### Prerequisites
- Claude CLI installed
- Anthropic API key configured (`ANTHROPIC_API_KEY` environment variable)
- Terminal/cron familiarity

### Setup

1. Create a shell script:

```bash
#!/bin/bash
cd /path/to/your/vault
claude -p "$(cat _meta/automation-prompt.md)"
```

2. Make it executable: `chmod +x run-carrel-overnight.sh`

3. Add a crontab entry:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/run-carrel-overnight.sh >> /tmp/carrel-overnight.log 2>&1
```

### Trade-offs vs Desktop App

| | Desktop App | `claude -p` + cron |
|---|---|---|
| API key required | No (uses subscription) | Yes |
| Setup complexity | GUI, low friction | Terminal, higher friction |
| Persistence | Survives restarts (app must run) | Always-on (system cron) |
| Checkpoint history | Full session checkpoints | One-shot, no checkpoints |
| Cost model | Subscription-based | Pay-per-use API |

For most researchers, the Desktop App path is strongly recommended.
