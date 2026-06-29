"use client";

import { useState } from "react";
import { useGame } from "@/components/GameProvider";

export default function Login() {
  const { configured, user, login, register, logout } = useGame();
  const [mode, setMode] = useState<"in" | "up">("in");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  if (!configured) {
    return (
      <main>
        <div className="card float-in">
          <h1 className="pixel">Guest mode</h1>
          <p className="muted">
            Accounts need Supabase configured (set <code>NEXT_PUBLIC_SUPABASE_URL</code>
            and <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code>). For now your EXP saves on this
            device. <a href="/practice">Play as guest →</a>
          </p>
        </div>
      </main>
    );
  }

  if (user) {
    return (
      <main>
        <div className="card float-in">
          <h1 className="pixel">Logged in</h1>
          <p className="muted">{user.email} — your EXP, level and mastery sync to your account.</p>
          <div className="row">
            <a className="btn" href="/practice">▶ Continue quest</a>
            <button className="btn ghost" onClick={() => logout()}>Log out</button>
          </div>
        </div>
      </main>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setMsg("");
    try {
      if (mode === "in") await login(email, pw);
      else { await register(email, pw); }
    } catch (err: any) {
      setMsg(err?.message || "Something went wrong.");
    } finally { setBusy(false); }
  }

  return (
    <main>
      <div className="card float-in" style={{ maxWidth: 420, margin: "0 auto" }}>
        <h1 className="pixel">{mode === "in" ? "Log in" : "Create account"}</h1>
        <form onSubmit={submit}>
          <label className="muted" style={{ fontSize: 12 }}>Email</label>
          <input className="opt" type="email" required value={email}
                 onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          <label className="muted" style={{ fontSize: 12 }}>Password</label>
          <input className="opt" type="password" required minLength={6} value={pw}
                 onChange={(e) => setPw(e.target.value)} placeholder="at least 6 characters" />
          {msg && <p style={{ color: "var(--red)", fontSize: 13 }}>{msg}</p>}
          <button className="btn" type="submit" disabled={busy} style={{ marginTop: 6 }}>
            {busy ? "…" : mode === "in" ? "Log in ▶" : "Create account ▶"}
          </button>
        </form>
        <p className="muted" style={{ fontSize: 13, marginBottom: 0 }}>
          {mode === "in" ? "New here? " : "Already have an account? "}
          <button className="badge" onClick={() => setMode(mode === "in" ? "up" : "in")}>
            {mode === "in" ? "Create one" : "Log in"}
          </button>
        </p>
      </div>
    </main>
  );
}
