import sys
import psutil
import discord
from discord.ext import commands

class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="stats", aliases=["botinfo", "bi"])
    async def stats_command(self, ctx: commands.Context) -> None:
        memory = psutil.Process().memory_info()
        mem_usage = memory.rss / 1024 / 1024

        view = discord.ui.LayoutView()
        container = discord.ui.Container()

        container.add_item(discord.ui.TextDisplay(
            "## Bot Statistics\n"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"**Servers** : {len(self.bot.guilds)}\n"
            f"**Users** : {len(self.bot.users)}\n"
            f"**Latency** : {round(self.bot.latency * 1000)}ms\n"
            f"**Memory** : {mem_usage:.2f} MB\n"
            f"**Library** : discord.py v{discord.__version__}\n"
            f"**Python** : v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ))

        view.add_item(container)
        await ctx.send(view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Stats(bot))