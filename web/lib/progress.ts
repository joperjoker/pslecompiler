// Client-side progress: per-question SRS schedule, per-concept mastery, and
// gamification (points, streak). Persisted in localStorage so the app is fully
// usable without a backend; the same shape syncs to Supabase when configured.
"use client";

import { SrsState, initSrs, reviewSrs, qualityFromAnswer } from "./srs";

const KEY = "psle-progress-v1";

export type Progress = {
  questions: Record<string, SrsState>;
  mastery: Record<string, { ability: number; reps: number }>;
  points: number;
  streak: number;
  lastDay: string;
};

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function loadProgress(): Progress {
  if (typeof window === "undefined")
    return { questions: {}, mastery: {}, points: 0, streak: 0, lastDay: "" };
  try {
    return JSON.parse(localStorage.getItem(KEY) || "") as Progress;
  } catch {
    return { questions: {}, mastery: {}, points: 0, streak: 0, lastDay: "" };
  }
}

export function saveProgress(p: Progress) {
  if (typeof window !== "undefined") localStorage.setItem(KEY, JSON.stringify(p));
}

export function recordAnswer(
  p: Progress, qid: string, concepts: string[], correct: boolean, latencyMs: number
): Progress {
  const srs = p.questions[qid] || initSrs();
  const q = qualityFromAnswer(correct, latencyMs);
  p.questions[qid] = reviewSrs(srs, q);

  for (const c of concepts) {
    const m = p.mastery[c] || { ability: 0, reps: 0 };
    // exponential moving average of correctness
    m.ability = m.ability * 0.7 + (correct ? 1 : 0) * 0.3;
    m.reps += 1;
    p.mastery[c] = m;
  }

  // gamification
  p.points += correct ? (latencyMs < 12000 ? 15 : 10) : 2;
  const d = today();
  if (p.lastDay !== d) {
    p.streak = p.lastDay ? p.streak + 1 : 1;
    p.lastDay = d;
  }
  saveProgress(p);
  return { ...p };
}

// Order questions: due ones first (smallest dueAt), unseen next, future last.
export function dueOrder<T extends { qid: string }>(p: Progress, qs: T[]): T[] {
  const now = Date.now();
  return [...qs].sort((a, b) => {
    const da = p.questions[a.qid]?.dueAt ?? 0;
    const db = p.questions[b.qid]?.dueAt ?? 0;
    const aDue = da <= now ? 0 : 1;
    const bDue = db <= now ? 0 : 1;
    if (aDue !== bDue) return aDue - bDue;
    return da - db;
  });
}
