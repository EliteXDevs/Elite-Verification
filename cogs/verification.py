from __future__ import annotations

import operator
import random
import string
from io import BytesIO
from typing import Optional

import discord
from discord import ui
from discord.ext import commands
from discord.ui import (
    ActionRow,
    Container,
    LayoutView,
    MediaGallery,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)

from utils.config import del_verify_config, get_verify_config, set_verify_config

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    _PIL = True
except ImportError:
    _PIL = False

# ──────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────

_METHODS  = ("button", "math", "captcha")
_ROLE_CLR = discord.Color.from_str("#5865F2")

# ──────────────────────────────────────────────────────────────
#  Captcha image generator
# ──────────────────────────────────────────────────────────────

def _make_captcha(text: str) -> BytesIO:
    if not _PIL:
        raise RuntimeError("Pillow is not installed — run: pip install Pillow")

    W, H = 300, 100
    img  = Image.new("RGB", (W, H), (12, 12, 20))
    draw = ImageDraw.Draw(img)

    # background noise dots
    for _ in range(500):
        draw.point(
            (random.randint(0, W), random.randint(0, H)),
            fill=(random.randint(30, 70), random.randint(30, 70), random.randint(50, 100)),
        )

    # distraction lines
    for _ in range(10):
        draw.line(
            [(random.randint(0, W), random.randint(0, H)),
             (random.randint(0, W), random.randint(0, H))],
            fill=(random.randint(40, 80), 55, random.randint(80, 140)),
            width=1,
        )

    try:
        fnt = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44
        )
    except Exception:
        fnt = ImageFont.load_default()

    x = 16
    for ch in text:
        col = (
            random.randint(180, 255),
            random.randint(180, 255),
            random.randint(210, 255),
        )
        draw.text((x, random.randint(10, 28)), ch, font=fnt, fill=col)
        x += random.randint(38, 46)

    img = img.filter(ImageFilter.SMOOTH)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf

# ──────────────────────────────────────────────────────────────
#  Shared helpers
# ──────────────────────────────────────────────────────────────

def _reply(heading: str, body: str) -> LayoutView:
    """One-container LayoutView for quick ephemeral responses."""
    v = LayoutView()
    v.add_item(Container(TextDisplay(heading), Separator(), TextDisplay(body)))
    return v


async def _add_role(interaction: discord.Interaction, role: discord.Role, reason: str) -> bool:
    try:
        await interaction.user.add_roles(role, reason=reason)
        return True
    except discord.Forbidden:
        return False


async def _resolve_role(interaction: discord.Interaction) -> discord.Role | None:
    """Pull the verified role for this guild from config at click time."""
    cfg = get_verify_config(interaction.guild_id)
    return interaction.guild.get_role(cfg.get("role_id", 0))


async def _ensure_role(guild: discord.Guild) -> discord.Role:
    """Return the existing 'Verified' role or create one below the bot's top role."""
    existing = discord.utils.get(guild.roles, name="Verified")
    if existing:
        return existing

    role = await guild.create_role(
        name="Verified",
        color=_ROLE_CLR,
        reason="Auto-created by verification system",
    )
    try:
        top = max(
            (r.position for r in guild.me.roles if not r.is_default()),
            default=1,
        )
        await role.edit(position=max(1, top - 1))
    except discord.HTTPException:
        pass

    return role

# ──────────────────────────────────────────────────────────────
#  Modal  (captcha answer)
# ──────────────────────────────────────────────────────────────

class _CaptchaModal(ui.Modal, title="Enter the Code"):
    answer: ui.TextInput = ui.TextInput(
        label="Type the code shown in the image",
        placeholder="e.g. A3K9FW",
        min_length=1,
        max_length=8,
        style=discord.TextStyle.short,
    )

    def __init__(self, correct: str, role: discord.Role) -> None:
        super().__init__()
        self._correct = correct.upper()
        self._role    = role

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.answer.value.strip().upper() != self._correct:
            await interaction.response.send_message(
                view=_reply(
                    "# ❌  Wrong Code",
                    "That code was incorrect. Click **Get Captcha** again to retry.",
                ),
                ephemeral=True,
            )
            return

        ok = await _add_role(interaction, self._role, "Verification: captcha")
        v  = (
            _reply("# ✅  Verified", f"Correct! You've been granted **{self._role.name}**. Welcome!")
            if ok else
            _reply("# ❌  Error", "Couldn't assign the role — contact an admin.")
        )
        await interaction.response.send_message(view=v, ephemeral=True)

# ──────────────────────────────────────────────────────────────
#  Ephemeral challenge views  (fresh per user, per attempt)
# ──────────────────────────────────────────────────────────────

def _math_btn_cb(val: int, correct: int, role: discord.Role):
    """Factory — keeps val/correct/role correctly bound per button."""
    async def callback(interaction: discord.Interaction) -> None:
        if val != correct:
            await interaction.response.edit_message(
                view=_reply("# ❌  Wrong", "Incorrect. Click **Start Math Verification** to try again.")
            )
            return

        ok = await _add_role(interaction, role, "Verification: math")
        v  = (
            _reply("# ✅  Correct!", f"**{correct}** — you've been granted **{role.name}**. Welcome!")
            if ok else
            _reply("# ❌  Error", "Couldn't assign the role — contact an admin.")
        )
        await interaction.response.edit_message(view=v)

    return callback


