# Ingestion algorithm

## Stages
1. **Acquire** — committed PDFs in `data/sources/` (egress to MOE is blocked).
2. **Parse** (`parse_pdf.py`) — PDF → ordered `Section`s. Heading levels are
   inferred from relative font size; the helper `sections_from_blocks` is pure
   (no PyMuPDF) so it is unit-testable.
3. **Structure** — build the spine. Two mapper families:
   - *Heading-driven* (`structure.py::map_generic`) for prose-structured PDFs.
   - *Table-aware* (`science2023.py`) for the Science 2023 PDF, whose outcomes
     live in four-column tables. See note below.
4. **Semantic extraction (agent)** — `extract/` writes a TODO of every
   `LearningOutcome`; the agent (Claude Code, under the user's subscription —
   no external key) produces one `Extraction` record per outcome using
   `prompts/extract_lo.md`. `apply_extractions` merges them, creating the
   `Concept / Misconception / Distractor` subgraph and tagging cognitive level
   + difficulty.
5. **Embed (optional)** — `embed.py` attaches multilingual vectors when the
   model is available; otherwise skipped.
6. **Community detection** — `community.py` runs NetworkX greedy-modularity over
   the concept subgraph (AuraDB Free has no GDS) and adds `Community` nodes;
   summaries are written by the agent (`prompts/community_summary.md`).
7. **Wiki synthesis (agent)** — per topic/concept, a cited article
   (`prompts/wiki_synthesis.md`) → `WikiArticle` nodes.
8. **Emit artifacts** — `graph_artifacts.py` writes `nodes.jsonl`,
   `edges.jsonl`, idempotent `load.cypher`, and `manifest.json`.
9. **QA** — counts vs the source; spot-check outcomes against the PDF; dedupe.

## The Science 2023 table-aware parser
The official PDF (Section 5, pp. 36–80) is the hard case. Reverse-engineered:
- Themes are introduced by **"About \<Theme\>:"** pages (no outcomes there).
- Each topic table title is a **bold** line containing a level marker
  `(P3)`–`(P6)`; it is centred (x varies) and repeats atop every page the table
  spans, so topics are deduped by uid.
- Columns are *Learning Outcomes | Core Ideas | Practices | Values*. Column
  boundaries drift per page, but the **Learning Outcomes column is reliably the
  leftmost** (content `x0 < ~200`). Bullet markers (`•`) and their text sit on
  separate lines, so a lone bullet *opens* a new outcome and following
  left-column lines append to it.
- Result on the real PDF: 5 themes, 25 topics, 68 outcomes with primary levels
  and page citations. Core Ideas / Practices are kept as topic context.

New subjects: add a `SourceDoc` in `sources.py`. Use `map_generic` first; if the
PDF is table-based, add a dedicated parser like `science2023.py` and register it
in `cli.PDF_MAPPERS`.
