"use client";

import { useEffect, useMemo, useState } from "react";
import { loadQuestions } from "@/lib/bank";
import { Question } from "@/lib/types";
import { Progress, loadProgress, recordAnswer, dueOrder } from "@/lib/progress";
import { levelFromPoints } from "@/lib/level";

export default function Practice() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [idx, setIdx] = useState(0);
  const [chosen, setChosen] = useState<string | null>(null);
  const [shownAt, setShownAt] = useState<number>(Date.now());
  const [gain, setGain] = useState<number>(0);
  const [levelUp, setLevelUp] = useState<number | null>(null);

  useEffect(() => {
    const subject =
      new URLSearchParams(window.location.search).get("subject") || undefined;
    loadQuestions(subject).then((qs) =>
      setQuestions(dueOrder(loadProgress(), qs))
    );
    setShownAt(Date.now());
  }, []);

  const q = questions[idx];
  const answered = chosen !== null;
  const correctLabel = useMemo(
    () => q?.options.find((o) => o.is_correct)?.label,
    [q]
  );

  if (!q) return <main><div className="card">Loading quest…</div></main>;

  function choose(label: string) {
    if (answered) return;
    const before = loadProgress();
    const beforeLv = levelFromPoints(before.points).level;
    const correct = label === correctLabel;
    setChosen(label);
    const after: Progress = recordAnswer(
      before, q.qid, q.concepts || [], correct, Date.now() - shownAt
    );
    setGain(after.points - before.points);
    const afterLv = levelFromPoints(after.points).level;
    if (afterLv > beforeLv) {
      setLevelUp(afterLv);
      setTimeout(() => setLevelUp(null), 2200);
    }
  }

  function next() {
    setChosen(null);
    setGain(0);
    setShownAt(Date.now());
    setIdx((i) => (i + 1) % questions.length);
  }

  const correct = chosen === correctLabel;

  return (
    <main>
      {levelUp !== null && (
        <div className="toast">🎉 LEVEL UP! → Lv {levelUp} ✨</div>
      )}

      <div className="row" style={{ marginTop: 12 }}>
        <span className="badge">{q.subject}</span>
        {q.theme && <span className="badge">🗺️ {q.theme}</span>}
        {q.difficulty_band && <span className="badge">⚔️ {q.difficulty_band}</span>}
        {q.cognitive_level && <span className="badge">🧠 {q.cognitive_level}</span>}
        {q.provenance === "variant" && <span className="badge">🔁 variant</span>}
        <span className="spacer" />
        <span className="badge">Q {idx + 1}/{questions.length}</span>
      </div>

      <div className="card float-in" key={q.qid}>
        <h2>{q.stem}</h2>
        {q.options.map((o) => {
          let cls = "opt";
          if (answered && o.label === correctLabel) cls += " correct";
          else if (answered && o.label === chosen) cls += " wrong";
          return (
            <button key={o.label} className={cls} onClick={() => choose(o.label)}>
              <span><strong>({o.label})</strong> {o.text}</span>
              {answered && (o.label === correctLabel || o.label === chosen) && (
                <span className="why">
                  {o.label === correctLabel ? "✅ " : "❌ "}{o.rationale}
                  {o.misconception && o.label !== correctLabel && (
                    <em> — common trap: {o.misconception}</em>
                  )}
                </span>
              )}
            </button>
          );
        })}

        {answered && (
          <div className="row" style={{ marginTop: 12 }}>
            <span className="pixel" style={{ color: correct ? "var(--green)" : "var(--red)" }}>
              {correct ? "VICTORY!" : "OUCH!"}
            </span>
            {gain > 0 && <span className="badge">+{gain} EXP ⭐</span>}
            <span className="muted" style={{ fontSize: 12 }}>
              {(q.concepts || []).join(" · ") || "—"}
            </span>
            <span className="spacer" />
            <button className="btn" onClick={next}>Next ▶</button>
          </div>
        )}
      </div>
    </main>
  );
}
