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
- **App (`web/`):** Next.js (build-verified, 5 routes). Cozy pixel-RPG + Nyan Cat
  theme, **pure CSS + emoji, no image/font assets**. Town/Quest/Stats/Login pages,
  live HUD (Lv/EXP/coins/streak), SM-2 spaced repetition (`web/lib/srs.ts`),
  leveling (`web/lib/level.ts`). Serves from Supabase if env set, else the
  bundled seed `web/data/questions.json`.
- **Auth + persistence:** email+password via Supabase Auth (`web/lib/auth.ts`,
  `GameProvider.tsx`, `/login`). EXP/level/streak/mastery persist to the account
  (`profiles`/`attempts`/`mastery`, migration `0002`); **guest mode** (localStorage)
  is the fallback when Supabase env isn't set. SRS schedule stays device-local.
- **Rich question format:** stem `Block`s (text/image/table), per-option image,
  `hint`, and a **2nd-attempt flow** (first miss → hint + retry, then full
  per-option feedback; attempt-aware EXP). Table question in the sample.
- **Hardened paper parser:** page render to PNG, embedded-image extraction,
  table detection, and a `needs_vision` flag for full-page/image-only items
  (`paper_parse.py`); validated on a generated mock PDF.
- **Tests:** 19 passing.
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

## Next actions (pick up here)
1. **Provision Supabase + deploy to Vercel** (user chose "build ready, provision
   later"). Apply `supabase/migrations/0001`+`0002`, set `NEXT_PUBLIC_SUPABASE_*`,
   load a bank via `export_questions` import.sql, deploy `web/` to Vercel.
2. **Agent vision pass** for `needs_vision` items: render full-page/image-only
   questions → agent transcribes stem+options+figure → RawItem. Wire into
   `ingest-paper`.
3. **Real papers:** once uploaded to `data/papers/`, run ingest → tag →
   answer/feedback → variants → QA → export → reseed `web/data/questions.json`.
4. Polish app UX: session-summary screen, combo/daily-goal juice, cute /not-found.
5. Expand backbone: Math 2021 / English 2020 / Chinese 2015&2024 parsers.

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