class _MathChallenge(LayoutView):
    """Ephemeral: random equation with 4 answer buttons."""

    def __init__(self, role: discord.Role) -> None:
        super().__init__(timeout=60)

        a   = random.randint(2, 20)
        b   = random.randint(2, 20)
        sym, fn = random.choice(
            [("+", operator.add), ("−", operator.sub), ("×", operator.mul)]
        )
        if sym == "×":
            a, b = random.randint(2, 12), random.randint(2, 12)

        correct = fn(a, b)

        wrongs: set[int] = set()
        while len(wrongs) < 3:
            w = correct + random.choice([-1, 1]) * random.randint(1, 9)
            if w != correct:
                wrongs.add(w)

        choices = [correct, *wrongs]
        random.shuffle(choices)

        btns = []
        for val in choices:
            btn = ui.Button(label=str(val), style=discord.ButtonStyle.secondary)
            btn.callback = _math_btn_cb(val, correct, role)
            btns.append(btn)

        self.add_item(Container(
            TextDisplay("# 🔢  Math Challenge"),
            Separator(),
            TextDisplay(f"Solve this to verify:\n\n## `{a} {sym} {b} = ?`"),
            Separator(),
            ActionRow(*btns),
        ))


class _CaptchaChallenge(LayoutView):
    """Ephemeral: MediaGallery renders the image, button opens the answer modal."""

    def __init__(self, role: discord.Role, code: str) -> None:
        super().__init__(timeout=120)

        btn = ui.Button(label="Enter Code", style=discord.ButtonStyle.primary, emoji="🔡")

        async def _open_modal(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_CaptchaModal(code, role))

        btn.callback = _open_modal

        # add_item(media=...) is the correct CV2 API — no MediaGalleryItem class needed.
        # The filename MUST match the one passed to discord.File(buf, "captcha.png").
        gallery = MediaGallery()
        gallery.add_item(media="attachment://captcha.png")

        self.add_item(Container(
            TextDisplay("# 🖼️  Captcha Verification"),
            Separator(),
            gallery,
            Separator(),
            TextDisplay(
                "Type the **6-character code** shown above.\n"
                "-# Case-insensitive · Expires in 2 minutes"
            ),
            Separator(),
            ActionRow(btn),
        ))

# ──────────────────────────────────────────────────────────────
#  Persistent panel views
#
#  Fixed custom_id per method → one bot.add_view() covers all guilds.
#  Role is looked up from config at click time, not stored in the view.
# ──────────────────────────────────────────────────────────────

class _ButtonPanel(LayoutView):
    def __init__(self, *, icon_url: str = "") -> None:
        super().__init__(timeout=None)

        btn = ui.Button(
            label="Verify Me",
            style=discord.ButtonStyle.success,
            emoji="✅",
            custom_id="ver:button",
        )
        btn.callback = self._on_click

        inner = TextDisplay(
            "# 🔐  Verification Required\n"
            "> Click the button below to verify and gain access to the server."
        )

        # Thumbnail only on first post; re-registration doesn't re-render the message.
        if icon_url:
            block = Section(
                inner,
                accessory=Thumbnail(
                    media=discord.UnfurledMediaItem(url=icon_url),
                    description="Verify",
                ),
                id=1,
            )
        else:
            block = inner  # type: ignore[assignment]

        self.add_item(Container(block, Separator(), ActionRow(btn)))

    async def _on_click(self, interaction: discord.Interaction) -> None:
        role = await _resolve_role(interaction)
        if not role:
            await interaction.response.send_message(
                "⚠️ Verified role not found — contact an admin.", ephemeral=True
            )
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You're already verified!", ephemeral=True)
            return

        ok = await _add_role(interaction, role, "Verification: button")
        v  = (
            _reply("# ✅  Verified!", f"You've been granted **{role.name}**. Welcome!")
            if ok else
            _reply("# ❌  Error", "Couldn't assign the role — contact an admin.")
        )
        await interaction.response.send_message(view=v, ephemeral=True)


