import { useTweets } from "../hooks/useTweets";

export default function KolManagement() {
  const { tweets } = useTweets();

  // Build KOL summary from tweet data
  const kolStats = new Map<
    string,
    { displayName: string; focus: string; avatarUrl: string; count: number; lastSeen: string }
  >();
  for (const t of tweets) {
    const existing = kolStats.get(t.kol_username);
    if (!existing) {
      kolStats.set(t.kol_username, {
        displayName: t.kol_display_name,
        focus: t.kol_focus,
        avatarUrl: t.kol_avatar_url,
        count: 1,
        lastSeen: t.published_at,
      });
    } else {
      existing.count++;
      if (t.published_at > existing.lastSeen) existing.lastSeen = t.published_at;
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-gray-900 mb-1">账号管理</h1>
      <p className="text-sm text-gray-500 mb-6">
        追踪账号在{" "}
        <code className="bg-gray-100 px-1 rounded text-xs">config/kols.json</code>{" "}
        中配置，修改后提交即可生效。
      </p>

      {kolStats.size === 0 ? (
        <p className="text-gray-400 text-sm">暂无数据，等待首次采集。</p>
      ) : (
        <div className="space-y-3">
          {Array.from(kolStats.entries()).map(([username, info]) => (
            <div
              key={username}
              className="flex items-center gap-4 bg-white rounded-2xl border border-gray-100 shadow-sm p-4"
            >
              <img
                src={info.avatarUrl || `https://unavatar.io/twitter/${username}`}
                alt={info.displayName}
                className="w-12 h-12 rounded-full object-cover bg-gray-100 shrink-0"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">
                    {info.displayName}
                  </span>
                  <span className="text-xs text-gray-400">@{username}</span>
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {info.focus && <span className="mr-3">{info.focus}</span>}
                  <span>已收录 {info.count} 条投资推文</span>
                </div>
              </div>
              <a
                href={`https://x.com/${username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:text-blue-700 shrink-0"
              >
                主页 ↗
              </a>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 rounded-2xl bg-blue-50 border border-blue-100 p-5 text-sm text-blue-800">
        <p className="font-semibold mb-2">如何添加/删除追踪账号？</p>
        <ol className="list-decimal list-inside space-y-1 text-blue-700">
          <li>
            编辑仓库中的{" "}
            <code className="bg-blue-100 px-1 rounded text-xs">config/kols.json</code>
          </li>
          <li>填写 username、display_name、focus 字段</li>
          <li>将 enabled 设为 true（追踪）或 false（暂停）</li>
          <li>提交到 main 分支，下次 Actions 运行时生效</li>
        </ol>
      </div>
    </div>
  );
}
