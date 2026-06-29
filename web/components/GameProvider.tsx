"use client";

import {
  createContext, useCallback, useContext, useEffect, useState,
} from "react";
import {
  Progress, loadProgress, saveProgress, applyAnswer,
} from "@/lib/progress";
import { getSupabase } from "@/lib/supabase";
import { AuthUser, currentUser, signIn, signOut, signUp } from "@/lib/auth";
import { loadRemoteProgress, persistRemote } from "@/lib/remote";

type Ctx = {
  ready: boolean;
  user: AuthUser | null;
  configured: boolean;       // is Supabase wired?
  progress: Progress;
  answer: (a: { qid: string; concepts: string[]; correct: boolean;
    latencyMs: number; attemptNo: number }) => number; // returns EXP gained
  login: (e: string, p: string) => Promise<void>;
  register: (e: string, p: string) => Promise<void>;
  logout: () => Promise<void>;
};

const GameContext = createContext<Ctx | null>(null);

export function GameProvider({ children }: { children: React.ReactNode }) {
  const configured = !!getSupabase();
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [progress, setProgress] = useState<Progress>(() => loadProgress());

  const refresh = useCallback(async () => {
    const u = await currentUser();
    setUser(u);
    const merged = await loadRemoteProgress(loadProgress());
    setProgress(merged);
    saveProgress(merged);
    setReady(true);
  }, []);

  useEffect(() => {
    refresh();
    const sb = getSupabase();
    if (!sb) return;
    const { data } = sb.auth.onAuthStateChange(() => refresh());
    return () => data.subscription.unsubscribe();
  }, [refresh]);

  const answer: Ctx["answer"] = (a) => {
    const { progress: np, gained } = applyAnswer(
      progress, a.qid, a.concepts, a.correct, a.latencyMs, a.attemptNo
    );
    setProgress(np);
    saveProgress(np);                       // local mirror (keeps SRS schedule)
    if (user) void persistRemote(np, { chosen: "", ...a });  // cloud sync
    return gained;
  };

  const login = async (e: string, p: string) => { await signIn(e, p); await refresh(); };
  const register = async (e: string, p: string) => { await signUp(e, p); await signIn(e, p); await refresh(); };
  const logout = async () => { await signOut(); await refresh(); };

  return (
    <GameContext.Provider
      value={{ ready, user, configured, progress, answer, login, register, logout }}>
      {children}
    </GameContext.Provider>
  );
}

export function useGame(): Ctx {
  const c = useContext(GameContext);
  if (!c) throw new Error("useGame must be used within GameProvider");
  return c;
}
