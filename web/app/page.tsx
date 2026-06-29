"use client";

import { useEffect, useState } from "react";
import { loadQuestions, subjectsOf } from "@/lib/bank";

const SUBJECT_ICON: Record<string, string> = {
  Science: "🔬", Mathematics: "➗", English: "📖", Chinese: "🧧",
};

export default function Home() {
  const [subjects, setSubjects] = useState<string[]>([]);
  const [count, setCount] = useState(0);

  useEffect(() => {
    loadQuestions().then((qs) => {
      setSubjects(subjectsOf(qs));
      setCount(qs.length);
    });
  }, []);

  return (
    <main>
      <div className="card wood float-in" style={{ textAlign: "center" }}>
        <div style={{ fontSize: 44, lineHeight: 1 }}>
          <span className="spark">✨</span>
          <span className="nyan" style={{ height: 48, margin: "0 6px" }}>
            <span className="trail" style={{ width: 64, height: 22 }} />
            <span className="cat" style={{ fontSize: 40 }}>🐱</span>
          </span>
          <span className="spark">✨</span>
        </div>
        <h1 className="pixel" style={{ marginBottom: 4 }}>Welcome, adventurer!</h1>
        <p className="muted" style={{ marginTop: 0 }}>
          Defeat questions, earn EXP, level up. Every battle is tagged to the MOE
          syllabus, with feedback on why each answer is right or wrong.
        </p>
        <a className="btn" href="/practice">▶ Start quest</a>
      </div>

      <h2 className="pixel">Maps · {count} questions</h2>
      {subjects.map((s) => (
        <div key={s} className="card row float-in">
          <span style={{ fontSize: 26 }}>{SUBJECT_ICON[s] ?? "🗺️"}</span>
          <strong className="pixel" style={{ fontSize: 14 }}>{s}</strong>
          <span className="spacer" />
          <a className="btn sky" href={`/practice?subject=${encodeURIComponent(s)}`}>
            Enter
          </a>
        </div>
      ))}
      {subjects.length === 0 && (
        <p className="muted">Loading the world map…</p>
      )}
    </main>
  );
}
