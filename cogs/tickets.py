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

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩  Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing:
            await interaction.response.send_message(
                f"⬡ Tu as déjà un ticket ouvert : {existing.mention}", ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = discord.utils.get(guild.categories, name="Tickets")
        ch = await guild.create_text_channel(
            f"ticket-{member.name.lower()}",
            overwrites=overwrites,
            category=category
        )

        e = discord.Embed(
            title="✦  Ticket ouvert",
            description="Le staff va vous répondre sous peu.\nPour fermer le ticket, cliquez sur le bouton ci-dessous.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="👤 Membre", value=f"`{member}`", inline=True)
        e.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        e.set_footer(text="⬡ Système de tickets")
        await ch.send(content=member.mention, embed=e, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket créé : {ch.mention}", ephemeral=True)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒  Fermer le ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        e = discord.Embed(
            title="✦  Ticket fermé",
            description="Ce ticket va être supprimé dans 5 secondes.",
            color=ROUGE,
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"⬡ Fermé par {interaction.user.name}")
        await interaction.response.send_message(embed=e)
        await discord.utils.sleep_until(
            datetime.utcnow().replace(second=datetime.utcnow().second + 5)
        )
        await interaction.channel.delete()


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        await ctx.message.delete()
        e = discord.Embed(
            title="✦  Support & Tickets",
            description="Clique sur le bouton ci-dessous pour ouvrir un ticket.\nNotre équipe te répondra dans les plus brefs délais.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.set_footer(text="⬡ Système de tickets")
        await ctx.send(embed=e, view=TicketView())

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))
