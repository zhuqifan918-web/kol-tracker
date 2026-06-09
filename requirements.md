# 股票大V推文追踪系统 — 需求文档

## 一、背景与目标

追踪 X（Twitter）上指定的股票大V账号，当他们发布新推文并涉及股票推荐或投资方向时，自动生成 AI 摘要，通过前端页面集中展示，支持跳转到原始推文。

**约束条件**
- X 账号：普通用户账号，通过 Cookie 方式认证（无需付费 API）
- 追踪规模：≤ 10 个大V
- 部署：完全基于 GitHub（无需自建服务器，零成本）

---

## 二、整体架构

采用**全静态 + GitHub Actions 无服务器**方案：

```
┌─────────────────────────────────────────────────────┐
│                   GitHub Repository                  │
│                                                      │
│  ┌──────────────────┐      ┌──────────────────────┐  │
│  │  GitHub Actions  │      │     data/ 目录        │  │
│  │  (定时任务)       │─────▶│  tweets.json         │  │
│  │                  │      └──────────┬───────────┘  │
│  │  1. 拉取推文      │                 │              │
│  │  2. AI 分析       │                 │              │
│  │  3. 提交结果      │                 │              │
│  └──────────────────┘                 │              │
│                                       │              │
│  ┌────────────────────────────────────▼───────────┐  │
│  │           GitHub Pages (静态前端)               │  │
│  │   React SPA，直接 fetch data/tweets.json 渲染   │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**数据流**：GitHub Actions 每 30 分钟运行 → twscrape 拉新推文 → Claude API 分析 → 结果追加写入 `data/tweets.json` 并 commit → GitHub Pages 前端读取 JSON 展示。

---

## 三、已实现功能（当前状态）

### 3.1 数据采集 ✅

- 使用 **twscrape** 库（基于 X Cookie，无需付费 API）抓取推文
- GitHub Actions 每 **30 分钟**自动运行一次，支持手动触发
- 按 `tweet_id` 去重，仅处理新推文
- 最多保留 1000 条历史记录
- X 账号 Cookie 存储在 GitHub Secrets（`X_ACCOUNTS`）中

### 3.2 AI 分析 ✅

使用 Claude Haiku 模型对每条新推文分析，输出结构化 JSON：

| 字段 | 说明 |
|------|------|
| `is_investment_related` | 是否含投资内容（false 则过滤不展示） |
| `tickers` | 涉及的股票/加密货币代码列表 |
| `direction` | `bullish`（看多）/ `bearish`（看空）/ `neutral`（中性） |
| `summary` | 1–3 句中文摘要 |
| `confidence` | 置信度：`high` / `medium` / `low` |

支持第三方 Claude 兼容 API（通过 `ANTHROPIC_BASE_URL` 配置）。

### 3.3 邮件推送 ✅

- 每个大V可独立设置 `notify: true/false`
- 有新投资推文时，通过 SMTP 发送邮件（支持 QQ/163/Gmail）
- 邮件包含：方向标签、股票标的、AI 摘要、原推链接

### 3.4 前端页面 ✅

部署在 GitHub Pages，地址：`https://zhuqifan918-web.github.io/kol-tracker/`

**推文 Feed 页（主页）**
- 推文卡片：大V头像 + 用户名（可跳转 X 主页）、发布时间、方向标签、股票标的 Tag、AI 摘要、原文折叠展开、「查看原推 ↗」按钮
- 筛选栏：按大V / 方向（看多/看空/中性）/ 股票代码筛选
- 每 5 分钟自动刷新数据

**账号管理页**
- 展示已追踪的大V（从推文数据中统计）：头像、用户名、专注领域、已收录推文数
- 说明如何通过修改 `config/kols.json` 增删账号

### 3.5 大V配置 ✅

`config/kols.json` 中每个大V可配置：

```json
{
  "username": "X用户名",
  "display_name": "显示名称",
  "focus": "专注领域",
  "enabled": true,
  "notify": true
}
```

### 3.6 Secrets 配置 ✅

