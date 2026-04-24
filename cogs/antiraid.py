import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os

def get_color():
    if os.path.exists("theme.json"):
        with open("theme.json", "r") as f:
            return json.load(f).get("color", 0x9B59B6)
    return 0x9B59B6

ROUGE = 0xE74C3C
VERT = 0x2ECC71

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_tracker = defaultdict(list)   # guild_id → [timestamps]
        self.spam_tracker = defaultdict(list)   # user_id → [timestamps]
        self.RAID_THRESHOLD = 10   # membres en
        self.RAID_WINDOW = 10      # secondes
        self.SPAM_THRESHOLD = 5   # messages en
        self.SPAM_WINDOW = 5       # secondes

    def get_log_channel(self, guild):
        for ch in guild.text_channels:
            if "log" in ch.name.lower():
                return ch
        return None

    async def log_action(self, guild, title, description, color=ROUGE):
        ch = self.get_log_channel(guild)
        if not ch:
            return
        e = discord.Embed(
            title=f"✦  {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text="⬡ Anti-Raid")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        now = datetime.utcnow()
        self.join_tracker[guild.id].append(now)
        self.join_tracker[guild.id] = [
            t for t in self.join_tracker[guild.id]
            if now - t < timedelta(seconds=self.RAID_WINDOW)
        ]
        if len(self.join_tracker[guild.id]) >= self.RAID_THRESHOLD:
            await self.log_action(
                guild,
                "🚨 Raid détecté !",
                f"`{len(self.join_tracker[guild.id])}` membres ont rejoint en moins de `{self.RAID_WINDOW}s`.\nVerrouillage automatique activé."
            )
            for ch in guild.text_channels:
                try:
                    await ch.set_permissions(guild.default_role, send_messages=False)
                except Exception:
                    pass
            self.join_tracker[guild.id].clear()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        user = message.author
        now = datetime.utcnow()
        self.spam_tracker[user.id].append(now)
        self.spam_tracker[user.id] = [
            t for t in self.spam_tracker[user.id]
            if now - t < timedelta(seconds=self.SPAM_WINDOW)
        ]
        if len(self.spam_tracker[user.id]) >= self.SPAM_THRESHOLD:
            try:
                await user.timeout(timedelta(minutes=5), reason="Spam détecté par l'anti-raid")
                await self.log_action(
                    message.guild,
                    "🔇 Spam détecté",
                    f"{user.mention} (`{user}`) a été mute 5min pour spam."
                )
            except Exception:
                pass
            self.spam_tracker[user.id].clear()

    @commands.command(name="unlock")
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(ctx.guild.default_role, send_messages=None)
            except Exception:
                pass
        e = discord.Embed(
            title="✦  Serveur déverrouillé",
            description="Tous les salons sont à nouveau accessibles.",
            color=VERT,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"⬡ Action de {ctx.author.name}")
        await ctx.send(embed=e)

    @commands.command(name="lock")
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(ctx.guild.default_role, send_messages=False)
            except Exception:
                pass
        e = discord.Embed(
            title="✦  Serveur verrouillé",
            description="Tous les salons ont été verrouillés.",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"⬡ Action de {ctx.author.name}")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
