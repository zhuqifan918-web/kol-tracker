import { useState, useEffect } from "react";
import type { KOL, Summaries } from "../types";
import type { Tweet } from "../types";

export function useKols() {
  const [kols, setKols] = useState<KOL[]>([]);
  useEffect(() => {
    fetch(`./data/kols.json?t=${Date.now()}`)
      .then((r) => r.json())
      .then(setKols)
      .catch(() => setKols([]));
  }, []);
  return kols;
}

export function useSummaries() {
  const [summaries, setSummaries] = useState<Summaries>({});
  useEffect(() => {
    fetch(`./data/summaries.json?t=${Date.now()}`)
      .then((r) => r.json())
      .then(setSummaries)
      .catch(() => setSummaries({}));
  }, []);
  return summaries;
}

export function useTweetStats(tweets: Tweet[]): Record<string, { count: number; lastSeen: string }> {
  const stats: Record<string, { count: number; lastSeen: string }> = {};
  for (const t of tweets) {
    const s = stats[t.kol_username];
    if (!s) {
      stats[t.kol_username] = { count: 1, lastSeen: t.published_at };
    } else {
      s.count++;
      if (t.published_at > s.lastSeen) s.lastSeen = t.published_at;
    }
  }
  return stats;
}
