// Supabase persistence for gamification (points/streak/mastery + attempts).
// SRS per-question schedule stays device-local (localStorage); EXP/level/mastery
// persist to the account so progress follows the student across devices.
import { getSupabase } from "./supabase";
import { Progress } from "./progress";

export async function loadRemoteProgress(local: Progress): Promise<Progress> {
  const sb = getSupabase();
  if (!sb) return local;
  const { data: u } = await sb.auth.getUser();
  if (!u.user) return local;

  const merged: Progress = { ...local, mastery: { ...local.mastery } };
  const { data: prof } = await sb.from("profiles").select("*").eq("id", u.user.id).single();
  if (prof) {
    merged.points = prof.points ?? 0;
    merged.streak = prof.streak ?? 0;
    merged.lastDay = prof.last_day ?? "";
  }
  const { data: rows } = await sb.from("mastery").select("*").eq("user_id", u.user.id);
  for (const r of rows ?? []) {
    merged.mastery[r.concept] = { ability: r.ability ?? 0, reps: r.reps ?? 0 };
  }
  return merged;
}

export async function persistRemote(
  p: Progress, attempt: { qid: string; chosen: string; correct: boolean;
    latencyMs: number; attemptNo: number; concepts: string[] }
): Promise<void> {
  const sb = getSupabase();
  if (!sb) return;
  const { data: u } = await sb.auth.getUser();
  if (!u.user) return;
  const uid = u.user.id;

  await sb.from("profiles").upsert(
    { id: uid, points: p.points, streak: p.streak, last_day: p.lastDay || null,
      updated_at: new Date().toISOString() },
    { onConflict: "id" }
  );
  await sb.from("attempts").insert({
    user_id: uid, qid: attempt.qid, chosen: attempt.chosen,
    is_correct: attempt.correct, latency_ms: attempt.latencyMs,
    attempt_no: attempt.attemptNo,
  });
  const rows = attempt.concepts.map((c) => ({
    user_id: uid, concept: c,
    ability: p.mastery[c]?.ability ?? 0, reps: p.mastery[c]?.reps ?? 0,
    updated_at: new Date().toISOString(),
  }));
  if (rows.length) await sb.from("mastery").upsert(rows, { onConflict: "user_id,concept" });
}
