import type { Tweet } from "../types";

interface Props {
  tweets: Tweet[];
  selectedKols: string[];
  onToggleKol: (username: string) => void;
  direction: string;
  onDirectionChange: (d: string) => void;
  ticker: string;
  onTickerChange: (t: string) => void;
}

const DIRECTIONS = [
  { value: "", label: "全部方向" },
  { value: "bullish", label: "🟢 看多" },
  { value: "bearish", label: "🔴 看空" },
  { value: "neutral", label: "⚪ 中性" },
];

export default function FilterBar({
  tweets,
  selectedKols,
  onToggleKol,
  direction,
  onDirectionChange,
  ticker,
  onTickerChange,
}: Props) {
  const allKols = Array.from(
    new Map(
      tweets.map((t) => [t.kol_username, t.kol_display_name])
    ).entries()
  );

  return (
    <div className="flex flex-wrap gap-3 items-center py-3 px-4 bg-white border-b border-gray-100 sticky top-14 z-10">
      {/* KOL chips */}
      <div className="flex flex-wrap gap-2">
        {allKols.map(([username, displayName]) => (
          <button
            key={username}
            onClick={() => onToggleKol(username)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedKols.includes(username)
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            @{displayName}
          </button>
        ))}
      </div>

      {/* Direction */}
      <select
        value={direction}
        onChange={(e) => onDirectionChange(e.target.value)}
        className="px-3 py-1 rounded-lg border border-gray-200 text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        {DIRECTIONS.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
      </select>

      {/* Ticker search */}
      <input
        type="text"
        placeholder="搜索标的，如 NVDA"
        value={ticker}
        onChange={(e) => onTickerChange(e.target.value.toUpperCase())}
        className="px-3 py-1 rounded-lg border border-gray-200 text-sm w-36 focus:outline-none focus:ring-2 focus:ring-blue-300"
      />

      {(selectedKols.length > 0 || direction || ticker) && (
        <button
          onClick={() => {
            selectedKols.forEach(onToggleKol);
            onDirectionChange("");
            onTickerChange("");
          }}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          清除筛选
        </button>
      )}
    </div>
  );
}
