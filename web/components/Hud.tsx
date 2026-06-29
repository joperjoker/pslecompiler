"use client";

import { useEffect, useState } from "react";
import { loadProgress } from "@/lib/progress";
import { levelFromPoints } from "@/lib/level";

// Live MMORPG-style HUD: Nyan mascot + level + EXP bar + star coins + streak.
export default function Hud() {
  const [points, setPoints] = useState(0);
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    const read = () => {
      const p = loadProgress();
      setPoints(p.points);
      setStreak(p.streak);
    };
    read();
    window.addEventListener("progress-updated", read);
    return () => window.removeEventListener("progress-updated", read);
  }, []);

  const lv = levelFromPoints(points);

  return (
    <div className="hud">
      <span className="nyan" title="Nyan!">
        <span className="trail" />
        <span className="cat">🐱</span>
      </span>
      <span className="chip-lv">Lv {lv.level}</span>
      <div className="exp">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 2 }}>
          <span className="badge">{lv.title}</span>
          <span className="muted" style={{ fontSize: 11 }}>{lv.intoLevel}/{lv.span} EXP</span>
        </div>
        <div className="bar"><span style={{ width: `${lv.pct}%` }} /></div>
      </div>
      <span className="badge">⭐ {points}</span>
      <span className="badge">🔥 {streak}</span>
    </div>
  );
}
