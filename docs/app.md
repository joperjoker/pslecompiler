# Practice app

A Next.js (App Router) app in `web/`, deployable on Vercel, that serves the
question bank with gamified, spaced-repetition practice.

## Data flow
- Questions come from **Supabase** when `NEXT_PUBLIC_SUPABASE_*` are set
  (reads the `question_full` view), else from the **bundled seed**
  `web/data/questions.json` exported by `pslecompiler questions-demo`.
- Learner state (SRS schedule, concept mastery, points, streak) lives in
  `localStorage` (`web/lib/progress.ts`); the shape matches the Supabase
  `attempts` / `mastery` tables for later sync.

## Cognitive science
- **Spaced repetition:** SM-2 (`web/lib/srs.ts`) — wrong answers return tomorrow;
  correct answers stretch the interval by an ease factor; due items are served
  first (`dueOrder`).
- **Mastery:** an exponential moving average of correctness per concept, shown as
  bars on `/dashboard`.
- **Gamification:** points (faster-correct scores more) and daily streaks.

## Feedback
On answering, the chosen and correct options reveal their **rationale**; distractor
rationales are grounded in the misconception the option embodies — the engine's
per-option feedback surfaced directly to the learner.

## Supabase setup
Apply `supabase/migrations/0001_init.sql`, then load a bank with the engine's
`import.sql` (or the export step). Set the app's two env vars to the project URL
and anon key. See `docs/runbook.md`.

## Deploy
`web/` is the project root. Build verified with `next build` (4 static routes).
