from __future__ import annotations

import discord
from discord.ext import commands

from utils.config import del_verify_config, reset_prefix


class GuildRemoveEvent(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        del_verify_config(guild.id)
        reset_prefix(guild.id)
        print(f"  [leave] cleaned config for {guild.name} ({guild.id})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildRemoveEvent(bot))
