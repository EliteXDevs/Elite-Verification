import time

import discord
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ping", aliases=["latency", "pong"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx: commands.Context) -> None:
        """Check the bot's latency."""
        start = time.perf_counter()
        msg   = await ctx.send("Pinging...")
        end   = time.perf_counter()

        ws_latency  = round(self.bot.latency * 1000)
        msg_latency = round((end - start) * 1000)

        def indicator(ms: int) -> str:
            if ms < 100:
                return "🟢"
            elif ms < 200:
                return "🟡"
            return "🔴"

        view      = discord.ui.LayoutView()
        container = discord.ui.Container(discord.ui.TextDisplay("## 🏓  Pong!"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            f"> {indicator(ws_latency)}  **Websocket** : `{ws_latency}ms`\n"
            f"> {indicator(msg_latency)}  **Response**  : `{msg_latency}ms`"
        ))
        view.add_item(container)

        await msg.edit(content=None, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))