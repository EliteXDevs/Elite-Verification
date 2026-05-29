from __future__ import annotations

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.config import get_prefix

load_dotenv()

# ──────────────────────────────────────────────────────────────
#  Intents
# ──────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # prefix commands
intents.members = True          
intents.presences = True        

# ──────────────────────────────────────────────────────────────
#  Bot
# ──────────────────────────────────────────────────────────────
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None,
    case_insensitive=True,
)

# ──────────────────────────────────────────────────────────────
#  Extension loader
# ──────────────────────────────────────────────────────────────
async def _load_folder(folder: str) -> tuple[int, int]:
    """Load every non-dunder .py in *folder* as a discord.py extension.
    Returns (loaded, failed) counts."""
    ok = fail = 0
    if not os.path.isdir(folder):
        print(f"  [skip] {folder}/ not found")
        return ok, fail

    for name in sorted(os.listdir(folder)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        ext = f"{folder}.{name[:-3]}"
        try:
            await bot.load_extension(ext)
            print(f"  ✓  {ext}")
            ok += 1
        except Exception as exc:
            print(f"  ✗  {ext}  →  {exc}")
            fail += 1

    return ok, fail


# ──────────────────────────────────────────────────────────────
#  Entry
# ──────────────────────────────────────────────────────────────
async def main() -> None:
    token = os.getenv("TOKEN")
    if not token:
        raise SystemExit("ERROR: TOKEN is not set in .env")

    async with bot:
        print("\n── Cogs ───────────────────────────────")
        c_ok, c_fail = await _load_folder("cogs")

        print("\n── Events ─────────────────────────────")
        e_ok, e_fail = await _load_folder("events")

        total = c_ok + e_ok
        total_fail = c_fail + e_fail
        print(f"\n  Loaded {total} extension(s)  |  {total_fail} failed\n")

        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
