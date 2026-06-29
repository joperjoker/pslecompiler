# PSLE Question Compiler

**The MCQ question bank is the product.** A neurosymbolic system that builds a
gamified, cognitive-science-anchored PSLE question bank: it **ingests past-year
papers** into MCQ items, **generates verified answers + per-option feedback**, and
**tags every question to the MOE syllabus** — served through a Next.js practice app
with spaced repetition.

- **Neural** = the LLM (this agent) parsing items, verifying answers, writing
  per-option rationales, tagging, and generating variants.
- **Symbolic** = the MOE syllabus knowledge graph + hard validators + retrieval,
  which constrain and check everything the neural side proposes.

## The two halves

**1. Question bank (product)** — `Paper → Question → Option`, each question tagged
`ASSESSES`→LearningOutcome / `TESTS`→Concept, with distractor options linked to the
`Misconception` they embody. Built from uploaded past papers (`data/papers/`) plus
controlled variants. Feedback = per-option rationale (why right / why wrong).
See `docs/question-pipeline.md` and `web/` (the app).

**2. Syllabus backbone (scaffolding)** — a Neo4j graph with three layers:
structured spine (`Subject→Theme→Topic→LearningOutcome`), wiki synthesis, and a
GraphRAG layer (`Concept/Misconception/Distractor` + communities). The store is
**Neo4j**; because Neo4j cloud / the embedding host / `moe.gov.sg` are blocked by
this environment's egress policy, the pipeline emits **portable load artifacts**
(`nodes.jsonl`, `edges.jsonl`, `load.cypher`) and embeddings are **optional**.

## Status

- ✅ **Syllabus backbone:** Science 2023 fully ingested from the real MOE PDF —
  5 themes, 25 topics, **68 learning outcomes** (cited), with a 7-outcome
  enrichment (concepts/misconceptions/distractors + communities).
- ✅ **Question engine:** paper parser, neurosymbolic tagging, answer+feedback,
  variants, QA validators, export — proven on a worked sample paper (3 questions,
  0 QA errors).
- ✅ **App:** Next.js practice app (build-verified) — practice + per-option
  feedback + spaced repetition + mastery dashboard; Vercel + Supabase ready.
- ⏳ **Next:** ingest your real past papers; replicate the backbone to
  Mathematics 2021, English 2020, Chinese 2015/2024.

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
