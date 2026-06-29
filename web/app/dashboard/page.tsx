"use client";

import { useEffect, useState } from "react";
import { Progress, loadProgress } from "@/lib/progress";

export default function Dashboard() {
  const [prog, setProg] = useState<Progress | null>(null);
  useEffect(() => setProg(loadProgress()), []);
  if (!prog) return <main><p className="muted">Loading…</p></main>;

  const concepts = Object.entries(prog.mastery).sort(
    (a, b) => b[1].ability - a[1].ability
  );

  return (
    <main>
      <h1>Your progress</h1>
      <div className="card row">
        <div><div className="stat">{prog.points}</div><div className="muted">points</div></div>
        <div><div className="stat">🔥 {prog.streak}</div><div className="muted">day streak</div></div>
        <div><div className="stat">{concepts.length}</div><div className="muted">concepts seen</div></div>
      </div>

      <h2>Concept mastery</h2>
      {concepts.length === 0 && <p className="muted">Answer some questions to build mastery.</p>}
      {concepts.map(([c, m]) => (
        <div key={c} className="card">
          <div className="row">
            <strong>{c}</strong>
            <span className="spacer" />
            <span className="muted">{Math.round(m.ability * 100)}% · {m.reps} reps</span>
          </div>
          <div className="bar" style={{ marginTop: 8 }}>
            <span style={{ width: `${Math.round(m.ability * 100)}%` }} />
          </div>
        </div>
      ))}
    </main>
  );
}
