"""
Inject browser cookies into twscrape account (bypasses OAuth login).
Use this when your X account was created via Google/Apple Sign In.

Reads cookies.json (auth_token + ct0) and exports account JSON for GitHub Secret X_ACCOUNTS.

Usage:
    python3.11 scripts/inject_cookies.py
"""

import asyncio
import json
from twscrape import API


async def main():
    with open("cookies.json") as f:
        cookies = json.load(f)

    auth_token = cookies.get("auth_token", "")
    ct0 = cookies.get("ct0", "")
    if not auth_token or not ct0:
        print("ERROR: cookies.json must contain auth_token and ct0")
        return

    api = API()
    await api.pool.add_account(
        username="x_user",
        password="placeholder",
        email="placeholder@example.com",
        email_password="placeholder",
        cookies=json.dumps({"auth_token": auth_token, "ct0": ct0}),
    )

    # Mark account as active (skip login)
    acc = await api.pool.get("x_user")
    acc.active = True
    await api.pool.save(acc)

    # Test
    print("Testing cookie auth...")
    user = await api.user_by_login("unusual_whales")
    if user:
        print(f"OK: logged in, fetched user '{user.username}'")
    else:
        print("ERROR: could not fetch user, cookies may be invalid")
        return

    # Export
    accounts = await api.pool.get_all()
    data = [a.to_rs() for a in accounts]
    out = json.dumps(data, ensure_ascii=False)

    print("\n=== Copy the following JSON into GitHub Secret X_ACCOUNTS ===\n")
    print(out)
    print("\n=== End ===")


if __name__ == "__main__":
    asyncio.run(main())
