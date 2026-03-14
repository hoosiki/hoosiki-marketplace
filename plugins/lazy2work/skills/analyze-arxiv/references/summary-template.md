# Paper Summary Template

Follow this format to write a **detailed** paper summary document. Each section must be included.
If the paper does not explicitly address a section, note "Not explicitly addressed in the paper."
Target length is **150+ lines**, and 200+ lines is recommended for complex papers.

---

```markdown
# {Paper Title}

> **Authors**: {Author list}
> **Published**: {Year/Conference/Journal}
> **arXiv**: {arXiv ID and link}
> **Date**: {YYYYMMDD}

---

## 1. Problem Statement

- **Concrete** limitations of existing research/systems (which method, why, how much insufficient — quantitatively)
- Core question or problem this paper addresses in **a clear single sentence**
- Importance/impact of the problem (both practical and academic perspectives)
- Concrete numbers showing problem scale/difficulty (e.g., search space size, existing error rates)

## 2. Key Contribution

Numbered list of 3-5 contributions:
1. **{Contribution 1 title}**: Concrete description (specify: first/best/novel)
2. **{Contribution 2 title}**: Concrete description
3. ...

## 3. Methodology

### 3.1 Overall Architecture/Framework
- **Decompose** the system/model structure by component
- Role and relationships of each core module/component
- If applicable, organize key design parameters in a **table**:

| Parameter | Value/Range | Description |
|-----------|-------------|-------------|
| ... | ... | ... |

### 3.2 Core Technique
- Describe the proposed technique's **operation step-by-step**
- Include key equations in LaTeX with **variable definitions**:

$$equation$$

Where:
- $var1$: meaning
- $var2$: meaning

- Include pseudo-code if algorithmic:
```
1: Step description
2: ...
```

- Briefly explain design rationale (why this approach)

### 3.3 Training/Learning Method (if applicable)
- Loss function (with equations), optimization method (optimizer, learning rate, etc.)
- Training data and preprocessing pipeline
- Key hyperparameters and selection rationale
- If not applicable: briefly state reason (e.g., "Measurement study with no training process")

## 4. Experiments

### 4.1 Experimental Setup
- Dataset/simulation environment: name, scale, characteristics, **concrete conditions/settings**
- Comparisons (baseline models/methods) — briefly describe each
- Evaluation metrics — include **one-line definition** for each

### 4.2 Experimental Design
- List major experimental scenarios with **numbering**
- Ablation study design (if present) — what elements are removed/changed for validation
- Statistical validation (repetition count, confidence intervals, etc.)

## 5. Results

### 5.1 Main Performance Comparison
**Must reproduce the paper's key result table as a markdown table** (at least 1):

| Method | Metric1 | Metric2 | Metric3 |
|--------|---------|---------|---------|
| Baseline A | concrete number | concrete number | concrete number |
| Baseline B | concrete number | concrete number | concrete number |
| **Proposed** | **concrete number** | **concrete number** | **concrete number** |

### 5.2 Additional Analysis (if applicable)
- Ablation study results as separate table or list
- Parameter sensitivity analysis, scaling experiments, etc.

### 5.3 Key Findings
- 3-5 most important experimental results **with concrete numbers**
- Include interpretation/meaning (not just enumeration, but insight)

## 6. Limitations

### Author-Acknowledged Limitations
- List limitations directly mentioned in the paper

### Reviewer/Analyst Additional Limitations
- Points not addressed in the paper but requiring attention

### Future Research Directions
- Directions proposed by authors + potential developments identified by analyst

---

## Appendix: Key Terminology

| Term | Description |
|------|-------------|
| ... | ... |
```
