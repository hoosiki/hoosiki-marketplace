---
name: index-repo
description: "Write PROJECT_INDEX files to cut repo exploration tokens"
license: MIT
metadata:
  author: "Junsang Park (adapted from SuperClaude Framework)"
  version: "1.0.0"
  upstream: "SuperClaude Framework 4.3.0"
  source: "src/superclaude/commands/index-repo.md"
---

# /sc:index-repo - Repository Index Creator

## When to Use
- The user asks to index a repository or create `PROJECT_INDEX.md`
- A large repository will be explored repeatedly across sessions
- An existing index has drifted from the code

## Problem Statement

**Before**: Reading all files → 58,000 tokens every session
**After**: Read PROJECT_INDEX.md → 3,000 tokens (94% reduction)

## Index Creation Flow

### Phase 1: Analyze Repository Structure

**Parallel analysis** (5 concurrent `search_files` calls with `target='files'`):

1. **Code Structure**
   ```
   src/**/*.{ts,py,js,tsx,jsx}
   lib/**/*.{ts,py,js}
   ```

2. **Documentation**
   ```
   docs/**/*.md
   *.md (root level)
   README*.md
   ```

3. **Configuration**
   ```
   *.toml
   *.yaml, *.yml
   *.json (exclude package-lock, node_modules)
   ```

4. **Tests**
   ```
   tests/**/*.{py,ts,js}
   **/*.test.{ts,py,js}
   **/*.spec.{ts,py,js}
   ```

5. **Scripts & Tools**
   ```
   scripts/**/*
   bin/**/*
   tools/**/*
   ```

### Phase 2: Extract Metadata

For each file category, extract:
- Entry points (main.py, index.ts, cli.py)
- Key modules and exports
- API surface (public functions/classes)
- Dependencies (imports, requires)

### Phase 3: Generate Index

Create `PROJECT_INDEX.md` with structure:

```markdown
# Project Index: {project_name}

Generated: {timestamp}

## 📁 Project Structure

{tree view of main directories}

## 🚀 Entry Points

- CLI: {path} - {description}
- API: {path} - {description}
- Tests: {path} - {description}

## 📦 Core Modules

### Module: {name}
- Path: {path}
- Exports: {list}
- Purpose: {1-line description}

## 🔧 Configuration

- {config_file}: {purpose}

## 📚 Documentation

- {doc_file}: {topic}

## 🧪 Test Coverage

- Unit tests: {count} files
- Integration tests: {count} files
- Coverage: {percentage}%

## 🔗 Key Dependencies

- {dependency}: {version} - {purpose}

## 📝 Quick Start

1. {setup step}
2. {run step}
3. {test step}
```

### Phase 4: Validation

Quality checks:
- [ ] All entry points identified?
- [ ] Core modules documented?
- [ ] Index size < 5KB?
- [ ] Human-readable format?

---

## Usage

**Create index**:
```
/sc:index-repo
```

**Update existing index**:
```
/sc:index-repo mode=update
```

**Quick index (skip tests)**:
```
/sc:index-repo mode=quick
```

---

## Token Efficiency

**ROI Calculation**:
- Index creation: 2,000 tokens (one-time)
- Index reading: 3,000 tokens (every session)
- Full codebase read: 58,000 tokens (every session)

**Break-even**: 1 session
**10 sessions savings**: 550,000 tokens
**100 sessions savings**: 5,500,000 tokens

---

## Output Format

Creates two files:
1. `PROJECT_INDEX.md` (3KB, human-readable)
2. `PROJECT_INDEX.json` (10KB, machine-readable)
