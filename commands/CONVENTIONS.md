# Command File Conventions

## `${ARGS}` vs `$ARGUMENTS`

**`${ARGS}` (skill-constructed)** is used by *thin wrappers* whose calling skill assembles a typed-flag argument list. The skill conducts the interview, resolves defaults, applies vault context, and then invokes the slash command with a fully-formed flag set. Because the wrapper body cannot contain conditionals, all orchestration lives in the skill — the wrapper just shells out.

**`$ARGUMENTS` (raw user input)** is reserved for commands whose contract IS the direct user input — e.g., a single positional argument like a URL or file path passed straight through to the CLI. No skill mediation, no flag construction. Use only when the user types the exact CLI argument string.

## Wrapper Template

Thin wrappers must match this shape exactly:

```markdown
---
description: <one-line description>
argument-hint: <usage hint for completion>
---
!carrel <subcmd> ${ARGS}
```

No prose body, no conditionals (`if`, `case`), no embedded markdown headers, no additional frontmatter keys beyond `description` and `argument-hint`. The body is a single non-empty line beginning with `!carrel `.

## File Inventory

**Thin wrappers (7)** — validated by `tests/test_command_wrappers.py`:

- `carrel-automate.md` → `carrel automate`
- `carrel-batch.md` → `carrel batch`
- `carrel-feedback.md` → `carrel vault feedback`
- `carrel-migrate.md` → `carrel migrate`
- `carrel-mirror.md` → `carrel vault mirror`
- `carrel-reflect.md` → `carrel vault reflect-log`
- `carrel-share.md` → `carrel vault share`

**Full skill-prompts (8)** — current shape preserved, exempt from template:

- `carrel-capture.md`, `carrel-cheatsheet.md`, `carrel-convert.md`, `carrel-fix.md`, `carrel-setup.md`, `carrel-status.md`, `carrel-teammates.md`, `carrel-transcribe.md`

These either wrap an existing CLI cleanly or are pure skill prompts. They get the wrapper treatment in a future pass only if they accumulate orchestration prose.

## Reference

See `planning/specs/014-cc-plugin-v090.md` (Section A.3 and the Locked Decision row for the `${ARGS}` vs `$ARGUMENTS` convention) for full design rationale.
