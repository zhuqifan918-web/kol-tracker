import { useState } from "react";
import type { Tweet } from "../types";

const DIRECTION_BADGE: Record<string, string> = {
  bullish: "bg-green-100 text-green-700",
  bearish: "bg-red-100 text-red-700",
  neutral: "bg-gray-100 text-gray-600",
};
const DIRECTION_LABEL: Record<string, string> = {
  bullish: "🟢 看多",
  bearish: "🔴 看空",
  neutral: "⚪ 中性",
};
const CONFIDENCE_LABEL: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.floor(hours / 24);
  return `${days} 天前`;
}

interface Props {
  tweet: Tweet;
  onTickerClick: (ticker: string) => void;
}

export default function TweetCard({ tweet, onTickerClick }: Props) {
  const [expanded, setExpanded] = useState(false);
  const { analysis } = tweet;
  const direction = analysis.direction ?? "neutral";

  const avatarFallback = `https://unavatar.io/twitter/${tweet.kol_username}`;

  return (
    <article className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <a
            href={`https://x.com/${tweet.kol_username}`}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0"
          >
            <img
              src={tweet.kol_avatar_url || avatarFallback}
              alt={tweet.kol_display_name}
              onError={(e) => {
                (e.target as HTMLImageElement).src = avatarFallback;
              }}
              className="w-10 h-10 rounded-full object-cover bg-gray-100"
            />
          </a>
          <div className="min-w-0">
            <a
              href={`https://x.com/${tweet.kol_username}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-gray-900 hover:text-blue-600 truncate block"
            >
              {tweet.kol_display_name}
            </a>
            <span className="text-xs text-gray-400">
              @{tweet.kol_username}
              {tweet.kol_focus && ` · ${tweet.kol_focus}`}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${DIRECTION_BADGE[direction]}`}
          >
            {DIRECTION_LABEL[direction]}
          </span>
          <span className="text-xs text-gray-400">
            {relativeTime(tweet.published_at)}
          </span>
        </div>
      </div>

      {/* Tickers */}
      {analysis.tickers.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {analysis.tickers.map((t) => (
            <button
              key={t}
              onClick={() => onTickerClick(t)}
              className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono font-semibold hover:bg-blue-100 transition-colors"
            >
              ${t}
            </button>
          ))}
          {analysis.confidence && (
            <span className="px-2 py-0.5 bg-gray-50 text-gray-500 rounded text-xs">
              置信度：{CONFIDENCE_LABEL[analysis.confidence]}
            </span>
          )}
        </div>
      )}

      {/* AI Summary */}
      {analysis.summary && (
        <p className="text-gray-800 text-sm leading-relaxed mb-3 bg-gray-50 rounded-xl px-4 py-3">
          {analysis.summary}
        </p>
      )}

      {/* Original content (collapsible) */}
      <div className="border-t border-gray-50 pt-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-gray-400 hover:text-gray-600 mb-2 flex items-center gap-1"
        >
          <span>{expanded ? "▼" : "▶"}</span>
          原文
        </button>
        {expanded && (
          <p className="text-sm text-gray-500 leading-relaxed whitespace-pre-wrap">
            {tweet.content}
          </p>
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-end mt-3">
        <a
          href={tweet.tweet_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          查看原推
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </article>
  );
}
