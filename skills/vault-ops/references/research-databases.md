# Research Databases with Obsidian Bases

<!-- Source: kepano/obsidian-skills/skills/obsidian-bases @ a1dc48e68138490d522c04cbf5822214c6eb1202 (reviewed 2026-07-10) -->
<!-- Includes recursive-filter correction @ 9b736ba8da230341054cc668bedc0bcb041baa98 -->
<!-- Curated for Carrel research context; next review: 2026-10-10 -->

Obsidian Bases (`.base` files) create live database views over note frontmatter and file metadata without duplicating vault content.

## When to Suggest

- A researcher has 10+ papers and is losing track of reading status.
- A qualitative project needs interview, coding, or follow-up tracking.
- A writing project needs section, deadline, or blocker views.
- The researcher asks to sort, filter, group, or summarize vault files.

## Current File Shape

`.base` files are valid YAML. Use plural `filters`; mapping-valued `formulas`, `properties`, and custom `summaries`; and one or more named `views`.

```yaml
filters:
  and:
    - 'file.inFolder("papers")'

formulas:
  days_in_vault: '(now() - file.ctime).days'

properties:
  title:
    displayName: "Title"
  formula.days_in_vault:
    displayName: "Days in vault"

summaries:
  Count: 'values.length'

views:
  - type: table
    name: "Needs Notes"
    filters:
      or:
        - 'status == "unread"'
        - 'status == "reading"'
    order:
      - file.name
      - title
      - status
      - formula.days_in_vault
    sort:
      - property: file.ctime
        direction: ASC
    groupBy:
      property: status
      direction: ASC
    summaries:
      title: Count
      formula.days_in_vault: Average
```

Do not use the superseded top-level `filter`/`sort`, list-valued property or formula declarations, view `filter`, or view `group` shapes.

## Filters

A filter is a string expression or a recursive object containing one of `and`, `or`, or `not`.

```yaml
filters:
  and:
    - 'file.inFolder("papers")'
    - not:
        - 'status == "cited"'
```

View-specific filters use exactly the same shape. Useful operations include `==`, `!=`, comparisons, `&&`, `||`, `!`, `file.inFolder()`, and `file.hasTag()`.

## Properties and Formulas

- Note properties come from frontmatter: `status`, `note.status`, or `note["status"]`.
- Use bracket access for names containing hyphens: `note["due-date"]`, never subtraction-like `due-date` in an expression.
- File properties include `file.name`, `file.folder`, `file.ctime`, `file.mtime`, `file.size`, and `file.tags`.
- Formula properties are referenced as `formula.formula_name`.
- Guard optional values before date arithmetic: `'if(note["due-date"], (date(note["due-date"]) - today()).days, "")'`.

The `transcribed` field created by Carrel is an ISO date, not a checkbox. Treat it as a truthy/date value and label it “Transcribed on.”

## Views and Summaries

Each view needs `type`, `name`, and an `order` list. It may also use `filters`, `sort`, `groupBy`, and property-to-summary mappings. Sort and group directions are `ASC` or `DESC`.

Built-in summaries include `Average`, `Min`, `Max`, `Sum`, `Median`, `Checked`, `Unchecked`, `Empty`, `Filled`, and `Unique`. Define a custom row count once with `Count: 'values.length'` when needed.

## Embedding

Embed the default or a named view from a Markdown note:

```markdown
![[paper-tracker.base]]
![[paper-tracker.base#Needs Notes]]
```

## Carrel Templates

| Template | Created when | Source folder |
|----------|--------------|---------------|
| `reading-progress.base` | Always | `papers/` |
| `paper-tracker.base` | Many papers or literature review | `papers/` |
| `interview-tracker.base` | Qualitative or interview work | `transcripts/` |
| `writing-tracker.base` | Writing, thesis, or dissertation work | `drafts/` |

Carrel-shipped templates carry a `carrel-template:` marker. Never add that marker to a custom vault-local Base.

## Validation Checklist

- Parse the file as YAML.
- Require mapping-valued `properties`, `formulas`, and `summaries`.
- Require plural `filters` and view `order`; reject legacy `filter` and `group` keys.
- Confirm every `formula.X` reference has a matching formula.
- Confirm every folder, frontmatter property, and group/sort property exists.
- Use bracket access for hyphenated property names in expressions.
- Open the Base in Obsidian and check every named view after a schema change.

Source contract: [Obsidian Bases syntax](https://help.obsidian.md/bases/syntax).
