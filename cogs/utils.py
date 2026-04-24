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

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        e = discord.Embed(
            title=f"✦  {guild.name}",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        if guild.icon:
            e.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            e.set_image(url=guild.banner.url)
        e.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
        e.add_field(name="👑 Propriétaire", value=f"`{guild.owner}`", inline=True)
        e.add_field(name="📅 Créé le", value=f"`{guild.created_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name="👥 Membres", value=f"`{guild.member_count}`", inline=True)
        e.add_field(name="💬 Salons", value=f"`{len(guild.channels)}`", inline=True)
        e.add_field(name="🎭 Rôles", value=f"`{len(guild.roles)}`", inline=True)
        e.add_field(name="😀 Emojis", value=f"`{len(guild.emojis)}`", inline=True)
        e.add_field(name="🔒 Vérification", value=f"`{guild.verification_level}`", inline=True)
        e.set_footer(text=f"⬡ Demandé par {ctx.author.name}")
        await ctx.send(embed=e)

    @commands.command(name="avatar")
    async def avatar(self, ctx, membre: discord.Member = None):
        membre = membre or ctx.author
        e = discord.Embed(
            title=f"🖼️  Avatar de {membre.name}",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_image(url=membre.display_avatar.url)
        e.add_field(name="🔗 Lien", value=f"[Cliquez ici]({membre.display_avatar.url})")
        e.set_footer(text=f"⬡ Demandé par {ctx.author.name}")
        await ctx.send(embed=e)

    @commands.command(name="say")
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, salon: discord.TextChannel, *, message: str):
        await ctx.message.delete()
        e = discord.Embed(
            description=message,
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"⬡ Message du staff")
        await salon.send(embed=e)

    @commands.command(name="botinfo")
    async def botinfo(self, ctx):
        e = discord.Embed(
            title="🤖  Informations du bot",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=self.bot.user.display_avatar.url)
        e.add_field(name="🆔 ID", value=f"`{self.bot.user.id}`", inline=True)
        e.add_field(name="📅 Créé le", value=f"`{self.bot.user.created_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name="🌐 Serveurs", value=f"`{len(self.bot.guilds)}`", inline=True)
        e.add_field(name="👥 Membres", value=f"`{sum(g.member_count for g in self.bot.guilds)}`", inline=True)
        e.add_field(name="🎭 Préfixe", value="`+`", inline=True)
        e.set_footer(text=f"⬡ Demandé par {ctx.author.name}")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(Utils(bot))
