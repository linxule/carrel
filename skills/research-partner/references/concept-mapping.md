# Concept Mapping with Obsidian Canvas

<!-- Source: kepano/obsidian-skills/skills/json-canvas @ a1dc48e68138490d522c04cbf5822214c6eb1202 (reviewed 2026-07-10) -->
<!-- Curated for Carrel research context; next review: 2026-10-10 -->

Create `.canvas` files to visualize connections between papers, constructs, sources, and open questions. Canvas files use the [JSON Canvas 1.0 specification](https://jsoncanvas.org/spec/1.0/).

## When to Offer

- A researcher is exploring connections between papers or ideas.
- A theoretical framework or literature landscape needs a spatial view.
- The researcher says they need to “see the big picture.”

## Complete Example

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4e5f60718",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 300,
      "height": 150,
      "text": "# Identity Construction\nHow people build a sense of self during change"
    },
    {
      "id": "b2c3d4e5f6071829",
      "type": "file",
      "x": 400,
      "y": 0,
      "width": 300,
      "height": 150,
      "file": "papers/corley-gioia-2004/paper.md"
    },
    {
      "id": "c3d4e5f60718293a",
      "type": "link",
      "x": 800,
      "y": 0,
      "width": 300,
      "height": 150,
      "url": "https://doi.org/10.2307/20159058"
    }
  ],
  "edges": [
    {
      "id": "d4e5f60718293a4b",
      "fromNode": "a1b2c3d4e5f60718",
      "toNode": "b2c3d4e5f6071829",
      "fromSide": "right",
      "toSide": "left",
      "label": "developed in"
    },
    {
      "id": "e5f60718293a4b5c",
      "fromNode": "b2c3d4e5f6071829",
      "toNode": "c3d4e5f60718293a",
      "fromSide": "right",
      "toSide": "left",
      "label": "published as"
    }
  ]
}
```

## Node Types

| Type | Use for | Type-specific requirement |
|------|---------|---------------------------|
| `text` | Concepts, themes, questions | `text` Markdown string |
| `file` | Vault note or attachment | vault-relative `file`; optional `subpath` beginning `#` |
| `link` | External source | absolute `url` |
| `group` | Visual cluster | optional `label`, `background`, and `backgroundStyle` |

Every node also requires a unique string `id`, integer `x`/`y`, integer `width`/`height`, and a valid `type`. Carrel examples use 16-character lowercase hexadecimal IDs for consistency, but the JSON Canvas specification requires uniqueness rather than a particular length or alphabet.

Groups contain nodes spatially; there is no membership field. A group label is optional. Position child nodes inside the group's bounds.

```json
{
  "id": "f60718293a4b5c6d",
  "type": "group",
  "x": -50,
  "y": -50,
  "width": 800,
  "height": 300,
  "color": "6"
}
```

## Edges

Edges require unique string `id`, `fromNode`, and `toNode`. Optional sides are `top`, `right`, `bottom`, or `left`; optional endpoint shapes are `none` or `arrow`. Every endpoint must name an existing node.

## Colors and Layout

- Colors are presets `"1"` through `"6"` or a hex string such as `"#FF0000"`.
- Use red for tensions, orange for gaps, green for established findings, cyan for methods, and purple for theoretical framing.
- Leave 50–100px between nodes and 20–50px padding inside groups.
- Use left-to-right layouts for causal or temporal flows and center-out layouts for construct maps.

## Validation Checklist

- Parse the file as JSON.
- Require unique IDs across nodes and edges.
- Require `text`, `file`, or `url` for the corresponding node types.
- Accept group nodes without labels.
- Confirm every edge endpoint resolves to a node ID.
- Confirm side, endpoint, type, and color values come from the specification.
- Use actual newline escapes (`\n`) inside JSON text strings.
