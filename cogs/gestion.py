import discord
from discord.ext import commands
from datetime import timedelta
import asyncio
import json
import os
import typing

PERMS_FILE = "perms_data.json"
BL_FILE = "blacklist.json"
THEME_FILE = "theme.json"

def load_theme():
    if os.path.exists(THEME_FILE):
        with open(THEME_FILE, "r") as f:
            return json.load(f)
    return {"color": 0x9B59B6}

def save_theme(data):
    with open(THEME_FILE, "w") as f:
        json.dump(data, f)

def get_color():
    return load_theme().get("color", 0x9B59B6)

ROUGE = 0xE74C3C

def load_perms():
    if os.path.exists(PERMS_FILE):
        with open(PERMS_FILE, "r") as f:
            return json.load(f)
    return {"Perm1": "Aucun", "Perm2": "Aucun", "Perm3": "Aucun",
            "Perm4": "Aucun", "Perm5": "Aucun", "Perm6": "Aucun",
            "Perm7": "Aucun", "Perm8": "Aucun", "Perm9": "Aucun"}

def save_perms(data):
    with open(PERMS_FILE, "w") as f:
        json.dump(data, f)

def load_bl():
    if os.path.exists(BL_FILE):
        with open(BL_FILE, "r") as f:
            return json.load(f)
    return {}

def save_bl(data):
    with open(BL_FILE, "w") as f:
        json.dump(data, f)

def embed_success(titre, description):
    e = discord.Embed(title=f"✦ {titre}", description=f"```\n{description}\n```", color=get_color())
    e.set_footer(text="⬡ Système de Gestion")
    return e

def embed_error(description):
    e = discord.Embed(title="✦ Erreur", description=f"```\n{description}\n```", color=ROUGE)
    return e

