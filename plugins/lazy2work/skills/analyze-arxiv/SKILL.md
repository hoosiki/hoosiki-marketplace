---
name: analyze-arxiv
description: Analyze arXiv papers by fetching HTML content from ar5iv.labs.arxiv.org,
  creating structured summary documents (Problem Statement, Key Contribution,
  Methodology, Experiments, Results, Limitations) and prerequisite knowledge
  documents with deep research. Triggers on arXiv paper URLs
  (arxiv.org/abs/..., arxiv.org/pdf/...) or requests to analyze, summarize,
  or study an academic paper from arXiv. Also triggers on paper notes,
  paper review, paper notes, paper study.
---

# arXiv Paper Analyzer

Generates (1) a structured paper summary document and (2) a prerequisite knowledge research document from an arXiv paper URL.

## Workflow

### Phase 1: URL Parsing & Metadata Extraction

1. Extract arXiv ID from the provided URL.

   Supported URL formats:
   - `https://arxiv.org/abs/2301.12345` → ID: `2301.12345`
   - `https://arxiv.org/abs/2301.12345v2` → ID: `2301.12345v2`
   - `https://arxiv.org/pdf/2301.12345` → ID: `2301.12345`
   - `https://ar5iv.labs.arxiv.org/html/2301.12345` → ID: `2301.12345`
   - Bare ID input (e.g., `2301.12345`) is also accepted.

2. Construct the ar5iv HTML URL:
   ```
   https://ar5iv.labs.arxiv.org/html/{arxiv_id}
   ```

3. Determine the paper's field from category info or content:
   - Examples: `NLP`, `Computer-Vision`, `Reinforcement-Learning`, `LLM`, `Diffusion-Models`
   - Use English kebab-case (used as folder name)

### Phase 2: Read Paper Content

Fetch the full paper content from the ar5iv HTML page **without omission**.

**Reading strategy:**

1. Use WebFetch or an appropriate tool to read the ar5iv HTML page.
2. If the content is too long for a single read:
   - Split by sections (Abstract, Introduction, Related Work, Method, Experiments, Conclusion, etc.)
   - Read each section sequentially, accumulating information
   - **All sections must be read** — especially Method/Experiments/Results
3. From the content, identify and note the following **with concrete numbers**:
   - Paper title, authors, venue
   - Key content of each section
   - **Key equations**: Record precisely in LaTeX (including variable definitions)
   - **Algorithms**: Record step-by-step in pseudo-code form
   - **Tables**: Record as tables with concrete numbers
   - **Graphs/Figures**: Describe axis labels, trends, key values in text
   - **Hyperparameters/experimental conditions**: Record all specific settings
4. Supplement any insufficient sections via references or web search.

### Phase 3: Write Summary Document

Follow the template in [references/summary-template.md](references/summary-template.md) to write a **detailed** summary document.
Target length is **150+ lines**, and 200+ lines is recommended for complex papers.

**Required sections with detailed writing guide:**

1. **Problem Statement** — What problem is being solved?
   - Describe existing research limitations **concretely** (what method, why insufficient)
   - Support problem importance quantitatively (e.g., "existing methods have X% error", "takes Y hours")
   - Define the core question this paper addresses in a clear single sentence

2. **Key Contribution** — Core contributions/differentiators
   - List 3-5 contributions with **numbering**
   - Specify whether each is "first", "best", or "novel"
   - Distinguish theoretical vs. practical contributions

3. **Methodology** — Core methodology
   - **3.1 Overall architecture**: Explain all system components. Organize parameters/settings in a table
   - **3.2 Core technique**: Describe the proposed technique step-by-step. Include LaTeX equations with variable definitions. Include pseudo-code for algorithms
   - **3.3 Training method**: Specify loss functions, optimizers, hyperparameters concretely. If not applicable, briefly state reason

4. **Experiments** — Experimental design
   - **Concrete conditions** for datasets/simulation environments (scale, version, settings)
   - List baselines/comparisons clearly
   - Include **definitions** of evaluation metrics

5. **Results** — Key result numbers
   - **Must reproduce the paper's key tables** as markdown tables (at least 1 quantitative table)
   - Describe 3-5 key findings with concrete numbers
   - Separate ablation/additional analysis into subsections if present

6. **Limitations** — Limitations
   - Distinguish between **author-acknowledged limitations** and **reviewer/analyst additional limitations**
   - Organize future research directions separately

**File save path:**
```
papers/summary/{field}/{YYYYMMDD}/{paper_title}_{YYYYMMDD}.md
```

Rules:
- `{field}`: Field name from Phase 1 (kebab-case, English)
- `{YYYYMMDD}`: Today's date
- `{paper_title}`: Paper title converted to snake_case English (lowercase, spaces→underscores, special chars removed, truncated to 30 chars)
- Example: `papers/summary/NLP/20260225/attention_is_all_you_need_20260225.md`

### Phase 4: Prerequisite Identification & Research

1. Based on paper content from Phases 2-3, identify **prerequisite knowledge essential for understanding the paper**.

   Identification criteria:
   - Concepts required to understand the paper's methodology
   - Concepts the paper assumes the reader already knows
   - Exclude overly basic concepts (e.g., basic linear algebra, Python syntax)
   - Typically 3-7 core prerequisites is appropriate

2. For each identified prerequisite, research using web search tools:
   - Definition, core principles, key equations for each concept
   - Connection points: how used/extended in this paper
   - Examples or analogies for intuitive understanding

3. Follow the template in [references/prerequisite-template.md](references/prerequisite-template.md) to write the prerequisite document.

**File save path:**
```
papers/prerequisite/{field}/{YYYYMMDD}/research_{paper_title}_{YYYYMMDD}.md
```

### Phase 5: Final Check & Report

1. Report the paths of both generated documents to the user.
2. Provide a 3-line summary of the paper's key points.
3. List the prerequisite knowledge included in the prerequisite document.
4. Ask if there are additional questions.

## Examples

### Example 1: Basic Usage

User: `https://arxiv.org/abs/2301.12345 analyze this paper`

Actions:
1. Extract ID `2301.12345` → read `https://ar5iv.labs.arxiv.org/html/2301.12345`
2. Determine field (e.g., `LLM`)
3. Summary → `papers/summary/LLM/20260225/paper_title_20260225.md`
4. Prerequisite research → `papers/prerequisite/LLM/20260225/research_paper_title_20260225.md`
5. Report results

### Example 2: Long Paper

User: `https://arxiv.org/abs/2005.14165 analyze this`

Actions:
1. Attempt to read from ar5iv → content is very long
2. Read section by section (Abstract → Intro → Method → ... → Conclusion)
3. Write summary from accumulated information
4. Identify prerequisites (e.g., Transformer, Scaling Laws, Few-shot Learning)
5. Research each prerequisite
6. Write prerequisite document

### Example 3: Bare ID

User: `2401.04088 paper analysis`

Actions:
1. Recognize ID `2401.04088` → construct ar5iv URL
2. Same workflow follows

## Troubleshooting

### ar5iv Page Inaccessible

Some papers may not yet have ar5iv HTML conversion.

Solution:
1. Read abstract and metadata from `https://arxiv.org/abs/{id}`
2. Read the PDF via Read tool page by page (max 20 pages at a time)
3. Combine all information to write documents

### Field Determination Difficulty

For interdisciplinary papers, choose the most central field or confirm with the user.
Example: NLP + RL paper → if core contribution is NLP, use `NLP`; if RL, use `Reinforcement-Learning`