class _MathPanel(LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

        btn = ui.Button(
            label="Start Math Verification",
            style=discord.ButtonStyle.primary,
            emoji="🔢",
            custom_id="ver:math",
        )
        btn.callback = self._on_click

        self.add_item(Container(
            TextDisplay("# 🔢  Math Verification"),
            Separator(),
            TextDisplay(
                "Solve a quick equation to prove you're human.\n"
                "-# A fresh question is generated for every attempt."
            ),
            Separator(),
            ActionRow(btn),
        ))

    async def _on_click(self, interaction: discord.Interaction) -> None:
        role = await _resolve_role(interaction)
        if not role:
            await interaction.response.send_message(
                "⚠️ Verified role not found — contact an admin.", ephemeral=True
            )
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You're already verified!", ephemeral=True)
            return

        await interaction.response.send_message(view=_MathChallenge(role), ephemeral=True)


class _CaptchaPanel(LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

        btn = ui.Button(
            label="Get Captcha",
            style=discord.ButtonStyle.primary,
            emoji="🖼️",
            custom_id="ver:captcha",
        )
        btn.callback = self._on_click

        self.add_item(Container(
            TextDisplay("# 🖼️  Captcha Verification"),
            Separator(),
            TextDisplay(
                "Click below to receive your personal captcha image.\n"
                "-# A unique code is generated for every attempt."
            ),
            Separator(),
            ActionRow(btn),
        ))

    async def _on_click(self, interaction: discord.Interaction) -> None:
        role = await _resolve_role(interaction)
        if not role:
            await interaction.response.send_message(
                "⚠️ Verified role not found — contact an admin.", ephemeral=True
            )
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You're already verified!", ephemeral=True)
            return

        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        buf  = _make_captcha(code)

        await interaction.response.send_message(
            file=discord.File(buf, "captcha.png"),
            view=_CaptchaChallenge(role, code),
            ephemeral=True,
        )

# ──────────────────────────────────────────────────────────────
#  Panel registry
# ──────────────────────────────────────────────────────────────

_PANELS: dict[str, type[LayoutView]] = {
    "button":  _ButtonPanel,
    "math":    _MathPanel,
    "captcha": _CaptchaPanel,
}

# ──────────────────────────────────────────────────────────────
#  Cog
# ──────────────────────────────────────────────────────────────

class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Re-register all persistent panel views so buttons survive restarts."""
        self.bot.add_view(_ButtonPanel())
        self.bot.add_view(_MathPanel())
        self.bot.add_view(_CaptchaPanel())

    # ── internal ──────────────────────────────────────────────

    async def _post_panel(self, channel: discord.TextChannel, method: str) -> None:
        if method == "button":
            await channel.send(view=_ButtonPanel(icon_url=self.bot.user.display_avatar.url))
        else:
            await channel.send(view=_PANELS[method]())

    # ── command group ─────────────────────────────────────────

    @commands.group(name="verification", aliases=["ver"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def ver(self, ctx: commands.Context) -> None:
        """Show the current verification config for this server."""
        cfg = get_verify_config(ctx.guild.id)

        if not cfg:
            body = (
                "No verification configured for this server.\n\n"
                f"**Available methods:** `{'` · `'.join(_METHODS)}`\n"
                "**Usage:** `ver setup <method> [role] [#channel]`\n"
                "-# Role is optional — auto-created if omitted."
            )
        else:
            rid = cfg.get("role_id")
            cid = cfg.get("channel_id")
            body = (
                f"**Method:** `{cfg.get('method')}`\n"
                f"**Role:** <@&{rid}>\n"
                f"**Channel:** {'<#' + str(cid) + '>' if cid else 'not set'}"
            )

        await ctx.send(view=_reply("# ⚙️  Verification", body))

    # ── setup ─────────────────────────────────────────────────

    @ver.command(name="setup")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def ver_setup(
        self,
        ctx: commands.Context,
        method: str,
        role: Optional[discord.Role] = None,
        channel: Optional[discord.TextChannel] = None,
    ) -> None:
        """Configure verification and post the panel.

        Usage   : ver setup <method> [role] [#channel]
        Methods : button · math · captcha
        """
        method = method.lower()
        if method not in _METHODS:
            await ctx.send(view=_reply(
                "# ❌  Unknown Method",
                f"Valid methods: `{'` · `'.join(_METHODS)}`",
            ))
            return

        ch = channel or ctx.channel

        # Auto-create role if not supplied
        auto_note = ""
        if role is None:
            async with ctx.typing():
                role = await _ensure_role(ctx.guild)
            auto_note = " *(auto-created)*"

        set_verify_config(ctx.guild.id, {
            "method":     method,
            "role_id":    role.id,
            "channel_id": ch.id,
        })

        await self._post_panel(ch, method)

        await ctx.send(view=_reply(
            "# ✅  Verification Enabled",
            f"**Method:** `{method}`\n"
            f"**Role:** {role.mention}{auto_note}\n"
            f"**Channel:** {ch.mention}",
        ))

    # ── reset ─────────────────────────────────────────────────

    @ver.command(name="reset")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def ver_reset(self, ctx: commands.Context) -> None:
        """Disable verification for this server."""
        del_verify_config(ctx.guild.id)
        await ctx.send(view=_reply(
            "# 🗑️  Verification Cleared",
            "Verification has been disabled for this server.",
        ))

    # ── error handler ─────────────────────────────────────────

    @ver.error
    @ver_setup.error
    @ver_reset.error
    async def _on_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(view=_reply(
                "# 🚫  No Permission",
                "You need **Administrator** to manage verification.",
            ))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(view=_reply("# ❌  Bad Argument", str(error)))
        else:
            raise error


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Verification(bot))