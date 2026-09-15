# DOCX Unified JSON AST Specification

## 1. Overview & Schema Architecture

The `docx-bridge` JSON format represents a Word document as an Abstract Syntax Tree (AST). It provides two representation tiers:
1. **Simple Mode (`--simple`, Default)**: A clean, human-readable, and AI-optimized format focusing on semantic structure, styling, tables, and lists.
2. **Raw Mode (`--raw`)**: Complete 1:1 mapping of OpenXML nodes and namespaces, preserving all low-level XML attributes.

---

## 2. Root Document Schema (Simple Mode)

```json
{
  "sections": [
    {
      "page": {
        "size": "a4",
        "orientation": "portrait",
        "width": 11906,
        "height": 16838,
        "margins": {
          "top": 1440,
          "bottom": 1440,
          "left": 1440,
          "right": 1440,
          "header": 720,
          "footer": 720
        }
      },
      "content": [
        /* Block-level elements: Paragraphs, Tables */
      ]
    }
  ]
}
```

### 2.1 Section Geometry Properties

| Field | Type | Description | Default | Valid Values |
| :--- | :--- | :--- | :--- | :--- |
| `size` | `string` | Standard paper size key | `"a4"` | `"a4"`, `"letter"`, `"legal"`, `"a3"`, `"a5"` |
| `orientation` | `string` | Page orientation | `"portrait"` | `"portrait"`, `"landscape"` |
| `width` | `integer` | Width in dxa (twips) | `11906` | Positive integer |
| `height` | `integer` | Height in dxa (twips) | `16838` | Positive integer |
| `margins.top` | `integer` | Top margin in dxa | `1440` ($1\text{ in}$) | $\ge 0$ |
| `margins.bottom`| `integer` | Bottom margin in dxa | `1440` ($1\text{ in}$) | $\ge 0$ |
| `margins.left` | `integer` | Left margin in dxa | `1440` ($1\text{ in}$) | $\ge 0$ |
| `margins.right` | `integer` | Right margin in dxa | `1440` ($1\text{ in}$) | $\ge 0$ |

---

## 3. Paragraph Schema (`content[]`)

A paragraph can be expressed in two ways:
- **Concise Form**: For homogeneous text styling.
- **Run-Based Form**: For inline styled fragments (e.g. bolding specific words).

### 3.1 Concise Paragraph Example
```json
{
  "style": "Heading1",
  "text": "Executive Summary",
  "align": "left",
  "spacing": {
    "before": 240,
    "after": 120,
    "line": 276
  }
}
```

### 3.2 Complex Run-Based Paragraph Example
```json
{
  "align": "center",
  "runs": [
    {
      "text": "Antigravity ",
      "bold": true,
      "size": 28,
      "font": "Calibri",
      "color": "1E40AF"
    },
    {
      "text": "Engine Documentation",
      "italic": true,
      "size": 24,
      "color": "374151"
    }
  ]
}
```

### 3.3 Paragraph Level Attributes

| Property | Type | Description | Example / Range |
| :--- | :--- | :--- | :--- |
| `style` | `string` | Style ID | `"Heading1"`, `"Heading2"`, `"Normal"`, `"Title"` |
| `align` | `string` | Text alignment | `"left"`, `"center"`, `"right"`, `"both"` (justify) |
| `spacing.before` | `integer` | Space before paragraph (dxa) | `240` ($12\text{ pt}$) |
| `spacing.after` | `integer` | Space after paragraph (dxa) | `120` ($6\text{ pt}$) |
| `spacing.line` | `integer` | Line spacing in 240ths of a line | `240` ($1.0$), `288` ($1.2$), `360` ($1.5$), `480` ($2.0$) |
| `indent.left` | `integer` | Left indentation in dxa | `720` ($0.5\text{ in}$) |
| `indent.right` | `integer` | Right indentation in dxa | `720` |
| `indent.firstLine`| `integer` | First-line indent (dxa) | `360` |
| `indent.hanging` | `integer` | Hanging indent (dxa) | `360` |

---

## 4. Run-Level Schema (`runs[]`)

Inline text elements support rich typographic styling:

