import discord
from discord.ext import commands
from datetime import timedelta
import asyncio

VIOLET = 0x9B59B6
ROUGE = 0xE74C3C

def embed_success(titre, description):
    e = discord.Embed(title=f"✦ {titre}", description=f"```\n{description}\n```", color=VIOLET)
    e.set_footer(text="⬡ Système de Gestion")
    return e

def embed_error(description):
    e = discord.Embed(title="✦ Erreur", description=f"```\n{description}\n```", color=ROUGE)
    return e

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.page = 0
        self.pages = [
            {
                "title": "✦ Aide — Gestion",
                "fields": [
                    ("┌ +clear [nombre]", "└ Supprime des messages"),
                    ("┌ +kick @membre [raison]", "└ Expulse un membre"),
                    ("┌ +ban @membre [raison]", "└ Bannit un membre"),
                    ("┌ +unban nom", "└ Débannis un membre"),
                    ("┌ +mute @membre [durée] [raison]", "└ Mute un membre"),
                    ("┌ +unmute @membre", "└ Unmute un membre"),
                    ("┌ +addrole @membre @role", "└ Ajoute un rôle"),
                    ("┌ +delrole @membre @role", "└ Retire un rôle"),
                    ("┌ +userinfo [@membre]", "└ Infos sur un membre"),
                ]
            },
            {
                "title": "✦ Aide — Permissions",
                "fields": [
                    ("┌ +perms", "└ Voir les permissions du serveur"),
                    ("┌ +setperms [perm] [rôles]", "└ Modifier une permission"),
                ]
            },
        ]

    def build_embed(self):
        page = self.pages[self.page]
        e = discord.Embed(title=page["title"], color=VIOLET)
        for name, value in page["fields"]:
            e.add_field(name=name, value=value, inline=False)
        e.set_footer(text=f"⬡ Page {self.page + 1}/{len(self.pages)}")
        return e

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < len(self.pages) - 1:
            self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class Gestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx):
        view = HelpView()
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, nombre: int = 10):
        await ctx.message.delete()
        await ctx.channel.purge(limit=nombre)
        msg = await ctx.send(embed=embed_success(
            "Suppression",
            f"  {nombre} messages supprimés\n  Salon : #{ctx.channel.name}\n  Par : {ctx.author.name}"
        ))
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, membre: discord.Member, *, raison="Aucune raison"):
        await membre.kick(reason=raison)
        await ctx.send(embed=embed_success(
            "Expulsion",
            f"  Membre  : {membre.name}\n  Raison  : {raison}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membre: discord.Member, *, raison="Aucune raison"):
        await membre.ban(reason=raison)
        await ctx.send(embed=embed_success(
            "Bannissement",
            f"  Membre  : {membre.name}\n  Raison  : {raison}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, nom):
        bans = [entry async for entry in ctx.guild.bans()]
        for entry in bans:
            if entry.user.name.lower() == nom.lower():
                await ctx.guild.unban(entry.user)
                await ctx.send(embed=embed_success(
                    "Débannissement",
                    f"  Membre  : {entry.user.name}\n  Par     : {ctx.author.name}"
                ))
                return
        await ctx.send(embed=embed_error(f"Membre '{nom}' introuvable"))

    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, membre: discord.Member, role: discord.Role):
        await membre.add_roles(role)
        await ctx.send(embed=embed_success(
            "Rôle Ajouté",
            f"  Membre  : {membre.name}\n  Rôle    : {role.name}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="delrole")
    @commands.has_permissions(manage_roles=True)
    async def delrole(self, ctx, membre: discord.Member, role: discord.Role):
        await membre.remove_roles(role)
        await ctx.send(embed=embed_success(
            "Rôle Retiré",
            f"  Membre  : {membre.name}\n  Rôle    : {role.name}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, membre: discord.Member, duree: int = 10, *, raison="Aucune raison"):
        until = discord.utils.utcnow() + timedelta(minutes=duree)
        await membre.timeout(until, reason=raison)
        await ctx.send(embed=embed_success(
            "Mute",
            f"  Membre  : {membre.name}\n  Durée   : {duree} min\n  Raison  : {raison}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, membre: discord.Member):
        await membre.timeout(None)
        await ctx.send(embed=embed_success(
            "Unmute",
            f"  Membre  : {membre.name}\n  Par     : {ctx.author.name}"
        ))

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, membre: discord.Member = None):
        membre = membre or ctx.author
        roles = [r.mention for r in membre.roles[1:]]
        e = discord.Embed(title=f"✦ Informations — {membre.name}", color=VIOLET)
        e.set_thumbnail(url=membre.display_avatar.url)
        e.add_field(name="┌ Identifiant", value=f"└ `{membre.id}`", inline=False)
        e.add_field(name="┌ Compte créé", value=f"└ `{membre.created_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name="┌ A rejoint", value=f"└ `{membre.joined_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name=f"┌ Rôles ({len(roles)})", value="└ " + " ".join(roles) if roles else "└ Aucun", inline=False)
        e.set_footer(text=f"⬡ Demandé par {ctx.author.name}")
        await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(Gestion(bot))
