# Mermaid v11.x / v12.x Syntax Reference — Common Errors and Fixes

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
16. [Unicode Characters in Mermaid Syntax](#16-unicode-characters-in-mermaid-syntax)
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
`erDiagram`, `gantt`, `pie`, `gitGraph`, `mindmap`, `timeline`,
`block`, `journey`, `quadrantChart`, `xychart`,
`requirementDiagram`, `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`,
`C4Deployment`, `sankey`, `packet`, `architecture-beta`, `kanban`,
`radar-beta`, `treemap-beta`, `venn-beta` (v11.13.0+), `ishikawa-beta` (v11.13.0+),
`usecase-beta` (v12.0.0+).

Keywords are case-sensitive (`gitgraph` fails with "No diagram type detected").
`block-beta`, `xychart-beta`, `sankey-beta`, and `packet-beta` are still accepted.

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
Fullwidth and typographic punctuation (`（）`, `：`, `→`, `—`, `“”`) is not a special
character here: it renders unquoted on Mermaid 11.12.2 and 12.1.0 (section 16).

```
%% SAFE (simple label, no special chars)
A[데이터]
D[데이터（원본）]

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

If a node ID is the all-lowercase word `end`, Mermaid treats it as a subgraph
closer. IDs that merely start with `end` (`endpoint`) are fine.

```
%% WRONG — "end" is parsed as subgraph closer
flowchart TD
    subgraph Process
        start --> end
    end

%% CORRECT — rename the ID and quote the label, or capitalize (End / END)
flowchart TD
    subgraph Process
        start --> ep["end"]
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
%% NOT an error — dateFormat is optional; the default input format is YYYY-MM-DD
gantt
    title Plan
    section Work
        Task :2024-01-01, 30d

%% NOT an error — DD/MM/YYYY is a valid dayjs format; task dates must then use it
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
block
    columns 3
    a["Block A"] b["Block B"] c["Block C"]
    d["Block D"]:2 e["Block E"]

    a --> d
    b --> e
```

### Keyword

```
%% Both work — `block` is the documented keyword, `block-beta` is still accepted
block
    columns 2

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

Copy-pasting from web pages or word processors can introduce invisible Unicode characters.
Zero-width characters (U+200B, U+200C, U+200D, U+2060) and soft hyphens (U+00AD) glued to
a node ID or arrow cause cryptic "Lexical error" failures. Non-breaking and other Unicode
spaces are harmless: Mermaid 11.12.2 and 12.1.0 treat them as whitespace. See section 16.

**Fix**: run `scripts/fix_mermaid.py --fix`, or retype the problematic line manually.

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

## 16. Unicode Characters in Mermaid Syntax

Flowchart, sequence, class and state diagrams are parsed by Jison grammars in
both v11 and v12. The Langium parser (`@mermaid-js/parser`) only covers info,
pie, packet, gitGraph, architecture, radar, treemap and some newer diagram
types. Those Jison grammars pass label text through unchanged, so a Unicode
character fails only where Mermaid expects **syntax**: a node ID, an arrow, a
separator, a label delimiter, or a bare subgraph title.

Every rule in this section was checked with `mmdc` on Mermaid **11.12.2** and
**12.1.0**. Each character was rendered in 13 text contexts: flowchart `[..]`,
`(..)` and `["..."]` labels, `|..|` and `-- .. -->` edge labels, sequence
messages, notes and `participant .. as` aliases, class relation labels and
`class A["..."]`, and state transition labels, descriptions and
`state ".." as` names. It was also rendered in the syntax positions listed
below.

**Never convert Unicode inside label text.** All of these characters render
there, and replacing them with ASCII adds syntax:

```
%% Renders on 11.12.2 and 12.1.0
D[데이터（원본）]

%% Parse error: ASCII parentheses are node-shape syntax
D[데이터(원본)]
```

### 16.1 Where Unicode breaks, and what `fix_mermaid.py` does

The fixer rewrites only the syntax part of a line. Label text, edge labels,
messages, notes, aliases, comments, front matter, class member bodies and
multi-line state notes are never touched. Other diagram types (gantt, pie,
mindmap, …) are left alone, apart from deleting zero-width characters in
front of the diagram keyword.

| Character(s) | Fails as syntax (11.12.2 and 12.1.0) | `fix_mermaid.py` |
|---|---|---|
| Zero-width U+200B, U+200C, U+200D, U+2060; soft hyphen U+00AD | Glued to an ID: `A<U+200B> --> B` is a lexical error. In sequence and state diagrams it silently creates a second participant or state. In front of the diagram keyword it gives "No diagram type detected" | Deleted in syntax only (rule `invisible-char`). Kept in labels, where deleting U+200D would split an emoji such as 👩‍💻 into two |
| Typographic dashes `—` `–` `‐` `−` | Inside an arrow: `A —> B`, `A–>>B`, `A <–> B`. `S1 –> S2` renders a state named `–>` | The dash run before `>` becomes ASCII and is clamped to a valid length: flowchart, class and state need 2 or more (`–>` → `-->`), sequence takes at most 2 (`-—>>` → `-->>`). In a flowchart, a free-standing dash that opens an edge label also becomes `--` (`A — yes —> B` → `A -- yes --> B`) (rule `typo-dash`) |
| `→` `↔` `⇒` | As an arrow: `A → B`, `A→B: hi`. `S1 → S2` renders a state named `→` | Flowchart `→` `↔` `⇒` → `-->` `<-->` `==>`; class and state `→` → `-->`; sequence `→` → `->>` (rule `unicode-arrow`) |
| `←` `⇐`, and `↔` `⇒` outside flowcharts | As an arrow. The ASCII look-alikes `<--`, `<==`, sequence `<-->` and `==>` fail too | **Warning only** (`unicode-arrow-manual`): swap the operands and use a right-pointing arrow (`A ← B` → `B --> A`) |
| Fullwidth `（` `）` `【` `】` `｛` `｝` `｜` `；` `，` `＝` `＞` `＜` `：` | As flowchart syntax: a shape delimiter after an ID (`A（데이터）`), edge-label pipes (`-->｜라벨｜`), arrows (`--＞`, `＝＝>`), a statement separator (`；`), `class A，B red`, CSS (`fill：#f00`) | Converted to ASCII in flowchart syntax only (rule `fullwidth-cjk`) |
| Fullwidth colon `：` | As the label separator: `A->>B： hi` and `Note over A： x` fail, `A --> B ： x` fails in class diagrams, and in state diagrams `S1 --> S2 ： x` renders a state named `：` | Only the separator becomes `:`; the text after it is untouched (rule `fullwidth-cjk`). Skipped when another `:` follows with no space in between (`A->>B：x: hi`), because the `：` may then be part of an ID |
| `。` | At the end of a flowchart statement: `A --> B。` | **Warning only** (`fullwidth-period`): the ASCII `B.` renders a node named `B.`, so delete the character by hand |
| Curly double quotes `“` `”` `„` | As label delimiters when the label needs quoting: `A[“a (b)”]`, `A(“a [b]”)`, `A -->|“yes (y)”| B`. Always in `class A[“…”]` and `state “…” as S1` | The delimiter pair becomes ASCII `"` (rule `smart-quote`). Left alone when the label renders unquoted: `A[“데이터”]` shows the curly quotes as text |
| Any of the above in a bare subgraph title | `subgraph 처리（원본）`, `subgraph 처리–원본` and `subgraph “처리”` all fail, and so does `subgraph 처리(원본)` | The title is quoted instead of converted: `subgraph "처리（원본）"` (rule `subgraph-title-quote`) |

Typographic dashes in sequence arrows with an `x` or `)` head (`A–xB`) are
not rewritten, because the same characters can be part of a participant
name. The `--with-mmdc` loop reports them as parse errors.

### 16.2 Characters that need no fix

These render on 11.12.2 and 12.1.0 in every position tested, so the fixer no
longer rewrites them:

| Character(s) | Evidence |
|---|---|
| BOM U+FEFF | Renders anywhere, including in front of the diagram keyword and glued to an ID |
| Non-breaking U+00A0, narrow no-break U+202F, thin U+2009, hair U+200A and figure U+2007 spaces | Treated as whitespace as indentation, between an ID and its arrow, and after `participant`. U+00A0 was also tested between `flowchart` and `TD`, around `as`, and in subgraph titles |
| Single curly quotes `‘` `’`, guillemets `«` `»`, and curly quotes used as text | Render in every text context. Converting them inside a quoted label breaks it: `A["say “hi”"]` → `A["say "hi""]` renders as `say hi` |
| Ellipsis `…` | Renders in every text context; it has no syntax role |
| `×` `÷` `±` `≤` `≥` `≠` `∞` `²` `°` `µ` `™` `©` `➡` `•` `✓` `✗` | Render unquoted in node labels, edge labels, sequence messages and notes, class relation labels and state transition labels: `A[값 ≥ 100]` is fine |

### 16.3 Why label text is never converted

The previous fixer converted these characters on every line. On 11.12.2 and
12.1.0 that broke diagrams that rendered:

| Rendering input | After an ASCII conversion | Result |
|---|---|---|
| `D[데이터（원본）]` | `D[데이터(원본)]` | Parse error |
| `A -->|값｜값| B` | `A -->|값|값| B` | Parse error |
| `A->>B: 값；값` | `A->>B: 값;값` | Parse error (`;` ends the statement) |
| `A -- 값—값 --> B` | `A -- 값--값 --> B` | Parse error |
| `A[값“값]`, `state "값“값" as S1` | `A[값"값]`, `state "값"값" as S1` | Parse error |
| `S1 --> S2 : 값；값` | `S1 --> S2 : 값;값` | Renders an extra state named `;값` |
| `A -- 값→값 --> B` | `A -- 값-->값 --> B` | Renders an extra node `값` |

**CJK input methods**: fullwidth punctuation typed by a Korean, Japanese or
Chinese IME is harmless inside labels. It only matters when it replaces
syntax: `：` as the message separator, `（` right after a node ID, `｜` around
an edge label. Switch to English input for the syntax, not for label text.

### 16.4 Detection

Run the bundled linter (`python3 scripts/fix_mermaid.py file.md`). It reports
only characters in syntax positions. For a quick manual scan:

```bash
# Zero-width characters and soft hyphens (they break IDs; harmless in labels)
grep -nP '[\x{200B}-\x{200D}\x{2060}\x{00AD}]' file.md

# Typographic dashes or Unicode arrows used as arrows
grep -nP '[\x{2010}\x{2013}\x{2014}\x{2212}]>|\s[\x{2190}\x{2192}\x{2194}\x{21D0}\x{21D2}]\s' file.md

# Fullwidth colon used as a sequence-message separator
grep -nP '^\s*[^:\x{FF1A}]+-[-]?>>?[^:\x{FF1A}]+\x{FF1A}' file.md
```

---

## 17. Sequence Diagram Message Escaping

On Mermaid 11.12.2 and 12.1.0, braces, brackets and double quotes in message,
note and alias text render as typed, and the `#123;`-style entities produce
the same output. `fix_mermaid.py` therefore no longer escapes them:

```
%% All of these render on 11.12.2 and 12.1.0
V-->>C: 200 OK {id: 1, status: "ok"}
V->>P: paginate [page=1, size=100]
Note over V: PATCH /api/users/{id}/
A->>B: POST {"a": [1, 2], "b": {"c": null}}
```

Two characters still need a Mermaid entity in message, note and
`participant .. as` alias text:

| Character | Problem | Entity |
|-----------|---------|--------|
| `;` | Ends the statement: `A->>B: a; b` is a parse error (a trailing `;` is accepted) | `#59;` |
| `#` | Starts an entity: `A->>B: issue #1 fixed` silently renders as `issue` | `#35;` |

```
%% WRONG: parse error
A->>B: retry; then fail

%% CORRECT
A->>B: retry#59; then fail

%% WRONG: renders only "issue"
A->>B: issue #1 fixed

%% CORRECT
A->>B: issue #35;1 fixed
```

The fixer does not rewrite these automatically. A `;` shows up as a parse
error in the `--with-mmdc` loop, but a `#` does not fail, so check messages
containing `#` by eye.

Entities are `#<decimal>;` (or a named entity such as `#lt;`) and render as
the original character. Other useful ones: `#123;` `{`, `#125;` `}`,
`#91;` `[`, `#93;` `]`, `#34;` `"`, `#38;` `&`, `#lt;` `<`, `#gt;` `>`.

Only escape in these positions:
- **Arrow message text**: the part after `:` in `A->>B: <this text>`
- **Note text**: the part after `:` in `Note over A: <this text>`
- **Alias text**: the part after `as` in `participant A as <this text>`

Do NOT escape in:
- Participant IDs
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
