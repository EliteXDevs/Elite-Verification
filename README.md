# Verification Bot

Multi-method Discord verification bot built with **discord.py** and **Components V2**.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp example.env .env
# edit .env → paste your bot token

# 3. Run
python main.py
```

---

## Privileged Intents Required

Enable all three in the [Developer Portal](https://discord.com/developers/applications) under **Bot → Privileged Gateway Intents**:

| Intent | Required for |
|---|---|
| **Message Content** | Prefix commands |
| **Server Members** | Stats Cmds/Total Bot Users|
| **Presence** | Activity/status |

---

## Commands

### Prefix
| Command | Description |
|---|---|
| `setprefix <prefix>` | Set a custom prefix (max 5 chars) |
| `resetprefix` | Reset prefix to `!` |
| `prefix` | Show current prefix |

### Verification
| Command | Description |
|---|---|
| `ver setup <method> [role] [#channel]` | Configure & post the panel |
| `ver reset` | Disable verification |
| `ver` | Show current config |

`role` is **optional** — if omitted a `Verified` role is auto-created and positioned correctly.

### Methods

| Method | How it works |
|---|---|
| `button` | One-click verify button |
| `math` | Solve a random equation (4 choices) |
| `captcha` | Solve a PIL-generated image code via modal |

---

## Project Structure

```
bot/
├── main.py               ← entry point, auto-loads cogs/ & events/
├── .env                  ← TOKEN (gitignored)
├── requirements.txt
├── data/
│   └── config.json       ← auto-created; stores prefixes + verify config
├── utils/
│   └── config.py         ← unified JSON config helpers
├── cogs/
│   ├── prefix.py         ← setprefix / resetprefix / prefix
│   └── verification.py   ← all 3 verify methods + removal listeners
│   └── ping              ← Ping of bot
│   └── uptime            ← Uptime of bot
│   └── help              ← Help command for users
│   └── stats             ← Bot Statistics
└── events/
    ├── ready.py          ← on_ready: status + console summary
    ├── mention.py        ← bare @mention → helpful CV2 panel
    └── guild_remove.py   ← cleanup config on guild leave
```
