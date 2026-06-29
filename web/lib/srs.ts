// Minimal SM-2 spaced-repetition scheduler.
// quality: 0..5 (we map correct->5/4, wrong->2). Returns next interval (days),
// updated ease and reps.

export type SrsState = { reps: number; ease: number; intervalD: number; dueAt: number };

export function initSrs(): SrsState {
  return { reps: 0, ease: 2.5, intervalD: 0, dueAt: Date.now() };
}

export function reviewSrs(s: SrsState, quality: number): SrsState {
  let { reps, ease, intervalD } = s;
  ease = Math.max(1.3, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)));
  if (quality < 3) {
    reps = 0;
    intervalD = 1; // see again tomorrow
  } else {
    reps += 1;
    if (reps === 1) intervalD = 1;
    else if (reps === 2) intervalD = 6;
    else intervalD = Math.round(intervalD * ease);
  }
  const dueAt = Date.now() + intervalD * 24 * 60 * 60 * 1000;
  return { reps, ease, intervalD, dueAt };
}

export function qualityFromAnswer(correct: boolean, latencyMs: number): number {
  if (!correct) return 2;
  return latencyMs < 12000 ? 5 : 4; // fast & correct scores higher
}
