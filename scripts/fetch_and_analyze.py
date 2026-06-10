"""
Fetch tweets from tracked KOLs via twscrape (no API key required),
analyze investment-related content with Claude, and update data/tweets.json.

Auth: X_ACCOUNTS env var (JSON exported by gen_accounts.py) is loaded into
      twscrape's in-memory pool each run.
"""

import asyncio
import json
import os
import smtplib
import tempfile
from datetime import datetime, timezone
from email.mime.text import MIMEText

import anthropic
from twscrape import API

TWEETS_FILE = "data/tweets.json"
SUMMARIES_FILE = "data/summaries.json"
KOLS_FILE = "config/kols.json"
MAX_TWEETS_STORED = 5000
FETCH_COUNT = 20
MIN_TWEETS_FOR_SUMMARY = 5  # minimum investment tweets to generate a summary

DIRECTION_ZH = {"bullish": "🟢 看多", "bearish": "🔴 看空", "neutral": "⚪ 中性"}


def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def get_api() -> API:
    api = API()
    accounts_json = os.environ.get("X_ACCOUNTS")
    if not accounts_json:
        raise RuntimeError("X_ACCOUNTS env var is not set. Run scripts/gen_accounts.py first.")
    accounts = json.loads(accounts_json)
    for acc in accounts:
        await api.pool.add_account(**{
            "username":       acc["username"],
            "password":       acc["password"],
            "email":          acc["email"],
            "email_password": acc.get("email_password", acc["password"]),
            "cookies":        acc.get("cookies"),
        })
    return api


def analyze_tweet(text: str, claude: anthropic.Anthropic) -> dict:
    system = (
        "You are a financial analyst assistant. "
        "Analyze tweets and return structured JSON only — no markdown, no extra text."
    )
    prompt = f"""Analyze this tweet for investment relevance.

Tweet: {text}

Return a JSON object with exactly these fields:
- is_investment_related: boolean — true if the tweet discusses stocks, ETFs, crypto, market analysis, specific tickers, or investment recommendations
- tickers: array of stock/crypto ticker symbols mentioned (e.g. ["NVDA", "BTC"]), empty array if none
- direction: "bullish" | "bearish" | "neutral" | null — null only if not investment related
- summary: string — 1-3 sentence Chinese summary of the investment insight; null if not investment related
- confidence: "high" | "medium" | "low" | null — null if not investment related"""

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.content[0].text)


