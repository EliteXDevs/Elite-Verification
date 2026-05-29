
from __future__ import annotations

import discord
from discord.ext import commands


class ReadyEvent(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.bot.guilds)} servers",
            ),
        )

        guilds  = len(self.bot.guilds)
        users   = sum(g.member_count or 0 for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)

        print(
            f"{'─' * 44}\n"
            f"  Bot      {self.bot.user}  ({self.bot.user.id})\n"
            f"  Guilds   {guilds}\n"
            f"  Users    {users}\n"
            f"  Latency  {latency} ms\n"
            f"{'─' * 44}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReadyEvent(bot))
