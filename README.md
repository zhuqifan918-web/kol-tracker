# 股票大V推文追踪系统

追踪 X 上的股票大V，自动分析投资相关推文，通过静态网页集中展示。

**技术栈**：twikit（无需 API 付费）+ Claude API + GitHub Actions + GitHub Pages

---

## 一、首次部署步骤

### 1. Fork / 新建仓库

将本项目 push 到你自己的 GitHub 仓库。

### 2. 生成 X 账号 Cookie（本地执行一次）

```bash
pip install twikit
python scripts/gen_cookies.py
```

按提示输入用户名、邮箱、密码，脚本会输出一段 JSON。复制备用。

> **注意**：建议专门注册一个小号用于此用途，而不是主账号，以降低被限制的风险。

### 3. 配置 GitHub Secrets

进入仓库 → **Settings → Secrets and variables → Actions → New repository secret**，添加：

| Secret 名称 | 值 |
|---|---|
| `X_COOKIES` | 第 2 步输出的 JSON 字符串 |
| `ANTHROPIC_API_KEY` | Claude API 密钥（[获取地址](https://console.anthropic.com)） |

> 如果不使用 Cookie，也可以改用用户名/密码方式，添加 `X_USERNAME`、`X_EMAIL`、`X_PASSWORD` 三个 Secret（此时需关闭账号的 2FA）。

### 4. 配置追踪的大V

编辑 `config/kols.json`，将示例账号替换为你想追踪的大V：

```json
[
  {
    "username": "实际的X用户名",
    "display_name": "显示名称",
    "focus": "美股/A股/加密",
    "enabled": true
  }
]
```

### 5. 启用 GitHub Pages

进入仓库 → **Settings → Pages**：
- Source：选 **Deploy from a branch**
- Branch：选 `gh-pages`（首次 Actions 运行后会自动创建）
- 点击 Save

### 6. 手动触发首次运行

进入仓库 → **Actions → Fetch Tweets & Deploy → Run workflow**

运行完成后，访问 `https://<你的用户名>.github.io/<仓库名>/` 即可看到页面。

---

## 二、日常使用

- **自动运行**：GitHub Actions 每 30 分钟抓取一次新推文并重新部署
- **手动触发**：Actions 页面点击 `Run workflow`
- **添加大V**：编辑 `config/kols.json` 后提交到 main 分支
- **前端筛选**：按大V、方向（看多/看空）、股票代码筛选

---

## 三、项目结构

```
├── .github/workflows/
│   └── fetch-and-deploy.yml   # 定时抓取 + 分析 + 部署
├── config/
│   └── kols.json              # 追踪的大V列表（手动维护）
├── data/
│   └── tweets.json            # 推文 + AI 分析结果（Actions 自动更新）
├── scripts/
│   ├── fetch_and_analyze.py   # 主脚本：抓取 + Claude 分析
│   ├── gen_cookies.py         # 本地运行一次，生成 Cookie
│   └── requirements.txt
└── frontend/                  # React + Vite + Tailwind 前端
    ├── src/
    │   ├── pages/Feed.tsx
    │   ├── pages/KolManagement.tsx
    │   ├── components/TweetCard.tsx
    │   └── components/FilterBar.tsx
    └── public/data/tweets.json
```

---

## 四、本地开发前端

```bash
cd frontend
npm install
npm run dev
```

前端从 `public/data/tweets.json` 加载数据，可手动往里面放测试数据。

---

## 五、注意事项

- twikit 使用账号 Cookie 模拟请求，属非官方方式，有被 X 限制的小概率风险
- Cookie 有效期约 3~6 个月，过期后需重新运行 `gen_cookies.py` 更新 Secret
- GitHub Actions 免费版每月有 2000 分钟执行时长，每 30 分钟运行一次大约消耗 ~60 分钟/月，完全够用
