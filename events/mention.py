from __future__ import annotations

import discord
from discord.ext import commands
from discord.ui import (
    ActionRow,
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)

from utils.config import guild_prefix


class MentionEvent(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        # only act on a bare mention (nothing else after the ping)
        is_mention = (
            message.content.strip() in (
                f"<@{self.bot.user.id}>",
                f"<@!{self.bot.user.id}>",
            )
        )
        if not is_mention:
            return

        prefix  = guild_prefix(message.guild.id)
        latency = round(self.bot.latency * 1000)

        view = LayoutView()
        view.add_item(Container(
            Section(
                TextDisplay(
                    f"# Hey, {message.author.display_name}! 👋\n"
                    f"> Prefix here is **`{prefix}`**\n"
                    f"> Run **`{prefix}ver setup`** to configure verification.\n"
                    f"> Run **`{prefix}setprefix`** to change the prefix.\n"
                    f"> Run **`{prefix}help`** to see all bot cmds."
                ),
                accessory=Thumbnail(
                    media=discord.UnfurledMediaItem(
                        url=self.bot.user.display_avatar.url
                    ),
                    description="Bot avatar",
                ),
                id=1,
            ),
            Separator(),
            TextDisplay(f"-# Latency: **{latency} ms** · {len(self.bot.guilds)} servers"),
        ))

        await message.reply(view=view, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MentionEvent(bot))
