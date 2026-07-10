# Maintenance

Use the agent for synthesis and the runtime for deterministic persistence.

## Reflection

```bash
printf '%s\n' "<reflection body>" | python3 scripts/carrel.py reflection append --vault <vault>
```

## Mirror

```bash
printf '%s\n' "<mirror synthesis>" | python3 scripts/carrel.py mirror write --vault <vault>
```

## Feedback Digest

```bash
python3 scripts/carrel.py feedback export --vault <vault> --redact-list <path>
```

## Collaborator Handbook

```bash
python3 scripts/carrel.py share generate --vault <vault> --for "Name" --sensitivity medium
```

## Automation Preferences

```bash
python3 scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative --schedule daily --review-cadence quarterly
```

This persists the profile only. Generate the prompt separately after review:

```bash
python3 scripts/carrel.py vault automation-prompt --vault <vault>
```
