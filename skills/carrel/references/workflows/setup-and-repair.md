# Setup And Repair

Use `vault init` to create a portable vault. The runtime creates the folder
layout, copies assets from `assets/templates/`, writes
`.carrel/environment.json`, and writes `.carrel/agent-context.md`.

After setup, run:

```bash
python3 scripts/carrel.py env doctor --project-path <vault> --format json
python3 scripts/carrel.py env validate --vault <vault> --format json
```

If validation reports missing fields or invalid JSON, use:

```bash
python3 scripts/carrel.py env fix --vault <vault> --dry-run --format json
python3 scripts/carrel.py env fix --vault <vault>
```

Agents should update both the structured profile and the neutral context file
when the researcher's preferences materially change.
