import discord
from discord.ext import commands
from datetime import datetime
import json
import os
import asyncio

LOGS_FILE = "logs_config.json"
TICKET_CONFIG_FILE = "ticket_config.json"

def get_color():
    if os.path.exists("theme.json"):
        with open("theme.json", "r") as f:
            return json.load(f).get("color", 0x9B59B6)
    return 0x9B59B6

ROUGE = 0xE74C3C
VERT = 0x2ECC71

def load_logs():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    return {}

def load_ticket_config():
    if os.path.exists(TICKET_CONFIG_FILE):
        with open(TICKET_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_ticket_config(data):
    with open(TICKET_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def get_log_channel(bot, guild, type_log):
    data = load_logs()
    guild_id = str(guild.id)
    if guild_id in data and type_log in data[guild_id]:
        return guild.get_channel(data[guild_id][type_log])
    return None

# Types de tickets et leur catégorie associée
TICKET_TYPES = {
    "owner": {
        "label": "Contactez un Owner",
        "categorie": "Ticket owner",
        "description": "Contacter directement un Owner du serveur."
    },
    "abus": {
        "label": "Gestion abus",
        "categorie": "Gestion Abus",
        "description": "Signaler un abus sur le serveur."
    },
    "staff": {
        "label": "Gestion staff",
        "categorie": "Gestion Staff",
        "description": "Contacter la gestion du staff."
    },
    "partenariat": {
        "label": "Partenariat",
        "categorie": "Partenariat",
        "description": "Proposer un partenariat avec le serveur."
    },
}


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["label"],
                value=key,
                description=info["description"]
            )
            for key, info in TICKET_TYPES.items()
        ]
        super().__init__(
            placeholder="Selectionnez le type de ticket",
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        choix = self.values[0]
        info = TICKET_TYPES[choix]
        guild = interaction.guild
        member = interaction.user

        # Verifie si un ticket existe deja
        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{member.name.lower()}-{choix}"
        )
        if existing:
            return await interaction.response.send_message(
                f"Tu as deja un ticket de ce type ouvert : {existing.mention}",
                ephemeral=True
            )

        # Trouve la categorie
        category = discord.utils.get(guild.categories, name=info["categorie"])
        if not category:
            return await interaction.response.send_message(
                f"La categorie **{info['categorie']}** est introuvable sur le serveur.",
                ephemeral=True
            )

        # Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Cree le salon
        ch = await guild.create_text_channel(
            f"ticket-{member.name.lower()}-{choix}",
            overwrites=overwrites,
            category=category
        )

        # Message dans le ticket
        e = discord.Embed(
            title="Support & Tickets",
            description="Le staff va vous repondre sous peu.\nPour fermer le ticket, cliquez sur le bouton ci-dessous.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="Membre", value=f"`{member}`", inline=True)
        e.add_field(name="ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="Type", value=f"`{info['label']}`", inline=True)
        e.set_footer(text="Systeme de tickets")
        await ch.send(content=member.mention, embed=e, view=CloseTicketView())

        # Log
        log_ch = await get_log_channel(interaction.client, guild, "ticket")
        if log_ch:
            log_e = discord.Embed(title="Ticket ouvert", color=VERT, timestamp=datetime.utcnow())
            log_e.set_thumbnail(url=member.display_avatar.url)
            log_e.add_field(name="Membre", value=f"`{member}`", inline=True)
            log_e.add_field(name="Type", value=f"`{info['label']}`", inline=True)
            log_e.add_field(name="Salon", value=ch.mention, inline=True)
            log_e.set_footer(text="Logs Tickets")
            await log_ch.send(embed=log_e)

        await interaction.response.send_message(
            f"Ticket cree : {ch.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_ch = await get_log_channel(interaction.client, interaction.guild, "ticket")
        if log_ch:
            log_e = discord.Embed(title="Ticket ferme", color=ROUGE, timestamp=datetime.utcnow())
            log_e.add_field(name="Salon", value=f"`{interaction.channel.name}`", inline=True)
            log_e.add_field(name="Ferme par", value=f"`{interaction.user}`", inline=True)
            log_e.set_footer(text="Logs Tickets")
            await log_ch.send(embed=log_e)

        e = discord.Embed(
            title="Ticket ferme",
            description="Ce ticket va etre supprime dans 5 secondes.",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"Ferme par {interaction.user.name}")
        await interaction.response.send_message(embed=e)
        await asyncio.sleep(5)
        await interaction.channel.delete()


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        await ctx.message.delete()
        e = discord.Embed(
            title="Support & Tickets",
            description="Selectionnez le type de ticket dans le menu ci-dessous.\nNotre equipe te repondra dans les plus brefs delais.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.set_footer(text="Systeme de tickets")
        await ctx.send(embed=e, view=TicketView())

    @commands.command(name="ticket_settings")
    @commands.has_permissions(administrator=True)
    async def ticket_settings(self, ctx):
        await ctx.message.delete()
        e = discord.Embed(
            title="Parametres des tickets",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        for key, info in TICKET_TYPES.items():
            cat = discord.utils.get(ctx.guild.categories, name=info["categorie"])
            statut = "Trouvee" if cat else "Introuvable"
            e.add_field(
                name=info["label"],
                value=f"Categorie : `{info['categorie']}` — {statut}",
                inline=False
            )
        e.set_footer(text=f"Demande par {ctx.author.name}")
        await ctx.send(embed=e)

    @commands.command(name="close")
    @commands.has_permissions(administrator=True)
    async def close(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.send(embed=discord.Embed(
                title="Erreur",
                description="Cette commande s'utilise uniquement dans un ticket !",
                color=ROUGE
            ))
        log_ch = await get_log_channel(self.bot, ctx.guild, "ticket")
        if log_ch:
            log_e = discord.Embed(title="Ticket ferme", color=ROUGE, timestamp=datetime.utcnow())
            log_e.add_field(name="Salon", value=f"`{ctx.channel.name}`", inline=True)
            log_e.add_field(name="Ferme par", value=f"`{ctx.author}`", inline=True)
            log_e.set_footer(text="Logs Tickets")
            await log_ch.send(embed=log_e)
        e = discord.Embed(
            title="Ticket ferme",
            description="Ce ticket va etre supprime dans 5 secondes.",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"Ferme par {ctx.author.name}")
        await ctx.send(embed=e)
        await asyncio.sleep(5)
        await ctx.channel.delete()

    @commands.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.send(embed=discord.Embed(
                title="Erreur",
                description="Cette commande s'utilise uniquement dans un ticket !",
                color=ROUGE
            ))
        log_ch = await get_log_channel(self.bot, ctx.guild, "ticket")
        if log_ch:
            log_e = discord.Embed(title="Ticket supprime", color=ROUGE, timestamp=datetime.utcnow())
            log_e.add_field(name="Salon", value=f"`{ctx.channel.name}`", inline=True)
            log_e.add_field(name="Supprime par", value=f"`{ctx.author}`", inline=True)
            log_e.set_footer(text="Logs Tickets")
            await log_ch.send(embed=log_e)
        await ctx.channel.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))