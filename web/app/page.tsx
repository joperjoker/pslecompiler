"use client";

import { useEffect, useState } from "react";
import { loadQuestions, subjectsOf } from "@/lib/bank";
import { loadProgress, Progress } from "@/lib/progress";

export default function Home() {
  const [subjects, setSubjects] = useState<string[]>([]);
  const [count, setCount] = useState(0);
  const [prog, setProg] = useState<Progress | null>(null);

  useEffect(() => {
    loadQuestions().then((qs) => {
      setSubjects(subjectsOf(qs));
      setCount(qs.length);
    });
    setProg(loadProgress());
  }, []);

  return (
    <main>
      <h1>Master PSLE through practice</h1>
      <p className="muted">
        Every question is tagged to the MOE syllabus, with feedback on why each
        option is right or wrong. Spaced repetition brings back what you find hard.
      </p>

      <div className="card row">
        <div>
          <div className="stat">{prog?.points ?? 0}</div>
          <div className="muted">points</div>
        </div>
        <div>
          <div className="stat">🔥 {prog?.streak ?? 0}</div>
          <div className="muted">day streak</div>
        </div>
        <div>
          <div className="stat">{count}</div>
          <div className="muted">questions in bank</div>
        </div>
        <span className="spacer" />
        <a className="btn" href="/practice">Start practice</a>
      </div>

      <h2>Subjects</h2>
      {subjects.map((s) => (
        <div key={s} className="card row">
          <strong>{s}</strong>
          <span className="spacer" />
          <a className="btn ghost" href={`/practice?subject=${encodeURIComponent(s)}`}>
            Practice {s}
          </a>
        </div>
      ))}
      {subjects.length === 0 && (
        <p className="muted">Loading bank… (seed shipped with the app)</p>
      )}
    </main>
  );
}
