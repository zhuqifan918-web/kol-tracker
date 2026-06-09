import { useTweets } from "../hooks/useTweets";
import { useKols, useSummaries, useTweetStats } from "../hooks/useKols";
import type { KolSummary } from "../types";

const BIAS_LABEL: Record<string, string> = {
  bullish: "🟢 偏多",
  bearish: "🔴 偏空",
  neutral: "⚪ 中性",
};
const BIAS_COLOR: Record<string, string> = {
  bullish: "bg-green-50 text-green-700",
  bearish: "bg-red-50 text-red-700",
  neutral: "bg-gray-50 text-gray-600",
};

function SummaryPanel({ summary }: { summary: KolSummary }) {
  return (
    <div className="mt-3 pt-3 border-t border-gray-50 space-y-2 text-sm">
      <div className="flex flex-wrap gap-2 items-center">
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${BIAS_COLOR[summary.overall_bias]}`}>
          {BIAS_LABEL[summary.overall_bias]}
        </span>
        {summary.focus_tickers.map((t) => (
          <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono font-semibold">
            ${t}
          </span>
        ))}
      </div>
      {summary.key_themes.length > 0 && (
        <p className="text-gray-600">
          <span className="font-medium text-gray-700">关注主题：</span>
          {summary.key_themes.join("、")}
        </p>
      )}
      {summary.recent_shift && (
        <p className="text-gray-600">
          <span className="font-medium text-gray-700">近期变化：</span>
          {summary.recent_shift}
        </p>
      )}
      <p className="text-xs text-gray-400">
        总结生成于 {new Date(summary.generated_at).toLocaleDateString("zh-CN")}
      </p>
    </div>
  );
}

export default function KolManagement() {
  const kols = useKols();
  const summaries = useSummaries();
  const { tweets } = useTweets();
  const stats = useTweetStats(tweets);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-gray-900 mb-1">账号管理</h1>
      <p className="text-sm text-gray-500 mb-6">
        追踪账号在{" "}
        <code className="bg-gray-100 px-1 rounded text-xs">config/kols.json</code>{" "}
        中配置，修改后提交即可生效。
      </p>

      {kols.length === 0 ? (
        <p className="text-gray-400 text-sm">加载中…</p>
      ) : (
        <div className="space-y-4">
          {kols.map((kol) => {
            const stat = stats[kol.username];
            const summary = summaries[kol.username];
            return (
              <div
                key={kol.username}
                className={`bg-white rounded-2xl border shadow-sm p-4 ${
                  kol.enabled ? "border-gray-100" : "border-gray-100 opacity-60"
                }`}
              >
                <div className="flex items-center gap-3">
                  <img
                    src={`https://unavatar.io/twitter/${kol.username}`}
                    alt={kol.display_name}
                    className="w-12 h-12 rounded-full object-cover bg-gray-100 shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-gray-900">{kol.display_name}</span>
                      <a
                        href={`https://x.com/${kol.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-500 hover:text-blue-700"
                      >
                        @{kol.username} ↗
                      </a>
                      {!kol.enabled && (
                        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">已暂停</span>
                      )}
                      {kol.notify && kol.enabled && (
                        <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded-full">📧 推送</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 flex gap-3">
                      {kol.focus && <span>{kol.focus}</span>}
                      {stat && <span>已收录 {stat.count} 条投资推文</span>}
                    </div>
                  </div>
                </div>

                {summary ? (
                  <SummaryPanel summary={summary} />
                ) : kol.enabled ? (
                  <p className="mt-2 text-xs text-gray-400">历史总结生成中，等待首次完整采集…</p>
                ) : null}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-8 rounded-2xl bg-blue-50 border border-blue-100 p-5 text-sm text-blue-800">
        <p className="font-semibold mb-2">如何添加/删除追踪账号？</p>
        <ol className="list-decimal list-inside space-y-1 text-blue-700">
          <li>编辑仓库中的 <code className="bg-blue-100 px-1 rounded text-xs">config/kols.json</code></li>
          <li>填写 username、display_name、focus 字段</li>
          <li>enabled: true（追踪）/ false（暂停），notify: true（邮件推送）/ false（不推送）</li>
          <li>提交到 main 分支，下次 Actions 运行时生效</li>
        </ol>
      </div>
    </div>
  );
}
