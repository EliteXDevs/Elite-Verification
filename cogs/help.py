import discord
from discord.ext import commands

class HelpMenuView(discord.ui.LayoutView):
    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.author = ctx.author
        self.message = None
        self._build_home()

    def _clear(self):
        self.clear_items()

    def _build_home(self):
        self._clear()
        container = discord.ui.Container()
        
        container.add_item(discord.ui.TextDisplay(
            "## Help Menu"
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            "> Hey there, I am your favourite verification bot. Wanna know my commands and how to use them? Choose a category from the dropdown to see what cool feature I have."
        ))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(
            "**Important Links:**\n"
            "> [Invite me](https://yourinviteurl.com)\n"
            "> [Support Server](https://discord.gg/MgCEx8aHUk)"
        ))
        container.add_item(discord.ui.Separator())
        select_menu = discord.ui.Select(
            placeholder="Select a category...",
            custom_id="help_select",
            options=[
                discord.SelectOption(label="General", value="general"),
                discord.SelectOption(label="Verification", value="verification")
            ]
        )
        select_menu.callback = self.on_select_change
        container.add_item(discord.ui.ActionRow(select_menu))
        
        self.add_item(container)

    def _build_category(self, category):
        self._clear()
        container = discord.ui.Container()

        if category == "general":
            container.add_item(discord.ui.TextDisplay(
                "## General Commands"
            ))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(
                "`help` : Shows this menu.\n"
                "`stats` : View bot statistics.\n"
                "`ping` : Check the bot's latency.\n"
                "`uptime` : See how long the bot has been online.\n"
                "`prefix` : Change or view the bot prefix."
            ))
        elif category == "verification":
            container.add_item(discord.ui.TextDisplay(
                "## Verification Commands\n"
            ))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(
                "## Verification Commands\n"
                "`verification setup` : Configure the server verification system.\n"
                "`verification reset` : Reset verification settings to default."
            ))

        container.add_item(discord.ui.Separator())

        select_menu = discord.ui.Select(
            placeholder="Select a category...",
            custom_id="help_select",
            options=[
                discord.SelectOption(label="General", value="general"),
                discord.SelectOption(label="Verification", value="verification")
            ]
        )
        select_menu.callback = self.on_select_change
        container.add_item(discord.ui.ActionRow(select_menu))

        home_btn = discord.ui.Button(label="Home", style=discord.ButtonStyle.secondary, custom_id="home_btn")
        home_btn.callback = self.on_home_click
        container.add_item(discord.ui.ActionRow(home_btn))

        self.add_item(container)

    async def on_select_change(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This menu is not for you.", ephemeral=True)
        
        value = interaction.data['values'][0]
        self._build_category(value)
        await interaction.response.edit_message(view=self)

    async def on_home_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            
        self._build_home()
        await interaction.response.edit_message(view=self)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        view = HelpMenuView(ctx)
        view.message = await ctx.send(view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))