# 股票大V推文追踪系统 — 需求文档

## 一、背景与目标

追踪 X（Twitter）上指定的股票大V账号，当他们发布新推文并涉及股票推荐或投资方向时，自动生成 AI 摘要，通过前端页面集中展示，支持跳转到原始推文。

**约束条件**
- X 账号：普通用户账号，注册免费 Developer 账号（Free Tier）
- 追踪规模：≤ 10 个大V
- 推送通知：MVP 阶段暂不实现
- 部署：完全基于 GitHub（无需自建服务器）

---

## 二、整体架构

采用**全静态 + GitHub Actions 无服务器**方案，零服务器成本：

```
┌─────────────────────────────────────────────────────┐
│                   GitHub Repository                  │
│                                                      │
│  ┌──────────────────┐      ┌──────────────────────┐  │
│  │  GitHub Actions  │      │     data/ 目录        │  │
│  │  (定时任务)       │─────▶│  tweets.json         │  │
│  │                  │      │  kols.json           │  │
│  │  1. 拉取推文      │      └──────────┬───────────┘  │
│  │  2. AI 分析       │                 │              │
│  │  3. 提交结果      │                 │              │
│  └──────────────────┘                 │              │
│                                       │              │
│  ┌────────────────────────────────────▼───────────┐  │
│  │           GitHub Pages (静态前端)               │  │
│  │   React SPA，直接 fetch data/*.json 渲染        │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**数据流**：GitHub Actions 每 30 分钟运行 → 调用 X API 拉新推文 → 调用 Claude API 分析 → 结果追加写入 `data/tweets.json` 并 commit → GitHub Pages 前端读取 JSON 展示。

---

## 三、功能需求

### 3.1 数据采集（GitHub Actions）

**触发方式**
- 定时触发：每 30 分钟执行一次（`cron: '*/30 * * * *'`）
- 手动触发：支持 `workflow_dispatch` 手动运行

**采集逻辑**
1. 读取配置文件 `config/kols.json`（大V列表）
2. 对每个大V，调用 X API v2 `GET /2/users/:id/tweets` 拉取最新推文
3. 与 `data/tweets.json` 中已有记录对比，仅处理新推文（按 tweet_id 去重）
4. 将新推文交给 Claude API 分析
5. 将分析结果追加写入 `data/tweets.json`，触发 GitHub Pages 重新部署

**X API Free Tier 限制说明**
- 每月可读取推文数：500,000 条（足够 10 个账号 × 30 分钟轮询）
- 需使用 OAuth 2.0 Bearer Token（App-only 认证）
- API 密钥存储在 GitHub Actions Secrets 中

### 3.2 AI 分析（Claude API）

对每条新推文调用 Claude API 分析，返回结构化 JSON：

```json
{
  "is_investment_related": true,
  "tickers": ["NVDA", "AMD"],
  "direction": "bullish",
  "summary": "看好 AI 算力需求驱动的半导体板块，建议关注 NVDA 和 AMD 的短期回调买入机会。",
  "confidence": "high"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `is_investment_related` | bool | 是否包含投资相关内容，false 则不展示 |
| `tickers` | string[] | 提及的股票代码列表，可为空 |
| `direction` | enum | `bullish`（看多）/ `bearish`（看空）/ `neutral`（中性） |
| `summary` | string | 中文摘要，1–3 句话 |
| `confidence` | enum | `high` / `medium` / `low` |

**成本控制**：使用 Claude Haiku 模型处理过滤（判断是否投资相关），仅对相关推文使用 Sonnet 做详细分析；启用 Prompt Caching 复用 System Prompt。

### 3.3 数据存储（JSON 文件）

**`config/kols.json`** — 大V配置（手动维护）
```json
[
  {
    "id": "123456789",
    "username": "SomeStockGuru",
    "display_name": "某股票大V",
    "focus": "美股科技",
    "avatar_url": "https://...",
    "enabled": true
  }
]
```

**`data/tweets.json`** — 推文与分析结果（自动维护）
```json
[
  {
    "tweet_id": "1234567890123456789",
    "kol_username": "SomeStockGuru",
    "kol_display_name": "某股票大V",
    "content": "原始推文内容...",
    "tweet_url": "https://x.com/SomeStockGuru/status/1234567890123456789",
    "published_at": "2026-06-03T10:00:00Z",
    "fetched_at": "2026-06-03T10:30:00Z",
    "analysis": {
      "is_investment_related": true,
      "tickers": ["NVDA"],
      "direction": "bullish",
      "summary": "AI 需求旺盛，看好 NVDA 后续表现。",
      "confidence": "high"
    }
  }
]
```

### 3.4 前端页面（GitHub Pages）

**技术栈**：React + TypeScript + Vite，构建产物推送到 `gh-pages` 分支。

#### 页面一：推文 Feed（主页）

布局：
```
┌──────────────────────────────────────────────────────┐
│  📈 股票大V追踪                        [账号管理]      │
├──────────────────────────────────────────────────────┤
│  筛选：[全部大V ▼]  [全部方向 ▼]  [全部标的 ▼]        │
│         最近更新：2026-06-03 10:30                    │
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │ 🟢 [头像] SomeStockGuru · 2小时前              │  │
│  │    涉及：$NVDA $AMD   方向：看多               │  │
│  │    摘要：AI 需求旺盛，看好 NVDA 后续表现...     │  │
│  │    ─────────────────────────────────────────  │  │
│  │    原文：I'm very bullish on $NVDA because...  │  │
│  │    [折叠/展开]              [查看原推 ↗]        │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ 🔴 [头像] AnotherGuru · 5小时前                │  │
│  │    ...                                         │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

推文卡片包含：
- 大V头像 + 用户名（点击跳转 X 主页）
- 发布时间（相对时间）
- 方向标签：🟢 看多 / 🔴 看空 / ⚪ 中性
- 股票标的 Tag（可点击筛选）
- AI 摘要（中文，始终可见）
- 原始推文（默认折叠，点击展开）
- **「查看原推 ↗」按钮**（跳转 X 原始链接，新标签页打开）

#### 页面二：账号管理

- 展示当前追踪的大V列表（头像、用户名、专注领域、开关）
- 说明：账号增删通过修改 `config/kols.json` 文件进行（MVP 阶段）

---

## 四、项目结构

```
repo-root/
├── .github/
│   └── workflows/
│       └── fetch-tweets.yml      # 定时抓取 + 分析 + 提交
├── config/
│   └── kols.json                 # 大V配置（手动维护）
├── data/
│   └── tweets.json               # 推文 + 分析结果（Actions 自动维护）
├── scripts/
│   └── fetch_and_analyze.py      # 采集 + AI 分析脚本
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── TweetCard.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   └── KolList.tsx
│   │   └── pages/
│   │       ├── Feed.tsx
│   │       └── KolManagement.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## 五、GitHub Actions 工作流

```yaml
# .github/workflows/fetch-tweets.yml
name: Fetch & Analyze Tweets
on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install tweepy anthropic
      - run: python scripts/fetch_and_analyze.py
        env:
          X_BEARER_TOKEN: ${{ secrets.X_BEARER_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Commit updated data
        run: |
          git config user.name "github-actions[bot]"
          git add data/tweets.json
          git diff --staged --quiet || git commit -m "chore: update tweets"
          git push
```

---

## 六、Secrets 配置

在 GitHub Repository Settings → Secrets and variables → Actions 中配置：

| Secret 名称 | 说明 |
|-------------|------|
| `X_BEARER_TOKEN` | X API v2 Bearer Token（Free Tier） |
| `ANTHROPIC_API_KEY` | Claude API 密钥 |

---

## 七、MVP 开发任务清单

**Phase 1：数据管道**
- [ ] 注册 X Developer 账号，获取 Bearer Token
- [ ] 编写 `scripts/fetch_and_analyze.py`（X API 拉取 + Claude 分析 + 写 JSON）
- [ ] 配置 GitHub Actions 工作流
- [ ] 本地测试数据管道跑通

**Phase 2：前端**
- [ ] 初始化 React + Vite 项目
- [ ] 实现推文卡片组件（含原推链接）
- [ ] 实现筛选栏（按大V / 方向 / 标的）
- [ ] 实现账号管理页
- [ ] 配置 GitHub Pages 自动部署

**Phase 3：联调验收**
- [ ] Actions 自动更新数据，前端页面实时反映
- [ ] 验证原推链接正确可跳转
- [ ] 验证 AI 分析结果准确性

---

## 八、后续扩展（MVP 之后）

- 推送通知：浏览器 Web Push / Telegram Bot / 如流消息
- 前端支持手动添加大V账号（写回仓库 `config/kols.json`）
- 推文情绪趋势图（某标的近期看多/看空比例变化）
- 多用户支持 + 权限管理
