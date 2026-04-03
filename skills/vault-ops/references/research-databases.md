# Research Databases with Obsidian Bases

<!-- Source: kepano/obsidian-skills/skills/obsidian-bases @ v1.0.1 (2026-04-02) -->
<!-- Curated for Carrel research context -->
<!-- Review cadence: quarterly (next: 2026-07-01) -->

Obsidian Bases (`.base` files) create live, filterable, sortable database views over vault notes. Think Notion databases but local. They query note frontmatter and file metadata — no data duplication.

## When to Suggest

- Researcher has 10+ papers and asks "what have I read?" or "I'm losing track"
- Qualitative researcher managing interviews, coding progress, participants
- Researcher tracking writing progress across draft sections
- Any "show me everything that matches X" request

## File Format

`.base` files are YAML. Save to vault root or relevant folder.

```yaml
# paper-tracker.base
properties:
  - name: title
    type: text
  - name: status
    type: text
  - name: year
    type: number

filter: "file.folder = \"papers\""

sort:
  - property: year
    direction: desc
```

## Core Structure

```yaml
# Required
properties:          # Columns to display (from note frontmatter or file metadata)

# Optional
filter: "..."        # Which notes to include
sort:                # Default ordering
  - property: name
    direction: asc | desc
formulas:            # Computed columns
views:               # Named view configurations
summaries:           # Aggregations (sum, count, average)
```

## Properties (Columns)

Map to YAML frontmatter fields in your notes, or use built-in file properties.

```yaml
properties:
  - name: title          # From note frontmatter
    type: text
  - name: year
    type: number
  - name: status
    type: text
  - name: tags
    type: tags
  - name: coded          # Boolean checkbox
    type: checkbox
  - name: date
    type: date
```

**Built-in file properties** (no frontmatter needed):

| Property | Description |
|----------|-------------|
| `file.name` | Filename without extension |
| `file.folder` | Parent folder path |
| `file.ctime` | Creation date |
| `file.mtime` | Last modified date |
| `file.size` | File size in bytes |
| `file.tags` | All tags in the file |

## Filters

Control which notes appear. Use frontmatter values and file metadata.

```yaml
# Single condition
filter: "status == \"reading\""

# Multiple conditions
filter: "file.folder = \"papers\" && year >= 2020"

# Tags
filter: "tags includes \"qualitative\""

# Negation
filter: "!(status == \"cited\")"
```

**Operators:**

| Operator | Meaning |
|----------|---------|
| `=` | Path/folder matching (use for `file.folder`) |
| `==`, `!=` | Value equality (use for frontmatter properties) |
| `>`, `<`, `>=`, `<=` | Comparisons (numbers, dates) |
| `&&`, `\|\|` | AND, OR |
| `!` | NOT |
| `includes` | Tag/list contains value |
| `= ""`, `!= ""` | Empty, not empty |

**Common compound filter** (most-requested research query):
```yaml
filter: "file.folder = \"papers\" && tags includes \"identity\""
```

## Formulas (Computed Columns)

Add calculated fields that update automatically.

```yaml
formulas:
  - name: days-since-added
    formula: "(now() - file.ctime).days"
  - name: is-stale
    formula: "if((now() - file.mtime).days > 30, \"stale\", \"active\")"
  - name: reading-time
    formula: "round(file.size / 1500)"
```

**Useful functions for research:**

| Function | Example | Use |
|----------|---------|-----|
| `now()` | `(now() - file.ctime).days` | Days since added |
| `if(cond, then, else)` | `if(coded, "done", "pending")` | Status logic |
| `round(n)` | `round(file.size / 1500)` | Estimated reading time |
| `length(list)` | `length(tags)` | Count tags |
| `contains(str, sub)` | `contains(title, "identity")` | Text search |

## Views

Named configurations for different perspectives on the same data.

```yaml
views:
  - type: table
    name: "All Papers"
    sort:
      - property: year
        direction: desc

  - type: table
    name: "Needs Notes"
    filter: "status == \"reading\" || status == \"unread\""
    sort:
      - property: file.ctime
        direction: asc

  - type: list
    name: "By Theme"
    group: tags
```

## Summaries (Aggregations)

Show totals at the bottom of table columns.

```yaml
summaries:
  - property: title
    function: Count
  - property: days-since-added
    function: Average
```

**Available functions:** Count, Sum, Average, Min, Max, Median, Earliest, Latest

## Research Templates

Carrel includes 4 research-specific .base templates in `templates/`. These are created during vault scaffolding based on the setup interview:

| Template | Created when | Queries |
|----------|-------------|---------|
| `paper-tracker.base` | Researcher works with papers | `papers/` folder |
| `interview-tracker.base` | Qualitative researcher with interviews | `transcripts/` folder |
| `reading-progress.base` | Always (default) | `papers/` folder (aggregation view) |
| `writing-tracker.base` | Researcher actively writing | `drafts/` folder |

## Validation Checklist

Before saving a .base file:
- [ ] All referenced properties exist in note frontmatter (or are built-in `file.*` properties)
- [ ] String values in filters are escaped: `"status == \"reading\""`
- [ ] Filter paths match actual vault folders: `file.folder = "papers"` not `file.folder = "papers/"`
- [ ] Formula parentheses are balanced
- [ ] Property types match actual data (don't use `number` for text fields)
