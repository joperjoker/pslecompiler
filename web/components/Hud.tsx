"use client";

import { useGame } from "./GameProvider";
import { levelFromPoints } from "@/lib/level";

// Live MMORPG-style HUD: Nyan mascot + level + EXP bar + star coins + streak.
export default function Hud() {
  const { progress, user } = useGame();
  const lv = levelFromPoints(progress.points);

  return (
    <div className="hud">
      <span className="nyan" title="Nyan!">
        <span className="trail" />
        <span className="cat">🐱</span>
      </span>
      <span className="chip-lv">Lv {lv.level}</span>
      <div className="exp">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 2 }}>
          <span className="badge">{user ? user.email.split("@")[0] : lv.title}</span>
          <span className="muted" style={{ fontSize: 11 }}>{lv.intoLevel}/{lv.span} EXP</span>
        </div>
        <div className="bar"><span style={{ width: `${lv.pct}%` }} /></div>
      </div>
      <span className="badge">⭐ {progress.points}</span>
      <span className="badge">🔥 {progress.streak}</span>
    </div>
  );
}