```json
{
  "text": "Critical Alert",
  "bold": true,
  "italic": false,
  "underline": "single",
  "strike": false,
  "size": 22,
  "font": "Arial",
  "color": "DC2626",
  "highlight": "yellow",
  "verticalAlign": "superscript"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `text` | `string` | The text content (entities automatically escaped in XML) |
| `bold` | `boolean` | Bold toggle |
| `italic` | `boolean` | Italic toggle |
| `underline` | `string` or `boolean` | `"single"`, `"double"`, `"dotted"`, `"wave"`, `true` |
| `strike` | `boolean` | Strikethrough |
| `size` | `integer` | Font size in **half-points** (`22` = $11\text{ pt}$, `24` = $12\text{ pt}$) |
| `font` | `string` | Font family name (e.g. `"Calibri"`, `"Times New Roman"`, `"Arial"`) |
| `color` | `string` | Hex RGB color code without `#` (e.g. `"FF0000"`, `"1E40AF"`) |
| `highlight` | `string` | Highlight color (`"yellow"`, `"green"`, `"cyan"`, `"magenta"`, etc.) |
| `verticalAlign` | `string` | `"baseline"`, `"superscript"`, `"subscript"` |

---

## 5. Bullet & Numbered Lists Schema

`docx-bridge` features bullet and numbered list normalization:

### 5.1 Bullet Item
```json
{
  "text": "First bullet item",
  "level": 0,
  "indent": {
    "left": 720,
    "hanging": 360
  },
  "numbering": {
    "id": 1,
    "level": 0,
    "type": "bullet"
  }
}
```

### 5.2 Nested Numbered Item
```json
{
  "text": "Sub-point 1.A",
  "level": 1,
  "indent": {
    "left": 1440,
    "hanging": 360
  },
  "numbering": {
    "id": 2,
    "level": 1,
    "type": "decimal"
  }
}
```

---

## 6. Table Schema (`table`)

Tables are first-class block elements containing rows and cells:

```json
{
  "table": {
    "properties": {
      "alignment": "center",
      "width": { "value": 9000, "type": "dxa" },
      "borders": {
        "top": { "val": "single", "sz": 4, "space": 0, "color": "D1D5DB" },
        "bottom": { "val": "single", "sz": 4, "space": 0, "color": "D1D5DB" },
        "left": { "val": "none" },
        "right": { "val": "none" }
      }
    },
    "rows": [
      {
        "properties": { "isHeader": true, "cantSplit": true },
        "cells": [
          {
            "properties": {
              "width": { "value": 3000, "type": "dxa" },
              "shading": { "fill": "F3F4F6" }
            },
            "content": [
              { "text": "Feature", "bold": true }
            ]
          },
          {
            "properties": {
              "width": { "value": 6000, "type": "dxa" },
              "shading": { "fill": "F3F4F6" }
            },
            "content": [
              { "text": "Description", "bold": true }
            ]
          }
        ]
      },
      {
        "cells": [
          {
            "content": [{ "text": "Roundtrip" }]
          },
          {
            "content": [{ "text": "Zero-loss DOCX <-> JSON conversion" }]
          }
        ]
      }
    ]
  }
}
```

### 6.1 Cell Properties (`properties`)

| Property | Type | Description |
| :--- | :--- | :--- |
| `width` | `object` | `{ "value": integer, "type": "dxa" \| "pct" }` |
| `colSpan` | `integer` | Horizontal column merge span (`w:gridSpan`) |
| `rowSpan` | `integer` | Vertical row merge span (`w:vMerge`) |
| `shading.fill` | `string` | Cell background hex RGB (`"FFFFFF"`, `"E5E7EB"`) |
| `verticalAlign` | `string` | `"top"`, `"center"`, `"bottom"` |

---

## 7. Media & Images Schema

Images are represented as block or inline elements:

```json
{
  "image": {
    "data": "data:image/png;base64,iVBORw0KGgo...",
    "width": 3810000,
    "height": 2857500,
    "align": "center",
    "altText": "Architecture Diagram"
  }
}
```
- `width` and `height` are measured in **EMUs** ($1\text{ in} = 914,400\text{ EMUs}$).
- `data` can be a base64 Data URL or relative image file path.
