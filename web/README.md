# PSLE Practice app (Next.js)

Gamified, syllabus-anchored MCQ practice with per-option feedback and spaced
repetition.

- **Questions:** served from Supabase when `NEXT_PUBLIC_SUPABASE_*` are set,
  otherwise from the bundled seed `data/questions.json` (exported by the engine:
  `pslecompiler questions-demo`). Re-seed by copying a fresh
  `data/questions/<bank>/questions.json` over `web/data/questions.json`.
- **Progress:** spaced repetition (SM-2, `lib/srs.ts`), concept mastery, points
  and streaks — stored in `localStorage` (`lib/progress.ts`); the same shape maps
  to the Supabase `attempts` / `mastery` tables.

## Run
```bash
cd web
npm install
npm run dev      # http://localhost:3000
```

## Deploy (Vercel)
Push the repo and import `web/` as the project root, or use the Vercel
integration. Set the two `NEXT_PUBLIC_SUPABASE_*` env vars to serve from
Supabase; leave them unset to demo on the seed.

## Pages
- `/` — home: points, streak, subjects.
- `/practice` — answer questions, see why each option is right/wrong, earn points.
- `/dashboard` — concept mastery bars, points, streak.
