# Mermaid v11.x Syntax Reference — Common Errors and Fixes

## Table of Contents

1. [Diagram Type Declaration](#1-diagram-type-declaration)
2. [Flowchart Direction](#2-flowchart-direction)
3. [Special Characters in Labels](#3-special-characters-in-labels)
4. [Arrow Syntax by Diagram Type](#4-arrow-syntax-by-diagram-type)
5. [Subgraph and End Conflicts](#5-subgraph-and-end-conflicts)
6. [Sequence Diagram Rules](#6-sequence-diagram-rules)
7. [Class Diagram Rules](#7-class-diagram-rules)
8. [ER Diagram Rules](#8-er-diagram-rules)
9. [State Diagram Rules](#9-state-diagram-rules)
10. [Gantt Chart Rules](#10-gantt-chart-rules)
11. [Pie Chart Rules](#11-pie-chart-rules)
12. [Mindmap Rules](#12-mindmap-rules)
13. [Block Diagram Rules](#13-block-diagram-rules)
14. [Style and ClassDef](#14-style-and-classdef)
15. [Common Pitfalls](#15-common-pitfalls)
16. [Unicode and Langium Parser Issues](#16-unicode-and-langium-parser-issues)
17. [Sequence Diagram Message Escaping](#17-sequence-diagram-message-escaping)
18. [Sequence Diagram Reserved Words](#18-sequence-diagram-reserved-words)

---

## 1. Diagram Type Declaration

The first non-comment line must declare the diagram type.

```
%% WRONG — missing type
A --> B
B --> C

%% CORRECT
flowchart TD
    A --> B
    B --> C
```

Valid types: `flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`,
`erDiagram`, `gantt`, `pie`, `gitgraph`, `mindmap`, `timeline`,
`block-beta`, `journey`, `quadrantChart`, `xychart-beta`,
`requirementDiagram`, `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`,
`C4Deployment`, `sankey-beta`, `packet-beta`, `architecture-beta`, `kanban`.

Note: `stateDiagram` (without `-v2`) still works but v2 is recommended.

---

## 2. Flowchart Direction

`flowchart` and `graph` require a direction keyword.

| Keyword | Direction |
|---------|-----------|
| `TD` / `TB` | Top to Bottom |
| `BT` | Bottom to Top |
| `LR` | Left to Right |
| `RL` | Right to Left |

```
%% WRONG
flowchart
    A --> B

%% CORRECT
flowchart TD
    A --> B
```

---

## 3. Special Characters in Labels

Characters that break parsing must be inside double quotes.

### Problematic characters

`(`, `)`, `[`, `]`, `{`, `}`, `<`, `>`, `|`, `:`, `;`, `#`, `&`, `@`, `$`, `!`, `?`

### Fix: Wrap in double quotes

```
%% WRONG — parentheses break the node shape parser
A[입력(값)]
B[Check: OK]
C[Price $100]
D[Step #1]
E[A & B]

%% CORRECT
A["입력(값)"]
B["Check: OK"]
C["Price $100"]
D["Step #1"]
E["A & B"]
```

### Korean / Unicode labels

Always quote labels containing Korean, Japanese, Chinese, or other non-ASCII text
when they also contain special characters or are used in complex node shapes.

```
%% SAFE (simple label, no special chars)
A[데이터]

%% MUST QUOTE (special char inside Korean label)
B["데이터(원본)"]
C["처리: 완료"]
```

### Quotes inside labels

Use HTML entity `&quot;` or single quotes inside double-quoted labels.

```
D["He said 'hello'"]
E["Value is &quot;null&quot;"]
```

---

## 4. Arrow Syntax by Diagram Type

### Flowchart arrows

| Arrow | Meaning |
|-------|---------|
| `-->` | Solid line with arrow |
| `---` | Solid line without arrow |
| `-.->` | Dotted line with arrow |
| `-.-` | Dotted line without arrow |
| `==>` | Thick line with arrow |
| `===` | Thick line without arrow |
| `--text-->` | Solid with label |
| `-->|text|` | Solid with label (alt) |
| `-.text.->` | Dotted with label |
| `==text==>` | Thick with label |
| `--o` | Circle end |
| `--x` | Cross end |
| `<-->` | Bidirectional |

```
%% WRONG
A -> B
A - -> B
A -text-> B

%% CORRECT
A --> B
A -.-> B
A --text--> B
```

### Sequence diagram arrows

| Arrow | Meaning |
|-------|---------|
| `->` | Solid without arrowhead |
| `-->` | Dotted without arrowhead |
| `->>` | Solid with arrowhead |
| `-->>` | Dotted with arrowhead |
| `-x` | Solid with cross |
| `--x` | Dotted with cross |
| `-)` | Solid with open arrow (async) |
| `--)` | Dotted with open arrow (async) |

### Class diagram arrows

| Arrow | Meaning |
|-------|---------|
| `<\|--` | Inheritance |
| `*--` | Composition |
| `o--` | Aggregation |
| `-->` | Association |
| `..>` | Dependency |
| `..\|>` | Realization |
| `--` | Solid link |
| `..` | Dashed link |

### State diagram arrows

Only `-->` is valid for transitions.

```
%% WRONG
StateA -> StateB

%% CORRECT
StateA --> StateB
StateA --> StateB : event
```

---

## 5. Subgraph and End Conflicts

### Every subgraph needs `end`

```
%% WRONG — missing end
flowchart TD
    subgraph Group
        A --> B

%% CORRECT
flowchart TD
    subgraph Group
        A --> B
    end
```

### Node ID or label containing "end"

If any node ID starts with or equals `end`, Mermaid treats it as a subgraph closer.

```
%% WRONG — "end" is parsed as subgraph closer
flowchart TD
    subgraph Process
        start --> endpoint
        endpoint --> finish
    end

%% CORRECT — quote the label, rename the ID
flowchart TD
    subgraph Process
        start --> ep["endpoint"]
        ep --> finish
    end
```

Other reserved words to avoid as bare node IDs: `end`, `subgraph`, `click`, `style`,
`classDef`, `class`, `linkStyle`, `callback`.

---

## 6. Sequence Diagram Rules

### Participant declaration (optional but recommended)

```
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A ->> B: Hello
    B -->> A: Hi
```

### Activation

```
    A ->> +B: Request
    B -->> -A: Response
```

### Notes

```
    Note right of A: This is a note
    Note over A,B: Shared note
```

### Loops and alternatives

```
    loop Every minute
        A ->> B: Ping
    end

    alt Success
        B -->> A: OK
    else Failure
        B -->> A: Error
    end

    opt Optional
        A ->> B: Maybe
    end
```

### Common errors

```
%% WRONG — missing colon after arrow
A ->> B Hello

%% WRONG — space in participant name without alias
participant My Service

%% CORRECT
A ->> B: Hello
participant MS as My Service
```

---

## 7. Class Diagram Rules

### Class definition

```
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound() void
    }
```

### Visibility markers

| Marker | Meaning |
|--------|---------|
| `+` | Public |
| `-` | Private |
| `#` | Protected |
| `~` | Package/Internal |

### Relationships

```
classDiagram
    Animal <|-- Dog : inherits
    Car *-- Engine : has
    University o-- Student : contains
    Animal ..> Food : depends
```

### Common errors

```
%% WRONG — generic type with unescaped angle brackets
class List {
    +List<String> items
}

%% CORRECT — use ~~ for generics
class List {
    +List~String~ items
}
```

---

## 8. ER Diagram Rules

### Relationship syntax

```
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

### Cardinality markers

| Marker | Meaning |
|--------|---------|
| `\|\|` | Exactly one |
| `o\|` | Zero or one |
| `}o` | Zero or more |
| `}\|` | One or more |
| `o{` | Zero or more |
| `\|{` | One or more |

### Entity attributes

```
erDiagram
    CUSTOMER {
        string name PK
        string email
        int age
    }
```

### Common errors

```
%% WRONG — missing relationship label
CUSTOMER ||--o{ ORDER

%% WRONG — spaces in entity name
CUSTOMER ORDER ||--o{ LINE ITEM : contains

%% CORRECT
CUSTOMER ||--o{ ORDER : places
CUSTOMER_ORDER ||--|{ LINE_ITEM : contains
```

---

## 9. State Diagram Rules

```
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : start
    Processing --> Done : complete
    Done --> [*]

    state Processing {
        [*] --> Step1
        Step1 --> Step2
        Step2 --> [*]
    }
```

### Common errors

```
%% WRONG — using single dash arrow
Idle -> Processing

%% WRONG — missing -v2 (works but may have issues)
stateDiagram

%% CORRECT
stateDiagram-v2
    Idle --> Processing
```

---

## 10. Gantt Chart Rules

```
gantt
    title Project Plan
    dateFormat YYYY-MM-DD
    section Phase 1
        Task A :a1, 2024-01-01, 30d
        Task B :after a1, 20d
    section Phase 2
        Task C :2024-03-01, 15d
```

### Common errors

```
%% WRONG — missing dateFormat
gantt
    title Plan
    section Work
        Task :2024-01-01, 30d

%% WRONG — invalid date format token
gantt
    dateFormat DD/MM/YYYY
```

---

## 11. Pie Chart Rules

```
pie title Favorite Pets
    "Dogs" : 45
    "Cats" : 30
    "Birds" : 15
    "Other" : 10
```

### Common errors

```
%% WRONG — unquoted labels with spaces
pie
    Dogs and Cats : 45

%% WRONG — missing colon
pie
    "Dogs" 45

%% CORRECT
pie
    "Dogs and Cats" : 45
```

---

## 12. Mindmap Rules

```
mindmap
    root((Central Topic))
        Topic A
            Subtopic A1
            Subtopic A2
        Topic B
            Subtopic B1
```

Indentation defines hierarchy. Use consistent indentation (spaces, not tabs).

### Node shapes in mindmap

| Syntax | Shape |
|--------|-------|
| `id` | Default |
| `id[text]` | Square |
| `id(text)` | Rounded |
| `id((text))` | Circle |
| `id))text((` | Bang |
| `id)text(` | Cloud |

---

## 13. Block Diagram Rules

```
block-beta
    columns 3
    a["Block A"] b["Block B"] c["Block C"]
    d["Block D"]:2 e["Block E"]

    a --> d
    b --> e
```

### Common errors

```
%% WRONG — using 'block' instead of 'block-beta'
block
    columns 2

%% CORRECT
block-beta
    columns 2
```

---

## 14. Style and ClassDef

### Flowchart styling

```
flowchart TD
    A --> B
    B --> C

    classDef highlight fill:#f96,stroke:#333,stroke-width:2px
    class A highlight

    style B fill:#bbf,stroke:#333
    linkStyle 0 stroke:red,stroke-width:2px
```

### Common errors

```
%% WRONG — classDef before node definitions (sometimes fails)
flowchart TD
    classDef highlight fill:#f96
    A --> B
    class A highlight

%% BETTER — classDef after node definitions
flowchart TD
    A --> B
    classDef highlight fill:#f96
    class A highlight

%% WRONG — missing # in hex colors
classDef red fill:f00

%% CORRECT
classDef red fill:#f00
```

---

## 15. Common Pitfalls

### Trailing whitespace / invisible characters

Copy-pasting from web pages or word processors can introduce invisible Unicode characters
(zero-width spaces, non-breaking spaces). These cause cryptic parse failures.

**Fix**: If the syntax looks correct but still fails, try retyping the problematic line manually.

### Tab vs spaces

Mermaid is sensitive to indentation in some diagram types (mindmap, block-beta).
Always use spaces, never tabs.

### Empty lines in critical positions

Some diagram types break if there are empty lines in unexpected places
(e.g., inside a `loop` or `alt` block in sequence diagrams).

### Case sensitivity

- Diagram type keywords are case-sensitive: `sequenceDiagram` not `SequenceDiagram`
- `TD` / `LR` directions are case-sensitive
- `classDef` / `linkStyle` are case-sensitive

### Maximum diagram size

Very large diagrams (100+ nodes) may hit rendering timeouts or memory limits.
Consider splitting into multiple diagrams.

### Comment syntax

Use `%%` for comments. Must be at the start of a line (after optional whitespace).

```
flowchart TD
    %% This is a comment
    A --> B
```

Do NOT use `//` or `/* */` — these are not valid Mermaid comments.

---

## 16. Unicode and Langium Parser Issues

Mermaid v11 uses the Langium parser framework, which tokenizes input as a stream of
ASCII-oriented grammar rules. Many Unicode characters that look normal in editors
cause cryptic "Syntax error in text" failures because the Langium lexer does not
recognize them as valid tokens.

### 16.1 Invisible / Zero-Width Characters

These are **the hardest to detect** because they're invisible in most editors.
They typically appear when copy-pasting from web pages, Word, or chat apps.

| Character | Unicode | Hex Bytes (UTF-8) | Fix |
|-----------|---------|-------------------|-----|
| Zero-width space | U+200B | `E2 80 8B` | Delete |
| Zero-width non-joiner | U+200C | `E2 80 8C` | Delete |
| Zero-width joiner | U+200D | `E2 80 8D` | Delete |
| Word joiner | U+2060 | `E2 81 A0` | Delete |
| BOM (byte order mark) | U+FEFF | `EF BB BF` | Delete |
| Non-breaking space | U+00A0 | `C2 A0` | Replace with ASCII space (U+0020) |
| Narrow no-break space | U+202F | `E2 80 AF` | Replace with ASCII space |
| Thin space | U+2009 | `E2 80 89` | Replace with ASCII space |
| Hair space | U+200A | `E2 80 8A` | Replace with ASCII space |
| Figure space | U+2007 | `E2 80 87` | Replace with ASCII space |
| Soft hyphen | U+00AD | `C2 AD` | Delete |

**Detection tip**: Run `grep -P '[\x{200B}-\x{200D}\x{FEFF}\x{00A0}\x{2060}]'` or
use `cat -A` to reveal invisible characters as `M-` prefixed sequences.

```
%% WRONG — contains zero-width space between A and --> (invisible)
A​ --> B

%% CORRECT
A --> B
```

### 16.2 Smart Quotes (Typographic Quotes)

Copied from Word, Google Docs, macOS auto-correction, or web pages.
The Langium parser only recognizes ASCII `"` (U+0022) and `'` (U+0027).

| Wrong | Unicode | Fix |
|-------|---------|-----|
| `"` (left double) | U+201C | `"` (U+0022) |
| `"` (right double) | U+201D | `"` (U+0022) |
| `'` (left single) | U+2018 | `'` (U+0027) |
| `'` (right single) | U+2019 | `'` (U+0027) |
| `„` (low double) | U+201E | `"` (U+0022) |
| `«` `»` (guillemets) | U+00AB, U+00BB | `"` (U+0022) |

```
%% WRONG — smart quotes from Word/Docs
A["데이터 처리"]
B['Configuration']

%% CORRECT — ASCII quotes
A["데이터 처리"]
B['Configuration']
```

### 16.3 Typographic Dashes

| Wrong | Unicode | Fix |
|-------|---------|-----|
| `—` (em dash) | U+2014 | `--` |
| `–` (en dash) | U+2013 | `-` |
| `‐` (hyphen char) | U+2010 | `-` (U+002D) |
| `−` (minus sign) | U+2212 | `-` (U+002D) |

Em/en dashes are especially dangerous because they break arrow syntax:

```
%% WRONG — en dash looks like a regular dash but breaks the arrow
A –> B
A —> B

%% CORRECT
A --> B
```

### 16.4 Unicode Arrows and Symbols

Unicode arrows look correct but Mermaid only recognizes ASCII arrow syntax.

| Wrong | Unicode | Fix |
|-------|---------|-----|
| `→` | U+2192 | `-->` (flowchart) or text |
| `←` | U+2190 | `<--` or text |
| `↔` | U+2194 | `<-->` |
| `⇒` | U+21D2 | `==>` |
| `⇐` | U+21D0 | `<==` |
| `➡` | U+27A1 | `-->` |
| `•` | U+2022 | `-` or `*` |
| `…` | U+2026 | `...` |
| `✓` | U+2713 | wrap in quotes: `"✓"` |
| `✗` | U+2717 | wrap in quotes: `"✗"` |

```
%% WRONG — Unicode arrow in flowchart
A → B

%% CORRECT
A --> B
```

### 16.5 Fullwidth CJK Punctuation

Common in Korean/Japanese/Chinese input — these characters have different code points
than their ASCII equivalents, and the Langium parser does not treat them as equivalent.

| Wrong (Fullwidth) | Unicode | Fix (ASCII) | Unicode |
|--------------------|---------|-------------|---------|
| `（` | U+FF08 | `(` | U+0028 |
| `）` | U+FF09 | `)` | U+0029 |
| `【` | U+3010 | `[` | U+005B |
| `】` | U+3011 | `]` | U+005D |
| `｛` | U+FF5B | `{` | U+007B |
| `｝` | U+FF5D | `}` | U+007D |
| `：` | U+FF1A | `:` | U+003A |
| `；` | U+FF1B | `;` | U+003B |
| `，` | U+FF0C | `,` | U+002C |
| `。` | U+3002 | `.` | U+002E |
| `＝` | U+FF1D | `=` | U+003D |
| `＞` | U+FF1E | `>` | U+003E |
| `＜` | U+FF1C | `<` | U+003C |
| `｜` | U+FF5C | `\|` | U+007C |

```
%% WRONG — fullwidth parentheses (from Korean IME)
A["데이터（원본）"]

%% CORRECT — ASCII parentheses inside quoted label
A["데이터(원본)"]
```

**Korean-specific note**: When the Korean IME is active, pressing `(` may produce
the fullwidth `（` instead of ASCII `(`. This is the most common source of
fullwidth characters in Korean Mermaid diagrams. Always switch to English input
when typing Mermaid syntax, or verify after pasting.

### 16.6 Mathematical and Technical Symbols

| Wrong | Unicode | Fix |
|-------|---------|-----|
| `×` (multiply) | U+00D7 | `x` or wrap in quotes |
| `÷` (divide) | U+00F7 | `/` or wrap in quotes |
| `±` | U+00B1 | `+/-` or wrap in quotes |
| `≤` | U+2264 | `<=` or wrap in quotes |
| `≥` | U+2265 | `>=` or wrap in quotes |
| `≠` | U+2260 | `!=` or wrap in quotes |
| `∞` | U+221E | wrap in quotes: `"∞"` |
| `²` `³` (superscript) | U+00B2, U+00B3 | wrap in quotes |
| `°` (degree) | U+00B0 | wrap in quotes |
| `µ` (micro) | U+00B5 | wrap in quotes |
| `™` `©` `®` | Various | wrap in quotes |

For labels: wrap in double quotes. For message text in sequence diagrams:
use Mermaid entity syntax (see section 17).

```
%% WRONG — bare Unicode math symbol in label
A[값 ≥ 100]

%% CORRECT — quoted label
A["값 >= 100"]
```

### 16.7 Detection Script

To scan a Mermaid file for problematic Unicode characters:

```bash
# Find non-ASCII characters in mermaid blocks
grep -Pn '[^\x00-\x7F]' file.md

# Specifically find invisible characters
grep -Pn '[\x{200B}-\x{200D}\x{FEFF}\x{00A0}\x{2060}\x{00AD}\x{2009}\x{200A}\x{202F}]' file.md

# Find smart quotes
grep -Pn '[\x{201C}\x{201D}\x{2018}\x{2019}\x{201E}]' file.md

# Find fullwidth CJK punctuation
grep -Pn '[\x{FF08}\x{FF09}\x{3010}\x{3011}\x{FF5B}\x{FF5D}\x{FF1A}\x{FF1B}\x{FF0C}\x{FF1D}]' file.md
```

---

## 17. Sequence Diagram Message Escaping

In sequence diagrams, message text (after `:` in arrows) and Note text are parsed
by the Langium lexer. Characters `{`, `}`, `[`, `]`, `"` in these positions
cause "Syntax error in text" because the parser tries to interpret them as
diagram syntax tokens.

### Fix: Use Mermaid entity syntax

| Character | Entity | Description |
|-----------|--------|-------------|
| `{` | `#123;` | Opening curly brace |
| `}` | `#125;` | Closing curly brace |
| `[` | `#91;` | Opening bracket |
| `]` | `#93;` | Closing bracket |
| `"` | `#34;` | Double quote |
| `'` | `#39;` | Single quote |
| `#` | `#35;` | Hash (prevents entity conflicts) |
| `&` | `#38;` | Ampersand |
| `<` | `#lt;` | Less than |
| `>` | `#gt;` | Greater than |

Entities are rendered as the original character in the diagram output.

### Examples

```
%% WRONG — curly braces in message text
V-->>C: 200 OK {id: 1, status: "ok"}

%% CORRECT — entities for braces and quotes
V-->>C: 200 OK #123;id: 1, status: #34;ok#34;#125;

%% WRONG — brackets in message
V->>P: paginate [page=1, size=100]

%% CORRECT
V->>P: paginate #91;page=1, size=100#93;

%% WRONG — braces in Note
Note over V: PATCH /api/users/{id}/

%% CORRECT
Note over V: PATCH /api/users/#123;id#125;/
```

### When to apply

Only escape characters in these positions:
- **Arrow message text**: the part after `:` in `A->>B: <this text>`
- **Note text**: the part after `:` in `Note over A: <this text>`
- **URL path parameters** in messages: `{id}`, `{username}`, `{run_id}`

Do NOT escape in:
- Participant declarations (`participant A as Name`)
- Control flow keywords (`loop`, `alt`, `else`, `end`)
- Activation markers (`+`, `-`)
- Comments (`%%`)

---

## 18. Sequence Diagram Reserved Words

Certain words are reserved as syntax keywords in sequence diagrams.
Using them as participant IDs causes the Mermaid parser to interpret them
as control flow constructs instead of participant references, leading to
"Syntax error in text" or silently broken rendering.

This is especially insidious because `mermaid.parse()` may pass validation
while the rendering stage fails — the structural check doesn't catch
reserved word collisions in participant IDs.

### 18.1 Full Reserved Word List

Comparison is **case-insensitive** — `OPT`, `Opt`, and `opt` all collide.

| Reserved Word | Mermaid Syntax | Meaning | Safe Rename |
|---------------|---------------|---------|-------------|
| `opt` | `opt Description ... end` | Optional fragment | `OPTA` |
| `alt` | `alt Description ... else ... end` | Alternative paths | `ALTR` |
| `par` | `par Description ... and ... end` | Parallel execution | `PRSR` |
| `loop` | `loop Description ... end` | Loop block | `LOOPN` |
| `rect` | `rect rgb(...) ... end` | Highlight region | `RCTL` |
| `note` | `Note over A: text` | Note annotation | `NOTEB` |
| `end` | block terminator | Block closing | `ENDP` |
| `and` | `par` separator | Parallel separator | `ANDN` |
| `else` | `alt` separator | Alternative separator | `ELSN` |
| `break` | `break Description ... end` | Break block | `BRKN` |
| `critical` | `critical Description ... end` | Critical section | `CRIT` |
| `activate` | `activate A` | Activation bar | `ACTV` |
| `deactivate` | `deactivate A` | Deactivation bar | `DEACTV` |

### 18.2 Common Dangerous Abbreviations

These are real-world abbreviations that frequently collide with reserved words:

| Intended Participant | Collides With | Example Context |
|---------------------|---------------|-----------------|
| `OPT` (Optuna, Optimizer) | `opt` | ML optimization pipelines |
| `ALT` (Alternative, Alerting) | `alt` | A/B testing, monitoring |
| `PAR` (Parser, Parallel) | `par` | Compiler, data pipelines |
| `END` (Endpoint) | `end` | API documentation |
| `NOTE` (Notebook, Notepad) | `note` | Documentation systems |
| `RECT` (Rectangle, Rectifier) | `rect` | UI/graphics code |
| `LOOP` (Looper, EventLoop) | `loop` | Async/event systems |

### 18.3 How the Collision Happens

```
sequenceDiagram
    participant OPT as Optuna
    participant CEL as Celery
    CEL->>OPT: create_study
```

The parser reads `CEL->>OPT: create_study` and tokenizes `OPT` as the start
of an `opt` (optional fragment) block, not as a participant reference.
This produces a parse error or silently garbles the diagram.

### 18.4 Fix: Rename the Participant ID

Rename the ID while keeping the `as` alias (display name) unchanged:

```
%% WRONG
participant OPT as Optuna
CEL->>OPT: create_study

%% CORRECT — ID renamed, display name preserved
participant OPTA as Optuna
CEL->>OPTA: create_study
```

When renaming, update **every reference** to the old ID throughout the block:
- `participant` declaration
- Arrow sources and targets (`A->>OPT:` → `A->>OPTA:`)
- Notes (`Note over OPT:` → `Note over OPTA:`)
- Activation (`activate OPT` → `activate OPTA`)

### 18.5 Automated Detection

Use the bundled script to scan for reserved word conflicts:

```bash
# Lint only
python scripts/fix_mermaid.py docs/PROJECT_ANALYSIS.md

# Auto-fix
python scripts/fix_mermaid.py docs/ --fix
```

Or detect manually with grep:

```bash
# Find participant lines with potential reserved words
grep -nE '^\s*participant\s+(opt|alt|par|loop|rect|note|end|and|else|break|critical|activate|deactivate)\s' docs/*.md
```

---

## 19. mmdc Error Catalog (for the `--with-mmdc` feedback loop)

The Mermaid CLI emits stderr in a predictable shape. `validate_mermaid.py`
parses it with these regexes:

| Field | Regex | Example capture |
|---|---|---|
| line | `Parse error on line (\d+):` | `3` |
| context | `Parse error on line \d+:\s*\n(.+?)\n[-^]+\^` | `...ant end as User` |
| expected + got | `Expecting\s+(.+?),\s+got '([^']+)'` | `(['NEWLINE', 'participant', …], 'end')` |

### 19.1 Canonical error shapes and their fixes

**Reserved sequence-diagram keyword as participant ID.**

```
Error: Parse error on line 3:
...ant end as User    end->>A: hello
----------------------^
Expecting 'SPACE', 'NEWLINE', 'create', 'participant', …, got 'end'
```

- `got` is one of: `end`, `opt`, `alt`, `par`, `loop`, `rect`, `note`,
  `and`, `else`, `break`, `critical`, `activate`, `deactivate`.
- `expected` contains `'participant'`.
- **Rule triggered:** `reserved-word` → `SAFE_RENAMES[got]` (e.g. `end → ENDP`).

**Unquoted special character inside a flowchart node label.**

```
Error: Parse error on line 2:
...A[start] --> B(do (nested) stuff)
-----------------------^
Expecting 'SQE', 'PE', 'PIPE', 'UNICODE_TEXT', 'TEXT', got 'PS'
```

- `got` is a shape opener: `PS` (`(`), `SQS` (`[`), `DOUBLECIRCLESTART`.
- `expected` contains one of: `SQE`, `PE`, `DOUBLECIRCLEEND`,
  `STADIUMEND`, `SUBROUTINEEND`, `CYLINDEREND`, `DIAMOND_STOP`.
- **Rule triggered:** `unquoted-label` → flagged for manual quoting. The
  linter does **not** auto-rewrite labels because the intended quoting
  style (single vs. double quotes, `&quot;` escapes) is author-dependent.

**Unclosed subgraph / stray block keyword.**

```
Error: Parse error on line 3:
... --> B    unclosed subgraph test
----------------------^
Expecting 'SEMI', 'NEWLINE', 'SPACE', 'EOF', …, got 'subgraph'
```

- Usually caused by a `subgraph` declaration on the same logical line as
  an arrow, or a missing `end`.
- **Rule triggered:** *unknown* — reported verbatim, user decides.

### 19.2 Adding a new pattern

1. Reproduce the error with a minimal fixture and capture stderr.
2. Add a branch to `suggest_fix_for_mmdc_error` in `scripts/fix_mermaid.py`
   with a named rule and a hint string.
3. If the fix is safe to automate, extend `process_file` or add a new
   `apply_*` helper and thread it through `fix_with_mmdc_feedback`.
4. Add a test in `tests/test_fix_mermaid.py` asserting the rule name.
5. Append the error shape here so future maintainers know it is covered.
