"use client";

import { useEffect, useMemo, useState } from "react";
import { loadQuestions } from "@/lib/bank";
import { Question } from "@/lib/types";
import { loadProgress, dueOrder } from "@/lib/progress";
import { levelFromPoints } from "@/lib/level";
import { useGame } from "@/components/GameProvider";
import QuestionBlocks from "@/components/QuestionBlocks";

export default function Practice() {
  const { progress, answer } = useGame();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [idx, setIdx] = useState(0);
  const [shownAt, setShownAt] = useState<number>(Date.now());
  // attempt state
  const [picks, setPicks] = useState<string[]>([]);   // labels tried, in order
  const [revealed, setRevealed] = useState(false);    // show full feedback?
  const [gain, setGain] = useState(0);
  const [levelUp, setLevelUp] = useState<number | null>(null);

  useEffect(() => {
    const subject = new URLSearchParams(window.location.search).get("subject") || undefined;
    loadQuestions(subject).then((qs) => setQuestions(dueOrder(loadProgress(), qs)));
    reset();
  }, []);

  const q = questions[idx];
  const correctLabel = useMemo(() => q?.options.find((o) => o.is_correct)?.label, [q]);

  if (!q) return <main><div className="card">Loading quest…</div></main>;

  function reset() {
    setPicks([]); setRevealed(false); setGain(0); setShownAt(Date.now());
  }

  function choose(label: string) {
    if (revealed || picks.includes(label)) return;
    const attemptNo = picks.length + 1;
    const correct = label === correctLabel;
    const nextPicks = [...picks, label];
    setPicks(nextPicks);

    // First wrong attempt with a hint available -> let them try once more.
    const allowRetry = !correct && attemptNo === 1 && !!q.hint;
    if (allowRetry) return;

    // Otherwise score this attempt and reveal full feedback.
    const beforeLv = levelFromPoints(progress.points).level;
    const g = answer({
      qid: q.qid, concepts: q.concepts || [], correct,
      latencyMs: Date.now() - shownAt, attemptNo,
    });
    setGain(g); setRevealed(true);
    const afterLv = levelFromPoints(progress.points + g).level;
    if (afterLv > beforeLv) { setLevelUp(afterLv); setTimeout(() => setLevelUp(null), 2200); }
  }

  function next() { setIdx((i) => (i + 1) % questions.length); reset(); }

  const firstMiss = picks.length === 1 && picks[0] !== correctLabel && !revealed;
  const finalCorrect = revealed && picks[picks.length - 1] === correctLabel;

  return (
    <main>
      {levelUp !== null && <div className="toast">🎉 LEVEL UP! → Lv {levelUp} ✨</div>}

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
        <QuestionBlocks q={q} />

        {q.options.map((o) => {
          const tried = picks.includes(o.label);
          let cls = "opt";
          if (revealed && o.label === correctLabel) cls += " correct";
          else if ((revealed || tried) && o.label !== correctLabel && tried) cls += " wrong";
          return (
            <button key={o.label} className={cls} onClick={() => choose(o.label)}
                    disabled={revealed || (tried && !revealed)}>
              <span><strong>({o.label})</strong> {o.text}</span>
              {o.image && <img src={o.image} alt="" style={{ display: "block", maxHeight: 90, marginTop: 8 }} />}
              {revealed && (o.label === correctLabel || tried) && (
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

        {firstMiss && (
          <div className="card" style={{ background: "#fff7e6", marginTop: 10 }}>
            <strong className="pixel" style={{ fontSize: 12 }}>Not quite — try again! </strong>
            <span className="muted">💡 {q.hint}</span>
          </div>
        )}

        {revealed && (
          <div className="row" style={{ marginTop: 12 }}>
            <span className="pixel" style={{ color: finalCorrect ? "var(--green)" : "var(--red)" }}>
              {finalCorrect ? (picks.length > 1 ? "RECOVERED!" : "VICTORY!") : "OUCH!"}
            </span>
            {gain > 0 && <span className="badge">+{gain} EXP ⭐</span>}
            <span className="muted" style={{ fontSize: 12 }}>{(q.concepts || []).join(" · ")}</span>
            <span className="spacer" />
            <button className="btn" onClick={next}>Next ▶</button>
          </div>
        )}
      </div>
    </main>
  );
}
