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
  if (typeof window !== "undefined") {
    localStorage.setItem(KEY, JSON.stringify(p));
    window.dispatchEvent(new CustomEvent("progress-updated"));
  }
}

// Attempt-aware EXP: first-try correct is worth most; a 2nd-attempt save earns
// less; a miss still earns a small consolation so practice always feels rewarding.
export function expFor(correct: boolean, latencyMs: number, attemptNo: number): number {
  if (!correct) return 2;
  if (attemptNo >= 2) return 6;
  return latencyMs < 12000 ? 15 : 10;
}

// Pure reducer: returns a new Progress without persisting (the caller decides
// whether to save locally or to Supabase).
export function applyAnswer(
  prev: Progress, qid: string, concepts: string[], correct: boolean,
  latencyMs: number, attemptNo = 1
): { progress: Progress; gained: number } {
  const p: Progress = JSON.parse(JSON.stringify(prev));
  const srs = p.questions[qid] || initSrs();
  p.questions[qid] = reviewSrs(srs, qualityFromAnswer(correct, latencyMs));

  const target = correct ? (attemptNo >= 2 ? 0.6 : 1) : 0;
  for (const c of concepts) {
    const m = p.mastery[c] || { ability: 0, reps: 0 };
    m.ability = m.ability * 0.7 + target * 0.3;
    m.reps += 1;
    p.mastery[c] = m;
  }

  const gained = expFor(correct, latencyMs, attemptNo);
  p.points += gained;
  const d = today();
  if (p.lastDay !== d) {
    p.streak = p.lastDay ? p.streak + 1 : 1;
    p.lastDay = d;
  }
  return { progress: p, gained };
}

// Local-only convenience (guest mode).
export function recordAnswer(
  p: Progress, qid: string, concepts: string[], correct: boolean,
  latencyMs: number, attemptNo = 1
): Progress {
  const { progress } = applyAnswer(p, qid, concepts, correct, latencyMs, attemptNo);
  saveProgress(progress);
  return progress;
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