def send_email_notification(tweet: dict) -> None:
    smtp_host = os.environ.get("NOTIFY_SMTP_HOST")
    smtp_port = int(os.environ.get("NOTIFY_SMTP_PORT", "465"))
    smtp_user = os.environ.get("NOTIFY_SMTP_USER")
    smtp_pass = os.environ.get("NOTIFY_SMTP_PASS")
    to_addr   = os.environ.get("NOTIFY_EMAIL_TO")

    if not all([smtp_host, smtp_user, smtp_pass, to_addr]):
        return

    a = tweet["analysis"]
    direction = DIRECTION_ZH.get(a.get("direction", ""), "")
    tickers = "  ".join(f"${t}" for t in a.get("tickers", []))

    subject = f"[KOL追踪] {tweet['kol_display_name']}" + (f" · {tickers}" if tickers else "")
    body = f"""{tweet['kol_display_name']} (@{tweet['kol_username']}) 发布了新推文

{'方向：' + direction if direction else ''}{'　　标的：' + tickers if tickers else ''}

{a.get('summary', '')}

原文：
{tweet['content']}

查看原推：{tweet['tweet_url']}
"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_addr

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, [to_addr], msg.as_string())
        print(f"  Email sent to {to_addr}")
    except Exception as exc:
        print(f"  Email failed: {exc}")


async def main() -> None:
    kols = load_json(KOLS_FILE, [])
    existing_tweets: list = load_json(TWEETS_FILE, [])
    existing_ids = {t["tweet_id"] for t in existing_tweets}

    api = await get_api()
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    claude = anthropic.Anthropic(base_url=base_url) if base_url else anthropic.Anthropic()
    new_tweets: list = []

    for kol in kols:
        if not kol.get("enabled", True):
            continue

        username = kol["username"]
        print(f"\nFetching @{username}...")

        try:
            user = await api.user_by_login(username)
            if not user:
                print(f"  User not found: {username}")
                continue
            tweets = []
            async for tweet in api.user_tweets(user.id, limit=FETCH_COUNT):
                tweets.append(tweet)
        except Exception as exc:
            print(f"  ERROR fetching {username}: {exc}")
            continue

        avatar_url = getattr(user, "profileImageUrl", "") or kol.get("avatar_url", "")
        if avatar_url:
            avatar_url = avatar_url.replace("_normal", "_400x400")

        for tweet in tweets:
            tweet_id = str(tweet.id)
            if tweet_id in existing_ids:
                continue

            text = tweet.rawContent or ""
            print(f"  Analyzing {tweet_id}: {text[:60]}...")

            try:
                analysis = analyze_tweet(text, claude)
            except Exception as exc:
                import traceback
                print(f"  Analysis error: {exc}")
                traceback.print_exc()
                continue

            if not analysis.get("is_investment_related"):
                print("  Not investment-related, skipping")
                continue

            record = {
                "tweet_id": tweet_id,
                "kol_username": username,
                "kol_display_name": kol.get("display_name", username),
                "kol_avatar_url": avatar_url,
                "kol_focus": kol.get("focus", ""),
                "content": text,
                "tweet_url": f"https://x.com/{username}/status/{tweet_id}",
                "published_at": tweet.date.isoformat() if tweet.date else datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "analysis": analysis,
            }
            new_tweets.append(record)
            existing_ids.add(tweet_id)
            print(f"  Saved: {analysis.get('direction')} — {analysis.get('tickers')}")

            if kol.get("notify", False):
                send_email_notification(record)

        await asyncio.sleep(2)

    if new_tweets:
        all_tweets = new_tweets + existing_tweets
        all_tweets.sort(key=lambda t: t["published_at"], reverse=True)
        all_tweets = all_tweets[:MAX_TWEETS_STORED]
        save_json(TWEETS_FILE, all_tweets)
        print(f"\nDone — added {len(new_tweets)} new tweet(s), total {len(all_tweets)}")
    else:
        all_tweets = existing_tweets
        print("\nDone — no new investment-related tweets")

    # Regenerate summaries for KOLs that got new tweets
    updated_kols = {t["kol_username"] for t in new_tweets}
    if updated_kols:
        generate_summaries(all_tweets, updated_kols, claude)


def generate_summaries(all_tweets: list, kol_usernames: set, claude: anthropic.Anthropic) -> None:
    summaries = load_json(SUMMARIES_FILE, {})

    for username in kol_usernames:
        kol_tweets = [t for t in all_tweets if t["kol_username"] == username]
        if len(kol_tweets) < MIN_TWEETS_FOR_SUMMARY:
            print(f"  Skipping summary for {username}: only {len(kol_tweets)} tweets")
            continue

        print(f"  Generating summary for @{username} ({len(kol_tweets)} tweets)...")
        tweet_texts = "\n---\n".join(
            f"[{t['published_at'][:10]}] {t['content']}" for t in kol_tweets[:100]
        )

        try:
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=800,
                system="You are a financial analyst. Analyze a collection of tweets and return structured JSON only.",
                messages=[{"role": "user", "content": f"""Analyze these tweets from a stock market influencer and return a JSON summary.

Tweets (most recent first):
{tweet_texts}

Return JSON with exactly these fields:
- focus_tickers: array of top 5 most mentioned ticker symbols
- overall_bias: "bullish" | "bearish" | "neutral" — their general market stance
- key_themes: array of 3-5 Chinese strings describing main investment themes
- recent_shift: one Chinese sentence describing any notable change in recent views vs earlier; empty string if no change
- representative_quotes: array of 2-3 most insightful original tweet excerpts (keep original language)"""}],
            )
            summary = json.loads(response.content[0].text)
            summary["generated_at"] = datetime.now(timezone.utc).isoformat()
            summaries[username] = summary
            print(f"  Summary done: bias={summary.get('overall_bias')}, tickers={summary.get('focus_tickers')}")
        except Exception as exc:
            print(f"  Summary error for {username}: {exc}")

    save_json(SUMMARIES_FILE, summaries)


if __name__ == "__main__":
    asyncio.run(main())
