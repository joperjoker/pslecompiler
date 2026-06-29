"use client";

import { useEffect, useMemo, useState } from "react";
import { loadQuestions } from "@/lib/bank";
import { Question } from "@/lib/types";
import {
  Progress, loadProgress, recordAnswer, dueOrder,
} from "@/lib/progress";

export default function Practice() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [prog, setProg] = useState<Progress>(() => loadProgress());
  const [idx, setIdx] = useState(0);
  const [chosen, setChosen] = useState<string | null>(null);
  const [shownAt, setShownAt] = useState<number>(Date.now());

  useEffect(() => {
    const subject =
      new URLSearchParams(window.location.search).get("subject") || undefined;
    loadQuestions(subject).then((qs) => {
      const p = loadProgress();
      setProg(p);
      setQuestions(dueOrder(p, qs));
      setShownAt(Date.now());
    });
  }, []);

  const q = questions[idx];
  const answered = chosen !== null;
  const correctLabel = useMemo(
    () => q?.options.find((o) => o.is_correct)?.label,
    [q]
  );

  if (!q) return <main><p className="muted">Loading questions…</p></main>;

  function choose(label: string) {
    if (answered) return;
    const correct = label === correctLabel;
    const latency = Date.now() - shownAt;
    setChosen(label);
    setProg(recordAnswer(loadProgress(), q.qid, q.concepts || [], correct, latency));
  }

  function next() {
    setChosen(null);
    setShownAt(Date.now());
    setIdx((i) => (i + 1) % questions.length);
  }

  return (
    <main>
      <div className="row">
        <span className="badge">{q.subject}</span>
        {q.theme && <span className="badge">{q.theme}</span>}
        {q.difficulty_band && <span className="badge">{q.difficulty_band}</span>}
        {q.cognitive_level && <span className="badge">{q.cognitive_level}</span>}
        {q.provenance === "variant" && <span className="badge">variant</span>}
        <span className="spacer" />
        <span className="badge">🔥 {prog.streak} · {prog.points} pts</span>
      </div>

      <div className="card">
        <h2>{q.stem}</h2>
        {q.options.map((o) => {
          let cls = "opt";
          if (answered && o.label === correctLabel) cls += " correct";
          else if (answered && o.label === chosen) cls += " wrong";
          return (
            <button key={o.label} className={cls} onClick={() => choose(o.label)}>
              <span>({o.label}) {o.text}</span>
              {answered && (o.label === correctLabel || o.label === chosen) && (
                <span className="why">{o.rationale}</span>
              )}
            </button>
          );
        })}

        {answered && (
          <div className="row" style={{ marginTop: 12 }}>
            <span className="muted">
              {chosen === correctLabel ? "✅ Correct" : "❌ Not quite"} ·
              concepts: {(q.concepts || []).join(", ") || "—"}
            </span>
            <span className="spacer" />
            <button className="btn" onClick={next}>Next →</button>
          </div>
        )}
      </div>
    </main>
  );
}
