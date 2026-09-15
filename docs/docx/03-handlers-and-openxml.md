# OpenXML Handlers & Tag Mappings

## 1. Handler Architecture

The conversion between OpenXML elements and the JSON AST is decoupled across modular handlers in the [`handlers/`](file:///home/omkar/Documents/docx-bridge/handlers/) package.

```
handlers/
├── common/              # Shared base abstractions, unit conversions, and color helpers
│   ├── base.py          # CommonBaseHandler(ABC)
│   ├── units.py         # twip/dxa, pt, half-points, emu, inch, cm conversions
│   ├── color.py         # BGR <-> Hex RGB color conversions
│   ├── helpers.py       # Data coercion and normalization helpers
│   └── registry.py      # BaseHandlerRegistry abstract class
├── docx/                # OpenXML (.docx) handlers
│   ├── base.py          # DocxBaseHandler, XML namespaces, qn, de_qn, schema sorting
│   ├── document.py      # Root document structure (<w:document>, <w:body>)
│   ├── paragraph.py     # Paragraph properties (<w:p>, <w:pPr>, spacing, alignment)
│   ├── run.py           # Text runs (<w:r>, <w:rPr>, bold, font, size, color)
│   ├── table.py         # Tables (<w:tbl>, <w:tr>, <w:tc>, cell formatting, borders)
│   ├── numbering.py     # Abstract/concrete lists (<w:numbering>, <w:num>, <w:lvl>)
│   ├── styles.py        # Style sheet definitions (<w:styles>, <w:style>)
│   ├── sections.py      # Section geometries & headers/footers (<w:sectPr>)
│   ├── media.py         # Drawings, blips & images (<w:drawing>, <a:blip>)
│   └── relationships.py # OPC relationship trees (.rels)
├── doc/                 # Legacy Binary (.doc) handlers
│   └── ...              # DocBaseHandler, DocParagraphHandler, DocRunHandler, etc.
└── [root shims]         # Backward compatibility forwarding to handlers/docx/
```

Each handler implements two symmetric methods:
1. `parse(element, context)`: OpenXML Element $\longrightarrow$ JSON AST dictionary.
2. `build(data, context)`: JSON AST dictionary $\longrightarrow$ OpenXML Element.

---

## 2. OpenXML Tag to JSON Property Matrix

### 2.1 Paragraph Properties (`<w:pPr>`)

| OpenXML Element | Child Tag / Attribute | JSON AST Path | Description / Conversion |
| :--- | :--- | :--- | :--- |
| `<w:pStyle>` | `@w:val` | `style` | Style identifier (e.g. `"Heading1"`) |
| `<w:jc>` | `@w:val` | `align` | `"left"`, `"center"`, `"right"`, `"both"` |
| `<w:spacing>` | `@w:before` | `spacing.before` | Pre-paragraph spacing in dxa |
| `<w:spacing>` | `@w:after` | `spacing.after` | Post-paragraph spacing in dxa |
| `<w:spacing>` | `@w:line` | `spacing.line` | Line height in 240ths of a line |
| `<w:ind>` | `@w:left` | `indent.left` | Left indentation in dxa |
| `<w:ind>` | `@w:right` | `indent.right` | Right indentation in dxa |
| `<w:ind>` | `@w:firstLine` | `indent.firstLine` | First-line indent in dxa |
| `<w:ind>` | `@w:hanging` | `indent.hanging` | Hanging indent in dxa |
| `<w:numPr>` | `<w:numId>`, `<w:ilvl>` | `numbering.id`, `numbering.level` | List association |
| `<w:pageBreakBefore>` | Presence | `pageBreakBefore` | Forces page break before paragraph |

### 2.2 Run Properties (`<w:rPr>`)

| OpenXML Element | Child Tag / Attribute | JSON AST Path | Description / Conversion |
| :--- | :--- | :--- | :--- |
| `<w:b>` | Presence or `@w:val="1"` | `bold` | Bold font weight |
| `<w:i>` | Presence or `@w:val="1"` | `italic` | Italic font style |
| `<w:u>` | `@w:val` | `underline` | Underline decoration style |
| `<w:strike>` | Presence | `strike` | Strikethrough |
| `<w:rFonts>` | `@w:ascii`, `@w:hAnsi` | `font` | Primary font family name |
| `<w:sz>` | `@w:val` | `size` | Font size in **half-points** ($24 = 12\text{ pt}$) |
| `<w:color>` | `@w:val` | `color` | 6-character Hex RGB code (without `#`) |
| `<w:highlight>`| `@w:val` | `highlight` | Named highlight color (`"yellow"`, `"green"`) |
| `<w:vertAlign>`| `@w:val` | `verticalAlign`| `"superscript"` or `"subscript"` |

### 2.3 Table & Cell Properties (`<w:tblPr>`, `<w:tcPr>`)

| OpenXML Element | Child Tag / Attribute | JSON AST Path | Description / Conversion |
| :--- | :--- | :--- | :--- |
| `<w:tblW>` | `@w:w`, `@w:type` | `table.properties.width` | Table width in dxa or percent |
| `<w:jc>` | `@w:val` | `table.properties.alignment` | Table layout alignment |
| `<w:tblBorders>`| Sub-elements | `table.properties.borders` | Table border definitions |
| `<w:tcW>` | `@w:w`, `@w:type` | `cell.properties.width` | Cell width |
| `<w:gridSpan>` | `@w:val` | `cell.properties.colSpan`| Horizontal column merge span |
| `<w:vMerge>` | `@w:val="restart"\|"continue"` | `cell.properties.rowSpan`| Vertical row merge status |
| `<w:shd>` | `@w:fill` | `cell.properties.shading.fill` | Cell background hex RGB |

---

## 3. OpenXML Schema Order Enforcement

ECMA-376 requires child elements inside property containers to appear in **strict deterministic sequence**. Violating this sequence causes Microsoft Word to display a *"Word found unreadable content"* prompt.

`docx-bridge` automatically sorts generated XML nodes according to [`config/docx.json`](file:///home/omkar/Documents/docx-bridge/config/docx.json)`["schema_orders"]`:

```python
# Order enforced inside <w:pPr>
PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
    "widowControl", "numPr", "pBdr", "shd", "tabs", "spacing",
    "ind", "jc", "textAlignment", "outlineLvl", "rPr", "sectPr"
]

# Order enforced inside <w:rPr>
RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps",
    "strike", "dstrike", "outline", "shadow", "emboss", "imprint",
    "vanish", "color", "spacing", "w", "kern", "position", "sz",
    "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
    "vertAlign", "rtl", "cs", "lang"
]
```

---

## 4. Numbering Resolution Engine (`converter/docx/numbering.py`)

When generating DOCX packages from JSON, the numbering engine automatically:
1. Gathers all paragraphs with `numbering` or `level` attributes.
2. Synthesizes an `<w:abstractNum>` template supporting 9 hierarchy levels.
3. Automatically sets list prefixes (e.g. `•`, `-`, `1.`, `a.`, `i.`).
4. Calculates correct hanging and left indents ($720\text{ dxa} \times \text{level}$).
5. Instantiates `<w:num>` entries linked to `document.xml`.
