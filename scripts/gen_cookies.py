"""
Run this script ONCE locally to generate X session cookies.
Then paste the output into GitHub Secrets as X_COOKIES.

Usage:
    pip install twikit
    python scripts/gen_cookies.py
"""

import asyncio
import json
from twikit import Client


async def main():
    username = input("X username (without @): ").strip()
    email = input("X email: ").strip()
    password = input("X password: ").strip()

    client = Client("en-US")
    await client.login(auth_info_1=username, auth_info_2=email, password=password)

    import tempfile, os
    tmp = tempfile.mktemp(suffix=".json")
    client.save_cookies(tmp)
    with open(tmp) as f:
        cookies = f.read()
    os.unlink(tmp)

    print("\n=== Copy the following JSON into GitHub Secret X_COOKIES ===\n")
    print(cookies)
    print("\n=== End ===")


if __name__ == "__main__":
    asyncio.run(main())