| Secret | 说明 |
|--------|------|
| `X_ACCOUNTS` | twscrape 账号 JSON（本地运行 gen_accounts.py 生成） |
| `ANTHROPIC_API_KEY` | Claude API 密钥 |
| `ANTHROPIC_BASE_URL` | （可选）第三方 Claude 兼容 API 地址 |
| `NOTIFY_SMTP_HOST` | SMTP 服务器，如 `smtp.qq.com` |
| `NOTIFY_SMTP_PORT` | SMTP 端口，如 `465` |
| `NOTIFY_SMTP_USER` | 发件邮箱 |
| `NOTIFY_SMTP_PASS` | 邮箱授权码 |
| `NOTIFY_EMAIL_TO` | 收件邮箱 |

---

## 四、待实现功能

### 4.1 账号管理页增强（P1）

**需求**：账号管理页除展示统计数据外，还需明确展示：
- 当前所有追踪的大V列表（直接读取 `config/kols.json`）
- 每个大V的 X 主页链接（可点击跳转）
- 是否启用（`enabled`）、是否开启推送（`notify`）状态
- 专注领域标签

**当前问题**：账号管理页数据来源是 `tweets.json`，只有发过投资推文的大V才会出现；新添加但尚未采集到数据的大V不可见。

**解决方案**：
1. 在 GitHub Actions 构建时，将 `config/kols.json` 也复制到 `frontend/public/data/kols.json`
2. 前端账号管理页读取 `data/kols.json` 作为主数据源，`tweets.json` 只用于补充统计数据

---

### 4.2 历史推文抓取与总结（P1）

**需求**：
1. 对每个大V，抓取其过去 **1 年内**的历史推文（而不仅是最近 20 条）
2. 按时间**倒序**展示（最新的在最前）
3. 新增"**历史总结**"功能：对某个大V的所有历史推文进行聚合分析，生成：
   - 常关注的标的和板块
   - 整体观点倾向（偏多/偏空）
   - 近期关注重点变化趋势
   - 代表性观点摘录

**实现方案**：

**抓取部分**：
- 新增 `scripts/fetch_history.py`，一次性任务，抓取每个大V最近 1 年的全部推文
- twscrape 支持翻页（`cursor`），可持续抓取直到推文超过 1 年
- 历史数据写入 `data/tweets.json`，与增量数据格式相同

**总结部分**：
- 新增 `data/summaries.json`，存储每个大V的历史总结
- GitHub Actions 在检测到某大V有足够历史数据时，调用 Claude 生成总结
- 总结内容按大V分组，可在前端"账号管理页"展示

**前端部分**：
- Feed 页默认按时间倒序（已实现，需验证）
- 账号管理页每个大V卡片下方展示该大V的历史总结

---

## 五、项目结构

```
kol-tracker/
├── .github/workflows/
│   └── fetch-and-deploy.yml   # 定时抓取 + 分析 + 部署（每 30 分钟）
├── config/
│   └── kols.json              # 追踪的大V列表（手动维护）
├── data/
│   ├── tweets.json            # 推文 + AI 分析结果（Actions 自动更新）
│   └── summaries.json         # 各大V历史总结（待实现）
├── scripts/
│   ├── fetch_and_analyze.py   # 主脚本：增量抓取 + Claude 分析 + 邮件推送
│   ├── fetch_history.py       # 一次性脚本：抓取历史 1 年推文（待实现）
│   ├── inject_cookies.py      # 本地运行：从浏览器 Cookie 生成认证文件
│   ├── gen_accounts.py        # 本地运行：用户名/密码方式生成认证文件
│   └── requirements.txt
└── frontend/                  # React + Vite + Tailwind 前端
    ├── src/
    │   ├── App.tsx
    │   ├── types.ts
    │   ├── hooks/useTweets.ts
    │   ├── pages/
    │   │   ├── Feed.tsx
    │   │   └── KolManagement.tsx
    │   └── components/
    │       ├── TweetCard.tsx
    │       └── FilterBar.tsx
    └── public/data/
        ├── tweets.json        # 构建时从 data/ 复制
        └── kols.json          # 构建时从 config/ 复制（待实现）
```

---

## 六、后续扩展

- 浏览器 Web Push / Telegram Bot 推送
- 前端直接添加/删除大V（写回 `config/kols.json`）
- 推文情绪趋势图（某标的近期看多/看空变化）
- 多用户支持
