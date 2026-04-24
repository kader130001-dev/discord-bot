import discord
from discord.ext import commands
from datetime import datetime
import json
import os

def get_color():
    if os.path.exists("theme.json"):
        with open("theme.json", "r") as f:
            return json.load(f).get("color", 0x9B59B6)
    return 0x9B59B6

ROUGE = 0xE74C3C
VERT = 0x2ECC71

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        for ch in guild.text_channels:
            if "log" in ch.name.lower():
                return ch
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ch = self.get_log_channel(member.guild)
        if not ch:
            return
        e = discord.Embed(
            title="✦  Nouveau membre",
            color=VERT,
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="👤 Membre", value=f"`{member}`", inline=True)
        e.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="📅 Compte créé", value=f"`{member.created_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name="👥 Membres total", value=f"`{member.guild.member_count}`", inline=True)
        e.set_footer(text="⬡ Logs — Arrivée")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        ch = self.get_log_channel(member.guild)
        if not ch:
            return
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        e = discord.Embed(
            title="✦  Membre parti",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="👤 Membre", value=f"`{member}`", inline=True)
        e.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="🎭 Rôles", value=" ".join(roles) if roles else "`Aucun`", inline=False)
        e.set_footer(text="⬡ Logs — Départ")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        ch = self.get_log_channel(message.guild)
        if not ch:
            return
        e = discord.Embed(
            title="✦  Message supprimé",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=message.author.display_avatar.url)
        e.add_field(name="👤 Auteur", value=f"`{message.author}`", inline=True)
        e.add_field(name="💬 Salon", value=message.channel.mention, inline=True)
        e.add_field(name="📝 Contenu", value=f"```{message.content or 'Aucun contenu'}```", inline=False)
        e.set_footer(text="⬡ Logs — Suppression")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        ch = self.get_log_channel(before.guild)
        if not ch:
            return
        e = discord.Embed(
            title="✦  Message modifié",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=before.author.display_avatar.url)
        e.add_field(name="👤 Auteur", value=f"`{before.author}`", inline=True)
        e.add_field(name="💬 Salon", value=before.channel.mention, inline=True)
        e.add_field(name="📝 Avant", value=f"```{before.content}```", inline=False)
        e.add_field(name="✏️ Après", value=f"```{after.content}```", inline=False)
        e.set_footer(text="⬡ Logs — Modification")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        ch = self.get_log_channel(guild)
        if not ch:
            return
        e = discord.Embed(
            title="✦  Membre banni",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=user.display_avatar.url)
        e.add_field(name="👤 Utilisateur", value=f"`{user}`", inline=True)
        e.add_field(name="🆔 ID", value=f"`{user.id}`", inline=True)
        e.set_footer(text="⬡ Logs — Ban")
        await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        ch = self.get_log_channel(guild)
        if not ch:
            return
        e = discord.Embed(
            title="✦  Membre débanni",
            color=VERT,
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=user.display_avatar.url)
        e.add_field(name="👤 Utilisateur", value=f"`{user}`", inline=True)
        e.add_field(name="🆔 ID", value=f"`{user.id}`", inline=True)
        e.set_footer(text="⬡ Logs — Unban")
        await ch.send(embed=e)

async def setup(bot):
    await bot.add_cog(Logs(bot))
