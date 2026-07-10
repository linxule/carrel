# Cowork Scheduling Guide

Reviewed against Anthropic's scheduling, local-access, and programmatic-use documentation on 2026-07-10.

## Before Scheduling

1. Configure the automation profile. This changes only `.carrel/environment.json`.
2. Generate `_meta/automation-prompt.md` separately:

   ```bash
   carrel vault automation-prompt --vault .
   ```

   Use `--force` to replace an existing generated prompt. Carrel does not create
   a `.prev` backup; copy the old prompt yourself before forcing if a comparison
   matters.
3. Decide whether the task needs a folder on the local computer. Carrel vault
   maintenance normally does.

## Primary Path: Claude Cowork

Scheduled tasks are available in Cowork on paid Claude plans. Create one in
either of these current interfaces:

- Open a Cowork task and invoke `/schedule`.
- Open **Scheduled** in the left sidebar, choose **New task**, then **Set up
  manually**.

Provide a task name, the contents of `_meta/automation-prompt.md`, a cadence
(hourly, daily, weekly, weekdays, or manual), and optionally a model and working
folder. Review the displayed task and explicitly confirm scheduling.

### Local-vault requirement

General scheduled tasks can run remotely while the computer is offline. A task
that reads or writes a local Carrel vault is different:

- Select/connect the vault folder for the task.
- Keep Claude Desktop open on that computer when the run needs local files.
- Web or mobile sessions reach connected local folders through the open Desktop
  app; if Desktop is closed, the session may continue but cannot reach those
  files.
- Do not promise catch-up execution or checkpoint-based undo. Review actual run
  history on the Scheduled page and rely on Carrel's action log and explicit
  revert instructions.

After changing Carrel automation preferences, regenerate the prompt and edit
the task instructions. Configuration does not update Cowork's saved task.

Claude scheduled-task usage counts against the researcher's paid-plan usage.
Do not quote fixed dollar estimates. Actual usage depends on plan, model,
frequency, vault size, and enabled capabilities.

Sources:

- [Schedule recurring tasks in Claude Cowork](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork)
- [Use Claude Cowork on web, desktop, and mobile](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile)

## Advanced Fallback: `claude -p` and a Scheduler

Use this only for researchers comfortable maintaining terminal automation.
`claude -p` is non-interactive Claude Code execution; it requires working
Claude Code authentication and explicit tool permissions appropriate to the
task. `--bare` skips local discovery and keychain/OAuth reads, so bare runs need
API-key or `apiKeyHelper` settings and all required context passed explicitly.

Example wrapper:

```bash
#!/bin/sh
set -eu
cd /path/to/vault
claude -p "$(cat _meta/automation-prompt.md)" \
  --allowedTools "Read,Write,Edit,Bash"
```

Schedule that wrapper with cron, launchd, Task Scheduler, or another host
scheduler. Confirm the host's environment exposes the expected authentication,
PATH, plugin, and vault permissions; an interactive shell succeeding does not
prove a scheduled shell will.

For API-backed runs, usage and cost are provider/account dependent. Inspect
actual output metadata or the provider dashboard rather than estimating a fixed
per-run amount.

Source: [Run Claude Code programmatically](https://code.claude.com/docs/en/headless).
