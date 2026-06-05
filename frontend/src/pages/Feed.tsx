import { useState } from "react";
import { useTweets } from "../hooks/useTweets";
import TweetCard from "../components/TweetCard";
import FilterBar from "../components/FilterBar";

export default function Feed() {
  const { tweets, loading, error, lastUpdated, refresh } = useTweets();
  const [selectedKols, setSelectedKols] = useState<string[]>([]);
  const [direction, setDirection] = useState("");
  const [ticker, setTicker] = useState("");

  const toggleKol = (username: string) => {
    setSelectedKols((prev) =>
      prev.includes(username)
        ? prev.filter((k) => k !== username)
        : [...prev, username]
    );
  };

  const filtered = tweets.filter((t) => {
    if (selectedKols.length > 0 && !selectedKols.includes(t.kol_username))
      return false;
    if (direction && t.analysis.direction !== direction) return false;
    if (
      ticker &&
      !t.analysis.tickers.some((k) => k.includes(ticker))
    )
      return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sticky filter bar (below the header) */}
      <FilterBar
        tweets={tweets}
        selectedKols={selectedKols}
        onToggleKol={toggleKol}
        direction={direction}
        onDirectionChange={setDirection}
        ticker={ticker}
        onTickerChange={setTicker}
      />

      <main className="max-w-2xl mx-auto px-4 py-6">
        {/* Status bar */}
        <div className="flex items-center justify-between mb-4 text-xs text-gray-400">
          <span>
            {loading
              ? "加载中…"
              : error
              ? `加载失败：${error}`
              : `共 ${filtered.length} 条${tweets.length !== filtered.length ? `（已筛选，全部 ${tweets.length} 条）` : ""}`}
          </span>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span>
                更新于{" "}
                {lastUpdated.toLocaleTimeString("zh-CN", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            )}
            <button
              onClick={refresh}
              className="text-blue-500 hover:text-blue-700 font-medium"
            >
              刷新
            </button>
          </div>
        </div>

        {/* Tweet list */}
        {loading ? (
          <div className="flex justify-center py-20 text-gray-400">
            加载中…
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            {tweets.length === 0
              ? "暂无数据，等待 GitHub Actions 首次运行"
              : "没有符合条件的推文"}
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((tweet) => (
              <TweetCard
                key={tweet.tweet_id}
                tweet={tweet}
                onTickerClick={setTicker}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
