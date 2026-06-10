"""
One-time script to backfill up to 1 year of historical tweets for all enabled KOLs.
Run locally or trigger via workflow_dispatch with INPUT_HISTORY=true.

Writes to data/tweets.json (same format as fetch_and_analyze.py, deduplicates by tweet_id).
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta

from openai import OpenAI
from twscrape import API

TWEETS_FILE = "data/tweets.json"
KOLS_FILE = "config/kols.json"
MAX_TWEETS_STORED = 5000  # larger cap for history
ONE_YEAR_AGO = datetime.now(timezone.utc) - timedelta(days=365)


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
        raise RuntimeError("X_ACCOUNTS env var is not set.")
    accounts = json.loads(accounts_json)
    for acc in accounts:
        await api.pool.add_account(
            username=acc["username"],
            password=acc["password"],
            email=acc["email"],
            email_password=acc.get("email_password", acc["password"]),
            cookies=acc.get("cookies"),
        )
    return api


def analyze_tweet(text: str, client: OpenAI) -> dict:
    prompt = f"""Analyze this tweet for investment relevance.

Tweet: {text}

Return a JSON object with exactly these fields:
- is_investment_related: boolean
- tickers: array of ticker symbols (e.g. ["NVDA", "BTC"]), empty if none
- direction: "bullish" | "bearish" | "neutral" | null
- summary: 1-3 sentence Chinese summary | null if not investment related
- confidence: "high" | "medium" | "low" | null

Return JSON only, no markdown."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=400,
        messages=[
            {"role": "system", "content": "You are a financial analyst assistant. Return structured JSON only — no markdown, no extra text."},
            {"role": "user", "content": prompt},
        ],
    )
    return json.loads(response.choices[0].message.content)


async def fetch_kol_history(api: API, username: str, existing_ids: set, limit: int = 500) -> list:
    """Fetch up to `limit` tweets from the past year for a single KOL."""
    results = []
    try:
        user = await api.user_by_login(username)
        if not user:
            print(f"  User not found: {username}")
            return []
        async for tweet in api.user_tweets(user.id, limit=limit):
            if not tweet.date:
                continue
            tweet_date = tweet.date.replace(tzinfo=timezone.utc) if tweet.date.tzinfo is None else tweet.date
            if tweet_date < ONE_YEAR_AGO:
                print(f"  Reached tweets older than 1 year, stopping")
                break
            tweet_id = str(tweet.id)
            if tweet_id in existing_ids:
                continue
            results.append((tweet, getattr(user, "profileImageUrl", "") or ""))
    except Exception as exc:
        print(f"  ERROR: {exc}")
    return results


async def main() -> None:
    kols = load_json(KOLS_FILE, [])
    existing_tweets: list = load_json(TWEETS_FILE, [])
    existing_ids = {t["tweet_id"] for t in existing_tweets}

    api = await get_api()
    client = OpenAI(
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )

    new_tweets: list = []

    for kol in kols:
        if not kol.get("enabled", True):
            continue

        username = kol["username"]
        print(f"\nFetching history for @{username}...")

        tweet_tuples = await fetch_kol_history(api, username, existing_ids)
        print(f"  Found {len(tweet_tuples)} new tweets in past year")

        avatar_url = ""
        for tweet, raw_avatar in tweet_tuples:
            if raw_avatar and not avatar_url:
                avatar_url = raw_avatar.replace("_normal", "_400x400")

            tweet_id = str(tweet.id)
            text = tweet.rawContent or ""

            try:
                analysis = analyze_tweet(text, client)
            except Exception as exc:
                print(f"  Analysis error [{type(exc).__name__}]: {exc}")
                continue

            if not analysis.get("is_investment_related"):
                continue

            tweet_date = tweet.date.replace(tzinfo=timezone.utc) if tweet.date and tweet.date.tzinfo is None else tweet.date

            new_tweets.append({
                "tweet_id": tweet_id,
                "kol_username": username,
                "kol_display_name": kol.get("display_name", username),
                "kol_avatar_url": avatar_url,
                "kol_focus": kol.get("focus", ""),
                "content": text,
                "tweet_url": f"https://x.com/{username}/status/{tweet_id}",
                "published_at": tweet_date.isoformat() if tweet_date else datetime.now(timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "analysis": analysis,
            })
            existing_ids.add(tweet_id)

        print(f"  Kept {sum(1 for t in new_tweets if t['kol_username'] == username)} investment tweets")
        await asyncio.sleep(3)

    if new_tweets:
        # Merge and sort by published_at descending
        all_tweets = new_tweets + existing_tweets
        all_tweets.sort(key=lambda t: t["published_at"], reverse=True)
        all_tweets = all_tweets[:MAX_TWEETS_STORED]
        save_json(TWEETS_FILE, all_tweets)
        print(f"\nDone — added {len(new_tweets)} historical tweets, total {len(all_tweets)}")
    else:
        print("\nDone — no new investment-related historical tweets")


if __name__ == "__main__":
    asyncio.run(main())
