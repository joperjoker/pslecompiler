# PROGRESS / CONTINUITY — read this first next session

> Living handoff note. Update it at the end of each working session.
> Last updated: 2026-06-29. Branch: `claude/project-system-prompt-aaz36i`.

## One-line state
The MCQ **question bank is the product**; syllabus graph is the neurosymbolic
backbone. Engine + a cute Next.js practice app are built and pushed. Waiting on
the user's **past-year paper PDFs** to populate real questions.

## Done (committed & pushed)
- **Syllabus backbone (Phase A):** Science 2023 ingested from the real MOE PDF —
  5 themes, 25 topics, **68 learning outcomes** (cited) + a 7-outcome enrichment
  (concepts/misconceptions/distractors + communities). Table-aware parser:
  `src/pslecompiler/science2023.py`.
- **Question engine:** `qmodel.py`, `qpipeline.py`, `paper_parse.py`, `tag.py`
  (reuses `retrieve.py`), `qa_questions.py`, `export_questions.py`, `sample.py`.
  CLI: `ingest-paper`, `questions-demo`, `questions-qa`. Prompts in `prompts/`.
  Proven on a synthetic sample paper (3 Qs, **0 QA errors**).
- **App (`web/`):** Next.js (build-verified, 4 routes). Cozy pixel-RPG + Nyan Cat
  theme, **pure CSS + emoji, no image/font assets**. Town/Quest/Stats pages,
  live HUD (Lv/EXP/coins/streak), SM-2 spaced repetition (`web/lib/srs.ts`),
  leveling (`web/lib/level.ts`). Serves from Supabase if env set, else the
  bundled seed `web/data/questions.json`.
- **Stores:** Neo4j = authoring graph (portable artifacts in `data/artifacts/`
  since cloud/egress blocked here); Supabase = serving + learner data
  (`supabase/migrations/0001_init.sql`).
- **Tests:** 16 passing (`pytest -q`).

## Environment gotchas (this sandbox)
- Egress blocks `moe.gov.sg`, `huggingface.co`, Neo4j cloud — only pip/npm + Anthropic.
- So: embeddings are optional/pluggable; DB ships as artifacts; PDFs are committed
  (not downloaded). Neo4j live load uses the **HTTP Query API**, not Bolt.
- Playwright: use `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` via
  `playwright-core` (already a web devDep) for screenshots.

## Blocked on the user
1. **Past-year paper PDFs** → drop in `data/papers/` (see its README), then
   `pslecompiler ingest-paper --paper <file>` and author tagging+answer/feedback.
2. Go-ahead to **provision Supabase + deploy Vercel** (via MCP integrations).
3. Optional: **Neo4j AuraDB** creds for the live graph.

## Next actions (pick up here) — user leaning undecided between #2 and #3
1. **Harden paper ingestion** against a *realistic mock* PSLE paper PDF
   (multi-column, figures, answer-key page) + agent fallback. (My recommendation.)
2. **Stand up Supabase + deploy to Vercel** for a clickable live demo.
3. Polish app UX: session-summary screen, combo/daily-goal juice, cute /not-found.
4. Expand backbone: Math 2021 / English 2020 / Chinese 2015&2024 parsers.

## How to run (quick)
```bash
# engine
uv venv && source .venv/bin/activate && uv pip install -e '.[dev]'
pytest -q
PYTHONPATH=src python -m pslecompiler.cli questions-demo --stem science-primary-2023
# app
cd web && npm install && npm run dev   # http://localhost:3000
```

## Key docs
`docs/question-pipeline.md` (product flow), `docs/app.md`, `docs/architecture.md`,
`docs/data-model.md`, `docs/ingestion-algorithm.md`, `docs/retrieval-algorithm.md`,
`docs/runbook.md` (AuraDB/Supabase). Persona/context: `CLAUDE.md`.
