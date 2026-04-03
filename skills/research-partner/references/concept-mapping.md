# Concept Mapping with Obsidian Canvas

<!-- Source: kepano/obsidian-skills/skills/json-canvas @ v1.0.1 (2026-04-02) -->
<!-- Curated for Carrel research context -->
<!-- Review cadence: quarterly (next: 2026-07-01) -->

Create `.canvas` files to help researchers visualize connections between papers, constructs, and ideas. Canvas files open as interactive visual boards in Obsidian.

## When to Offer

- Researcher is exploring connections between papers or ideas
- Researcher says "I'm stuck" or "I can't see the big picture"
- Building or revising a theoretical framework
- Mapping a literature review landscape
- Researcher shows visual thinking in conversation (draws connections, says "I need to see this", asks for a map or diagram)

## File Format

Canvas files are JSON with `.canvas` extension. Save to `notes/` or vault root.

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "type": "text",
      "x": 0, "y": 0,
      "width": 300, "height": 150,
      "text": "# Identity Construction\nHow individuals build sense of self\nduring organizational change"
    },
    {
      "id": "b2c3d4e5f6g7h8i9",
      "type": "file",
      "file": "papers/corley-gioia-2004/paper.md",
      "x": 400, "y": 0,
      "width": 300, "height": 150
    }
  ],
  "edges": [
    {
      "id": "e1f2g3h4i5j6k7l8",
      "fromNode": "a1b2c3d4e5f6g7h8",
      "toNode": "b2c3d4e5f6g7h8i9",
      "fromSide": "right",
      "toSide": "left",
      "label": "foundational"
    }
  ]
}
```

## Node Types

| Type | Use for | Required fields |
|------|---------|----------------|
| `text` | Concepts, themes, questions | `text` (markdown content) |
| `file` | Link to vault note or paper | `file` (vault-relative path) |
| `group` | Thematic cluster container | `label` (not `text`) |

All nodes need: `id` (16-char hex), `type`, `x`, `y`, `width`, `height`. Nodes and groups also accept `color` (`"1"`-`"6"` presets or hex) for thematic coding.

Generate IDs with random hex: `Math.random().toString(16).slice(2, 18)`.

**Group containment**: Groups have no explicit membership property. Nodes become part of a group by having their `x`/`y` coordinates inside the group's bounding box. Position member nodes within the group's `x`, `y`, `width`, `height` bounds.

```json
{
  "id": "g1a2b3c4d5e6f7g8", "type": "group",
  "x": -50, "y": -50, "width": 700, "height": 250,
  "label": "Identity Literature"
},
{
  "id": "a1b2c3d4e5f6g7h8", "type": "text",
  "x": 0, "y": 0, "width": 300, "height": 150,
  "text": "# Identity Construction", "color": "6"
},
{
  "id": "b2c3d4e5f6g7h8i9", "type": "file",
  "file": "papers/corley-gioia-2004/paper.md",
  "x": 400, "y": 0, "width": 300, "height": 150, "color": "4"
}
```

## Edges

Connect nodes directionally. Properties:

| Field | Required | Values |
|-------|----------|--------|
| `id` | Yes | 16-char hex |
| `fromNode` | Yes | Source node ID |
| `toNode` | Yes | Target node ID |
| `fromSide` | No | `top`, `right`, `bottom`, `left` |
| `toSide` | No | `top`, `right`, `bottom`, `left` |
| `label` | No | Relationship description |
| `color` | No | `"1"`-`"6"` (presets) or hex |

## Color Presets for Thematic Coding

Apply colors to both **nodes** (more visually useful — larger surface area) and **edges**. Same presets work for both:

| Color | Suggested use |
|-------|--------------|
| `"1"` (red) | Tensions, contradictions |
| `"2"` (orange) | Questions, gaps |
| `"3"` (yellow) | Key constructs (note: low contrast in light themes) |
| `"4"` (green) | Established findings |
| `"5"` (cyan) | Methodological notes |
| `"6"` (purple) | Theoretical framing |

Node coloring is typically more useful than edge coloring for research concept maps — a green paper node (established finding) is more visually informative than a green arrow.

## Layout Guidelines

- Place related nodes near each other (50-100px gaps)
- Use groups to cluster papers by theme: `"type": "group", "label": "Identity Literature"`
- Left-to-right for temporal/causal flows
- Center-out for construct maps
- Width 250-400, height 100-200 for readable nodes

## Example: Literature Concept Map

A researcher studying identity construction maps 4 papers and their conceptual relationships. The canvas shows construct clusters (identity, sensemaking, organizational change) with paper nodes linked to the constructs they address. Edges labeled with the relationship type (challenges, extends, applies).

Create canvas files proactively when the researcher is in "exploration mode." Say: "I mapped the connections between your papers — open `notes/literature-map.canvas` in Obsidian to see it visually. You can drag things around."
