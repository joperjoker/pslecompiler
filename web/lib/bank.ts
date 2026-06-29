import { Question } from "./types";
import seed from "@/data/questions.json";
import { getSupabase } from "./supabase";

// Load the question bank. Prefers Supabase when configured; otherwise serves the
// bundled seed exported from the engine (data/questions/sample/questions.json).
export async function loadQuestions(subject?: string): Promise<Question[]> {
  const sb = getSupabase();
  if (sb) {
    let q = sb.from("question_full").select("*");
    if (subject) q = q.eq("subject", subject);
    const { data, error } = await q;
    if (!error && data) return data as unknown as Question[];
  }
  const all = seed as unknown as Question[];
  return subject ? all.filter((q) => q.subject === subject) : all;
}

export function subjectsOf(qs: Question[]): string[] {
  return Array.from(new Set(qs.map((q) => q.subject))).sort();
}
