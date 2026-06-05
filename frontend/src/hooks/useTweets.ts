import { useState, useEffect, useCallback } from "react";
import type { Tweet } from "../types";

const DATA_URL = "./data/tweets.json";
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useTweets() {
  const [tweets, setTweets] = useState<Tweet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchTweets = useCallback(async () => {
    try {
      const res = await fetch(`${DATA_URL}?t=${Date.now()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: Tweet[] = await res.json();
      setTweets(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTweets();
    const timer = setInterval(fetchTweets, REFRESH_INTERVAL);
    return () => clearInterval(timer);
  }, [fetchTweets]);

  return { tweets, loading, error, lastUpdated, refresh: fetchTweets };
}
