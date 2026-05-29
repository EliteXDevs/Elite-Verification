"""
cogs/prefix.py — Per-guild prefix management (CV2)
Commands: setprefix · resetprefix · prefix
"""
from __future__ import annotations

import discord
from discord.ext import commands
from discord.ui import Container, LayoutView, Section, Separator, TextDisplay, Thumbnail

from utils.config import DEFAULT_PREFIX, guild_prefix, reset_prefix, set_prefix

# ──────────────────────────────────────────────────────────────
#  Shared UI helper
# ──────────────────────────────────────────────────────────────

def _panel(heading: str, body: str, *, bot_avatar: str | None = None) -> LayoutView:
    v = LayoutView()
    if bot_avatar:
        v.add_item(Container(
            Section(
                TextDisplay(f"{heading}\n{body}"),
                accessory=Thumbnail(
                    media=discord.UnfurledMediaItem(url=bot_avatar),
                    description="Bot",
                ),
                id=1,
            ),
        ))
    else:
        v.add_item(Container(TextDisplay(heading), Separator(), TextDisplay(body)))
    return v


# ──────────────────────────────────────────────────────────────
#  Cog
# ──────────────────────────────────────────────────────────────

class Prefix(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── setprefix ────────────────────────────────────────────

    @commands.command(name="setprefix", aliases=["sp"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setprefix(self, ctx: commands.Context, prefix: str) -> None:
        """Set a custom command prefix for this server.

        Usage: setprefix <prefix>
        """
        if len(prefix) > 5:
            await ctx.send(view=_panel(
                "# ❌  Too Long",
                "Prefix must be **5 characters or fewer**.",
            ))
            return

        set_prefix(ctx.guild.id, prefix)
        await ctx.send(view=_panel(
            "# ✅  Prefix Updated",
            f"Prefix set to **`{prefix}`**\n"
            f"-# You can also always use {self.bot.user.mention}",
        ))

    # ── resetprefix ──────────────────────────────────────────

    @commands.command(name="resetprefix", aliases=["rp"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def resetprefix(self, ctx: commands.Context) -> None:
        """Reset the prefix back to the default."""
        reset_prefix(ctx.guild.id)
        await ctx.send(view=_panel(
            "# 🔄  Prefix Reset",
            f"Prefix restored to **`{DEFAULT_PREFIX}`**",
        ))

    # ── prefix (info) ────────────────────────────────────────

    @commands.command(name="prefix")
    @commands.guild_only()
    async def prefix_info(self, ctx: commands.Context) -> None:
        """Show the current prefix for this server."""
        p = guild_prefix(ctx.guild.id)
        await ctx.send(view=_panel(
            "# ℹ️  Prefix",
            f"Current prefix: **`{p}`**\n"
            f"-# Mention also works: {self.bot.user.mention} `<command>`",
            bot_avatar=self.bot.user.display_avatar.url,
        ))

    # ── error handlers ───────────────────────────────────────

    @setprefix.error
    async def _setprefix_err(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(view=_panel("# 🚫  No Permission", "You need **Administrator** to change the prefix."))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(view=_panel("# ❌  Missing Argument", f"Usage: `{guild_prefix(ctx.guild.id)}setprefix <new_prefix>`"))
        else:
            raise error

    @resetprefix.error
    async def _resetprefix_err(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(view=_panel("# 🚫  No Permission", "You need **Administrator** to reset the prefix."))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Prefix(bot))
