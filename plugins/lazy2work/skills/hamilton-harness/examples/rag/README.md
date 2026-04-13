# Example — rag_ingestion (RAG)

A retrieval-augmented-generation ingestion pipeline: directory of documents →
chunks → embeddings → vector index.

## Highlights

- **`Chunk` schema** — typed chunk objects with offsets, validated via
  `RowModelValidator` on the list output.
- **External config as input** — the embedding model name, chunk size, and
  store path are all `source: input`, so the same pipeline can run with
  different configurations.
- **Critical final node** — `vector_index_path` has `importance: critical`;
  downstream production systems rely on it.

## Try it

Copy the example contents into your project's `hamilton_pipeline/`, then run
from there:

```bash
mkdir -p hamilton_pipeline && cp -r "$CLAUDE_SKILL_DIR/examples/rag/"* hamilton_pipeline/
cd hamilton_pipeline
python "$CLAUDE_SKILL_DIR/scripts/viz.py" specs/rag_ingestion.yaml --format mermaid
```

Or experiment in-place: `cd "$CLAUDE_SKILL_DIR/examples/rag"` and run the same
`viz.py` command.

The Mermaid output is copy-pasteable into a PR description or Notion page.

## Teaching points

- RAG is a natural fit for Hamilton — ingestion is a clear DAG (linear with
  maybe a fan-out for chunking strategies).
- Keep the **embedding model name** as a parameter, not a hardcoded constant.
  This lets you A/B test models by swapping the input without rebuilding the
  DAG.
- Think about where you want `@check_output` — embeddings should probably
  check `no_nulls` and maybe a dimension assertion (custom validator).
