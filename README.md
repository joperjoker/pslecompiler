# PSLE Question Compiler — Syllabus "Second Brain"

A knowledge base that ingests the Singapore MOE primary syllabi (English,
Mathematics, Science, Chinese — Standard level) and breaks them into
**MCQ-ready atoms** for building a gamified, cognitive-science-anchored question
bank for PSLE students.

It is a **graph-native second brain** with three layers:

1. **Structured spine** — `Subject → SyllabusVersion → Theme → Topic →
   LearningOutcome`, versioned by syllabus year (all versions coexist).
2. **Wiki synthesis layer** — citation-grounded articles per topic/concept.
3. **GraphRAG layer** — a graph of `Concept / Misconception / Distractor`
   (the engine for *grounded* MCQ distractors) plus community summaries.

Target store: **Neo4j** (property graph + vector index + wiki/community nodes).
Because Neo4j cloud, the embedding-model host, and `moe.gov.sg` are blocked by
this environment's egress policy, the pipeline emits **portable load artifacts**
(`nodes.jsonl`, `edges.jsonl`, `load.cypher`) that you apply to your own AuraDB,
and embeddings are an **optional, pluggable** layer.

## Status

- ✅ Vertical slice: **Science 2023** fully ingested from the real MOE PDF —
  5 themes, 25 topics, **68 learning outcomes** with primary levels and
  citations. A 7-outcome semantic enrichment demonstrates the
  concept/misconception/distractor + community layers end to end.
- ⏳ Phase B: replicate to Mathematics 2021, English 2020, Chinese 2015/2024.

## Quickstart

```bash
uv venv && source .venv/bin/activate
uv pip install -e .            # core; add '.[embeddings]' when network allows

# 1. Ingest a syllabus PDF -> spine + artifacts + extraction TODO
pslecompiler ingest --source science-primary-2023.pdf --no-embed

# 2. (agent) author extractions for the TODO outcomes, then merge them
pslecompiler enrich --stem science-primary-2023 \
    --extractions data/extracted/science-primary-2023.extractions.jsonl --no-embed

# 3. Retrieve MCQ question-spec bundles (grounded distractors included)
pslecompiler retrieve --stem science-primary-2023 --subject Science \
    --version 2023 --query "changes of state" --count 3

# 4. (optional, when network allows) load into your Neo4j AuraDB
pslecompiler load --stem science-primary-2023
```

## Layout

```
src/pslecompiler/   pipeline + algorithms (see docs/architecture.md)
schema/             constraints.cypher (Neo4j constraints + vector indexes)
prompts/            agent prompts for extraction / wiki / community synthesis
data/sources/       MOE syllabus PDFs (committed; see its README for filenames)
data/extracted/     extraction TODO + extraction records (JSONL)
data/artifacts/     portable load files per source (nodes/edges/load.cypher)
docs/               architecture, data model, ingestion + retrieval algorithms,
                    and the AuraDB runbook
tests/              pytest suite (runs without Neo4j or network)
```

See `docs/` for the full design and `docs/runbook.md` to stand up your AuraDB.
