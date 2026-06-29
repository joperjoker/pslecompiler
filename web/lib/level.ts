// MMORPG-style leveling derived from points (EXP). Each level needs a bit more
// EXP than the last (classic RPG curve), so the EXP bar always has somewhere to go.

export type LevelInfo = {
  level: number;
  intoLevel: number; // EXP earned within the current level
  span: number;      // EXP needed to clear the current level
  pct: number;       // 0..100 progress to next level
  title: string;     // cute rank title
};

const TITLES = [
  "Slime Tamer", "Mushroom Scout", "Acorn Knight", "Star Apprentice",
  "Rainbow Adept", "Comet Ranger", "Galaxy Sage", "Nyan Champion",
];

function expForLevel(level: number): number {
  // EXP required to go from `level` to `level+1`
  return 80 + level * 40;
}

export function levelFromPoints(points: number): LevelInfo {
  let level = 1;
  let remaining = Math.max(0, points);
  while (remaining >= expForLevel(level)) {
    remaining -= expForLevel(level);
    level += 1;
  }
  const span = expForLevel(level);
  const intoLevel = remaining;
  const pct = Math.round((intoLevel / span) * 100);
  const title = TITLES[Math.min(level - 1, TITLES.length - 1)];
  return { level, intoLevel, span, pct, title };
}
