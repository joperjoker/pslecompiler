"use client";

import { useGame } from "./GameProvider";

export default function TopBar() {
  const { user, configured, logout } = useGame();
  return (
    <div className="row" style={{ marginBottom: 10 }}>
      <a href="/" className="pixel" style={{ fontSize: 16 }}>🍄&nbsp;PSLE&nbsp;Quest</a>
      <span className="spacer" />
      <a href="/" className="badge">Town</a>
      <a href="/practice" className="badge">Quest</a>
      <a href="/dashboard" className="badge">Stats</a>
      {!configured && <span className="badge" title="Supabase not configured">👤 guest</span>}
      {configured && (user
        ? <button className="badge" onClick={() => logout()} title={user.email}>Log out</button>
        : <a href="/login" className="badge">Log in</a>)}
    </div>
  );
}
