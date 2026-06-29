import { getSupabase } from "./supabase";

export type AuthUser = { id: string; email: string };

export async function signUp(email: string, password: string) {
  const sb = getSupabase();
  if (!sb) throw new Error("Accounts need Supabase configured (guest mode only).");
  const { error } = await sb.auth.signUp({ email, password });
  if (error) throw error;
}

export async function signIn(email: string, password: string) {
  const sb = getSupabase();
  if (!sb) throw new Error("Accounts need Supabase configured (guest mode only).");
  const { error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function signOut() {
  const sb = getSupabase();
  if (sb) await sb.auth.signOut();
}

export async function currentUser(): Promise<AuthUser | null> {
  const sb = getSupabase();
  if (!sb) return null;
  const { data } = await sb.auth.getUser();
  return data.user ? { id: data.user.id, email: data.user.email ?? "" } : null;
}
