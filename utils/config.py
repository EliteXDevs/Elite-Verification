from __future__ import annotations

import json
import os
from typing import Optional

from discord.ext.commands import when_mentioned_or

# ──────────────────────────────────────────────────────────────
_PATH = "data/config.json"
DEFAULT_PREFIX = "!"


def _load() -> dict:
    try:
        with open(_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ──────────────────────────────────────────────────────────────
#  Prefix helpers
# ──────────────────────────────────────────────────────────────

def get_prefix(bot, message):
    """Dynamic prefix callable — supports both guild prefix and @mention."""
    if not message.guild:
        prefix = DEFAULT_PREFIX
    else:
        prefix = _load().get("prefixes", {}).get(str(message.guild.id), DEFAULT_PREFIX)
    return when_mentioned_or(prefix)(bot, message)


def guild_prefix(guild_id: int) -> str:
    """Return the current prefix for a guild (for display)."""
    return _load().get("prefixes", {}).get(str(guild_id), DEFAULT_PREFIX)


def set_prefix(guild_id: int, prefix: str) -> None:
    data = _load()
    data.setdefault("prefixes", {})[str(guild_id)] = prefix
    _save(data)


def reset_prefix(guild_id: int) -> None:
    data = _load()
    data.get("prefixes", {}).pop(str(guild_id), None)
    _save(data)


# ──────────────────────────────────────────────────────────────
#  Verification config helpers
# ──────────────────────────────────────────────────────────────

def get_verify_config(guild_id: int) -> dict:
    return _load().get("verify", {}).get(str(guild_id), {})


def set_verify_config(guild_id: int, cfg: dict) -> None:
    data = _load()
    data.setdefault("verify", {})[str(guild_id)] = cfg
    _save(data)


def del_verify_config(guild_id: int) -> None:
    data = _load()
    data.get("verify", {}).pop(str(guild_id), None)
    _save(data)
