"""
Fetch tweets from tracked KOLs via twikit (no API key required),
analyze investment-related content with Claude, and update data/tweets.json.

Auth: uses X_COOKIES env var (JSON string) if set, otherwise falls back to
      X_USERNAME + X_EMAIL + X_PASSWORD. Cookie-based auth is more stable
      for GitHub Actions — see README for how to generate cookies.
"""

import asyncio
import json
import os
import smtplib
import tempfile
from datetime import datetime, timezone
from email.mime.text import MIMEText

import anthropic
from twikit import Client

TWEETS_FILE = "data/tweets.json"
KOLS_FILE = "config/kols.json"
MAX_TWEETS_STORED = 1000
FETCH_COUNT = 20  # tweets per KOL per run


def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def get_x_client() -> Client:
    client = Client("en-US")
    cookies_json = os.environ.get("X_COOKIES")
    if cookies_json:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            tmp.write(cookies_json)
            tmp_path = tmp.name
        client.load_cookies(tmp_path)
        os.unlink(tmp_path)
        print("Loaded auth from X_COOKIES")
    else:
        username = os.environ["X_USERNAME"]
        email = os.environ.get("X_EMAIL", "")
        password = os.environ["X_PASSWORD"]
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password,
        )
        print(f"Logged in as {username}")
    return client


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
- confidence: "high" | "medium" | "low" | null — how clear/confident the recommendation is; null if not investment related"""

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.content[0].text)


DIRECTION_ZH = {"bullish": "🟢 看多", "bearish": "🔴 看空", "neutral": "⚪ 中性"}


def send_email_notification(tweet: dict) -> None:
    """Send email via SMTP. Requires NOTIFY_EMAIL_* env vars."""
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


def parse_created_at(raw: str) -> str:
    """Convert Twitter's date format to ISO 8601."""
    try:
        dt = datetime.strptime(raw, "%a %b %d %H:%M:%S %z %Y")
        return dt.isoformat()
    except (ValueError, TypeError):
        return raw or datetime.now(timezone.utc).isoformat()


async def main() -> None:
    kols = load_json(KOLS_FILE, [])
    existing_tweets: list = load_json(TWEETS_FILE, [])
    existing_ids = {t["tweet_id"] for t in existing_tweets}

    x_client = await get_x_client()
    claude = anthropic.Anthropic()

    new_tweets: list = []

    for kol in kols:
        if not kol.get("enabled", True):
            continue

        username = kol["username"]
        print(f"\nFetching @{username}...")

        try:
            user = await x_client.get_user_by_screen_name(username)
            tweets = await user.get_tweets("Tweets", count=FETCH_COUNT)
        except Exception as exc:
            print(f"  ERROR fetching {username}: {exc}")
            continue

        # Update avatar URL in kol record (best-effort)
        avatar_url = getattr(user, "profile_image_url", "") or kol.get("avatar_url", "")
        # Use higher-res avatar (replace _normal with _400x400)
        avatar_url = avatar_url.replace("_normal", "_400x400")

        for tweet in tweets:
            tweet_id = str(tweet.id)
            if tweet_id in existing_ids:
                continue

            text = tweet.text or ""
            print(f"  Analyzing {tweet_id}: {text[:60]}...")

            try:
                analysis = analyze_tweet(text, claude)
            except Exception as exc:
                print(f"  Analysis error: {exc}")
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
                "published_at": parse_created_at(
                    getattr(tweet, "created_at", None)
                ),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "analysis": analysis,
            }
            new_tweets.append(record)
            existing_ids.add(tweet_id)
            print(f"  Saved: {analysis.get('direction')} — {analysis.get('tickers')}")

            if kol.get("notify", False):
                send_email_notification(record)

        await asyncio.sleep(2)  # be polite between users

    if new_tweets:
        all_tweets = new_tweets + existing_tweets
        all_tweets = all_tweets[:MAX_TWEETS_STORED]
        save_json(TWEETS_FILE, all_tweets)
        print(f"\nDone — added {len(new_tweets)} new tweet(s), total {len(all_tweets)}")
    else:
        print("\nDone — no new investment-related tweets")


if __name__ == "__main__":
    asyncio.run(main())
