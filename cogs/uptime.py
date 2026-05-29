import datetime

import discord
from discord.ext import commands


class Uptime(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()

    @commands.command(name="uptime", aliases=["up"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def uptime(self, ctx: commands.Context) -> None:
        """Check how long the bot has been online."""
        delta         = datetime.datetime.utcnow() - self.start_time
        total_seconds = int(delta.total_seconds())

        days    = total_seconds // 86400
        hours   = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        parts = []
        if days:
            parts.append(f"`{days}d`")
        if hours:
            parts.append(f"`{hours}h`")
        if minutes:
            parts.append(f"`{minutes}m`")
        parts.append(f"`{seconds}s`")

        uptime_str  = "  ".join(parts)
        started_ts  = int(self.start_time.replace(tzinfo=datetime.timezone.utc).timestamp())
        started_str = f"<t:{started_ts}:R>"

        view      = discord.ui.LayoutView()
        container = discord.ui.Container(discord.ui.TextDisplay("## ⏱️  Uptime"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"> **Duration** : {uptime_str}\n"
            f"> **Started**  : {started_str}"
        ))
        view.add_item(container)

        await ctx.send(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Uptime(bot))