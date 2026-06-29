"use client";

import { levelFromPoints } from "@/lib/level";
import { useGame } from "@/components/GameProvider";

export default function Dashboard() {
  const { progress: prog, ready } = useGame();
  if (!ready) return <main><div className="card">Loading…</div></main>;

  const lv = levelFromPoints(prog.points);
  const concepts = Object.entries(prog.mastery).sort(
    (a, b) => b[1].ability - a[1].ability
  );

  return (
    <main>
      <div className="card wood float-in">
        <div className="row">
          <span className="nyan"><span className="trail" /><span className="cat">🐱</span></span>
          <div>
            <div className="pixel" style={{ fontSize: 16 }}>Lv {lv.level} · {lv.title}</div>
            <div className="muted" style={{ fontSize: 12 }}>{lv.intoLevel}/{lv.span} EXP to next level</div>
          </div>
          <span className="spacer" />
          <span className="badge">⭐ {prog.points}</span>
          <span className="badge">🔥 {prog.streak}</span>
        </div>
        <div className="bar" style={{ marginTop: 10 }}><span style={{ width: `${lv.pct}%` }} /></div>
      </div>

      <h2 className="pixel">Skill mastery</h2>
      {concepts.length === 0 && (
        <div className="card muted">No skills trained yet — go on a quest! 🗺️</div>
      )}
      {concepts.map(([c, m]) => (
        <div key={c} className="card float-in">
          <div className="row">
            <strong>{c}</strong>
            <span className="spacer" />
            <span className="muted" style={{ fontSize: 12 }}>
              {Math.round(m.ability * 100)}% · {m.reps} reps
            </span>
          </div>
          <div className="bar skill" style={{ marginTop: 8 }}>
            <span style={{ width: `${Math.round(m.ability * 100)}%` }} />
          </div>
        </div>
      ))}
    </main>
  );
}