THEMES = {
    "violet": 0x9B59B6,
    "bleu": 0x3498DB,
    "rouge": 0xE74C3C,
    "or": 0xF1C40F,
    "vert": 0x2ECC71,
    "rose": 0xFF69B4,
    "orange": 0xE67E22,
    "blanc": 0xFFFFFF,
    "noir": 0x2C2F33,
}

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.page = 0
        self.pages = [
            {
                "title": "✦ Aide — Modération",
                "fields": [
                    ("┌ +clear [nombre]", "└ Supprime des messages"),
                    ("┌ +kick @membre [raison]", "└ Expulse un membre"),
                    ("┌ +ban @membre [raison]", "└ Bannit un membre"),
                    ("┌ +unban nom", "└ Débannis un membre"),
                    ("┌ +baninfo nom", "└ Infos sur un ban"),
                    ("┌ +mute @membre [durée] [raison]", "└ Mute un membre"),
                    ("┌ +unmute @membre", "└ Unmute un membre"),
                ]
            },
            {
                "title": "✦ Aide — Rôles & Membres",
                "fields": [
                    ("┌ +addrole @membre @role", "└ Ajoute un rôle"),
                    ("┌ +delrole @membre @role", "└ Retire un rôle"),
                    ("┌ +userinfo [@membre]", "└ Infos sur un membre"),
                ]
            },
            {
                "title": "✦ Aide — Permissions & Blacklist",
                "fields": [
                    ("┌ +perms", "└ Voir les permissions du serveur"),
                    ("┌ +setperms [perm] [rôles]", "└ Modifier une permission"),
                    ("┌ +bl @membre [raison]", "└ Blacklist + ban un membre"),
                    ("┌ +unbl @membre", "└ Retire de la blacklist"),
                    ("┌ +blinfo @membre/ID", "└ Infos blacklist d'un membre"),
                ]
            },
            {
                "title": "✦ Aide — Paramètres",
                "fields": [
                    ("┌ +theme <couleur>", "└ Change la couleur des embeds"),
                    ("┌ Couleurs disponibles :", "└ violet, bleu, rouge, or, vert, rose, orange, blanc, noir"),
                ]
            },
        ]

    def build_embed(self):
        page = self.pages[self.page]
        e = discord.Embed(title=page["title"], color=get_color())
        for name, value in page["fields"]:
            e.add_field(name=name, value=value, inline=False)
        e.set_footer(text=f"⬡ Page {self.page + 1}/{len(self.pages)}")
        return e

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="help_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="help_next")
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

    @commands.command(name="theme")
    @commands.has_permissions(administrator=True)
    async def theme(self, ctx, couleur: str):
        couleur = couleur.lower()
        if couleur not in THEMES:
            liste = ", ".join(THEMES.keys())
            await ctx.send(embed=embed_error(f"Couleur invalide !\n  Disponibles : {liste}"))
            return
        data = {"color": THEMES[couleur]}
        save_theme(data)
        e = discord.Embed(
            title="✦ Thème mis à jour",
            description=f"```\n  Couleur : {couleur}\n```",
            color=THEMES[couleur]
        )
        e.set_footer(text="⬡ Système de Gestion")
        await ctx.send(embed=e)

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

    @commands.command(name="baninfo")
    async def baninfo(self, ctx, *, nom: str):
        bans = [entry async for entry in ctx.guild.bans()]
        for entry in bans:
            if entry.user.name.lower() == nom.lower():
                await ctx.send(embed=embed_success(
                    "Info Ban",
                    f"  Membre  : {entry.user.name}\n  Raison  : {entry.reason or 'Aucune raison'}"
                ))
                return
        await ctx.send(embed=embed_error(f"'{nom}' introuvable dans les bans"))

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
        e = discord.Embed(title=f"✦ Informations — {membre.name}", color=get_color())
        e.set_thumbnail(url=membre.display_avatar.url)
        e.add_field(name="┌ Identifiant", value=f"└ `{membre.id}`", inline=False)
        e.add_field(name="┌ Compte créé", value=f"└ `{membre.created_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name="┌ A rejoint", value=f"└ `{membre.joined_at.strftime('%d/%m/%Y')}`", inline=True)
        e.add_field(name=f"┌ Rôles ({len(roles)})", value="└ " + " ".join(roles) if roles else "└ Aucun", inline=False)
        e.set_footer(text=f"⬡ Demandé par {ctx.author.name}")
        await ctx.send(embed=e)

    @commands.command(name="perms")
    async def perms(self, ctx):
        data = load_perms()
        description = ""
        for perm, roles in data.items():
            description += f"**{perm}**\n{roles}\n\n"
        e = discord.Embed(title="✦ Permissions du serveur", description=description, color=get_color())
        e.set_footer(text="⬡ Voir +help pour plus d'infos")
        await ctx.send(embed=e)

    @commands.command(name="setperms")
    @commands.has_permissions(administrator=True)
    async def setperms(self, ctx, perm: str, *, roles: str):
        data = load_perms()
        if perm not in data:
            await ctx.send(embed=embed_error(f"{perm} invalide. Utilise Perm1 à Perm9"))
            return
        data[perm] = roles
        save_perms(data)
        await ctx.send(embed=embed_success(
            "Permissions mises à jour",
            f"  {perm} → {roles}"
        ))

    @commands.command(name="bl")
    @commands.has_permissions(administrator=True)
    async def bl(self, ctx, membre: discord.Member, *, raison="Aucune raison"):
        data = load_bl()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}
        data[guild_id][str(membre.id)] = {
            "nom": membre.name,
            "raison": raison,
            "par": ctx.author.name
        }
        save_bl(data)
        await membre.ban(reason=f"Blacklist : {raison}")
        await ctx.send(embed=embed_success(
            "Blacklist",
            f"  Membre  : {membre.name}\n  Raison  : {raison}\n  Par     : {ctx.author.name}\n  Action  : Banni du serveur"
        ))

    @commands.command(name="unbl")
    @commands.has_permissions(administrator=True)
    async def unbl(self, ctx, membre: discord.Member):
        data = load_bl()
        guild_id = str(ctx.guild.id)
        if guild_id in data and str(membre.id) in data[guild_id]:
            del data[guild_id][str(membre.id)]
            save_bl(data)
            await ctx.send(embed=embed_success(
                "Blacklist Retirée",
                f"  Membre  : {membre.name}\n  Par     : {ctx.author.name}"
            ))
        else:
            await ctx.send(embed=embed_error(f"{membre.name} n'est pas dans la blacklist"))

    @commands.command(name="blinfo")
    async def blinfo(self, ctx, membre: typing.Union[discord.Member, int]):
        data = load_bl()
        guild_id = str(ctx.guild.id)
        membre_id = str(membre.id) if isinstance(membre, discord.Member) else str(membre)
        membre_nom = membre.name if isinstance(membre, discord.Member) else f"ID: {membre}"
        if guild_id in data and membre_id in data[guild_id]:
            info = data[guild_id][membre_id]
            await ctx.send(embed=embed_success(
                "Info Blacklist",
                f"  Membre  : {info['nom']}\n  Raison  : {info['raison']}\n  Par     : {info['par']}"
            ))
        else:
            await ctx.send(embed=embed_error(f"{membre_nom} n'est pas dans la blacklist"))

async def setup(bot):
    await bot.add_cog(Gestion(bot))
