# AI / LLM Document Generation Guide

## 1. Purpose

This guide provides system instructions, schemas, and prompting patterns for Large Language Models (LLMs) and Autonomous AI Agents generating or parsing `docx-bridge` JSON documents.

Adhering to this specification ensures **100% syntactically valid DOCX packages** with zero Word repair prompts.

---

## 2. LLM System Prompt Template

When instructing an AI to generate documents for `docx-bridge`, provide the following system instruction block:

```markdown
You are an expert Document Architect. Your task is to output clean, valid JSON adhering to the `docx-bridge` AST format.

Rules for Document Generation:
1. Wrap all content inside a `sections` array with page geometry and a `content` array.
2. Font sizes are measured in HALF-POINTS:
   - 10pt = 20
   - 11pt = 22 (Default body)
   - 14pt = 28 (Heading 3)
   - 18pt = 36 (Heading 2)
   - 24pt = 48 (Heading 1)
3. Measurements (margins, indents, spacing, table widths) are in DXA (1/20th of a point):
   - 1 inch = 1440 dxa
   - 0.5 inch = 720 dxa
   - 0.25 inch = 360 dxa
4. Colors MUST be 6-character hex strings WITHOUT the leading '#' (e.g. "1E3A8A", NOT "#1E3A8A").
5. Alignments: Use "left", "center", "right", or "both" (for justified).
6. Headings: Use standard style keys: "Heading1", "Heading2", "Heading3", "Normal", "Title".
7. For tables: Explicitly specify cell widths in dxa. Ensure row cells have a `content` array containing paragraphs.
8. Output ONLY the raw JSON object. Do not wrap in conversational chatter.
```

---

## 3. Common AI Hallucinations & Mitigation Matrix

| Hallucination / Mistake | Broken Value | Correct `docx-bridge` Value | Reason |
| :--- | :--- | :--- | :--- |
| **Hex color with `#`** | `"color": "#FF0000"` | `"color": "FF0000"` | OpenXML `w:color` expects raw hex values without `#` |
| **Font size in whole points** | `"size": 12` | `"size": 24` | Word sizes use half-points ($12\text{ pt} = 24\text{ half-pts}$) |
| **Margin in inches or pixels**| `"top": "1in"` | `"top": 1440` | All coordinate engines require integers in dxa |
| **Direct strings in cell** | `{"cells": ["Text"]}` | `{"cells": [{"content": [{"text": "Text"}]}]}` | Cell content must be block-level paragraphs |
| **CSS text alignment** | `"align": "justify"` | `"align": "both"` | OpenXML justification value is `"both"` |

---

## 4. Golden Example: Professional Business Report

Here is a reference JSON payload for AI models to follow:

```json
{
  "sections": [
    {
      "page": {
        "size": "a4",
        "orientation": "portrait",
        "margins": {
          "top": 1440,
          "bottom": 1440,
          "left": 1440,
          "right": 1440
        }
      },
      "content": [
        {
          "style": "Heading1",
          "text": "Quarterly Performance Briefing",
          "spacing": { "before": 0, "after": 240 }
        },
        {
          "align": "both",
          "runs": [
            {
              "text": "This document highlights key strategic initiatives completed during ",
              "font": "Calibri",
              "size": 22
            },
            {
              "text": "Q3 2026",
              "bold": true,
              "color": "1E40AF",
              "font": "Calibri",
              "size": 22
            },
            {
              "text": ". All milestones were delivered ahead of schedule.",
              "font": "Calibri",
              "size": 22
            }
          ]
        },
        {
          "style": "Heading2",
          "text": "Key Highlights",
          "spacing": { "before": 360, "after": 120 }
        },
        {
          "text": "Engine modularization completed across all pipelines",
          "level": 0,
          "indent": { "left": 720, "hanging": 360 },
          "numbering": { "id": 1, "level": 0, "type": "bullet" }
        },
        {
          "text": "Strict OpenXML schema validation achieved with zero repair prompts",
          "level": 0,
          "indent": { "left": 720, "hanging": 360 },
          "numbering": { "id": 1, "level": 0, "type": "bullet" }
        },
        {
          "style": "Heading2",
          "text": "Financial Summary",
          "spacing": { "before": 360, "after": 180 }
        },
        {
          "table": {
            "properties": {
              "alignment": "center",
              "width": { "value": 9000, "type": "dxa" },
              "borders": {
                "top": { "val": "single", "sz": 4, "color": "9CA3AF" },
                "bottom": { "val": "single", "sz": 4, "color": "9CA3AF" },
                "insideH": { "val": "single", "sz": 4, "color": "E5E7EB" },
                "left": { "val": "none" },
                "right": { "val": "none" }
              }
            },
            "rows": [
              {
                "properties": { "isHeader": true },
                "cells": [
                  {
                    "properties": {
                      "width": { "value": 4500, "type": "dxa" },
                      "shading": { "fill": "F3F4F6" }
                    },
                    "content": [{ "text": "Category", "bold": true, "color": "111827" }]
                  },
                  {
                    "properties": {
                      "width": { "value": 4500, "type": "dxa" },
                      "shading": { "fill": "F3F4F6" }
                    },
                    "content": [{ "text": "Amount (USD)", "bold": true, "align": "right", "color": "111827" }]
                  }
                ]
              },
              {
                "cells": [
                  {
                    "content": [{ "text": "Infrastructure & Cloud" }]
                  },
                  {
                    "content": [{ "text": "$42,500", "align": "right" }]
                  }
                ]
              },
              {
                "cells": [
                  {
                    "content": [{ "text": "Engineering & Tooling" }]
                  },
                  {
                    "content": [{ "text": "$88,200", "align": "right" }]
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 5. Python Verification Script

To validate an AI-generated JSON file before producing the `.docx`:

```python
from converter.docx.json_to_docx import json_to_docx

try:
    json_to_docx("generated_output.json", "output.docx")
    print("Document successfully compiled to DOCX without errors.")
except Exception as e:
    print(f"Validation failed: {e}")
```
