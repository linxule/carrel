# Maintenance

Use the agent for synthesis and the runtime for deterministic persistence.

## Reflection

```bash
printf '%s\n' "<reflection body>" | python scripts/carrel.py reflection append --vault <vault>
```

## Mirror

```bash
printf '%s\n' "<mirror synthesis>" | python scripts/carrel.py mirror write --vault <vault>
```

## Feedback Digest

```bash
python scripts/carrel.py feedback export --vault <vault> --redact-list <path>
```

## Collaborator Handbook

```bash
python scripts/carrel.py share generate --vault <vault> --for "Name" --sensitivity medium
```

## Automation Preferences

```bash
python scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative
```
