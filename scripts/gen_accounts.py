"""
Run ONCE locally to add your X account to twscrape and export credentials.
The exported JSON goes into GitHub Secret X_ACCOUNTS.

Usage:
    python3.11 scripts/gen_accounts.py
"""

import asyncio
import json
from twscrape import API


async def main():
    username = input("X username (without @): ").strip()
    email    = input("X email: ").strip()
    password = input("X password: ").strip()

    api = API()
    await api.pool.add_account(username, password, email, password)
    await api.pool.login_all()

    accounts = await api.pool.get_all()
    data = [a.to_rs() for a in accounts]
    out = json.dumps(data, ensure_ascii=False)

    print("\n=== Copy the following JSON into GitHub Secret X_ACCOUNTS ===\n")
    print(out)
    print("\n=== End ===")


if __name__ == "__main__":
    asyncio.run(main())
