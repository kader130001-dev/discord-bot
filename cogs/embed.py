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


# ─── Modals ───────────────────────────────────────────────────────────────────

class TitreModal(discord.ui.Modal, title="✏️ Modifier le titre"):
    valeur = discord.ui.TextInput(label="Titre", placeholder="Titre de l'embed...", max_length=256)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class DescriptionModal(discord.ui.Modal, title="💬 Modifier la description"):
    valeur = discord.ui.TextInput(label="Description", placeholder="Description...", style=discord.TextStyle.long, max_length=4000)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class AuteurModal(discord.ui.Modal, title="🕵️ Modifier l'auteur"):
    nom = discord.ui.TextInput(label="Nom de l'auteur", placeholder="Ex: L'Équipe Palma", max_length=256)
    icon_url = discord.ui.TextInput(label="URL de l'icône (optionnel)", placeholder="https://...", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class FooterModal(discord.ui.Modal, title="🔻 Modifier le footer"):
    texte = discord.ui.TextInput(label="Texte du footer", placeholder="Ex: Cordialement, L'Équipe", max_length=2048)
    icon_url = discord.ui.TextInput(label="URL de l'icône (optionnel)", placeholder="https://...", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class ThumbnailModal(discord.ui.Modal, title="⬛ Modifier le thumbnail"):
    valeur = discord.ui.TextInput(label="URL du thumbnail", placeholder="https://...", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class ImageModal(discord.ui.Modal, title="🖼️ Modifier l'image"):
    valeur = discord.ui.TextInput(label="URL de l'image", placeholder="https://...", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class UrlModal(discord.ui.Modal, title="🌐 Modifier l'URL"):
    valeur = discord.ui.TextInput(label="URL du titre", placeholder="https://...", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class CouleurModal(discord.ui.Modal, title="🔴 Modifier la couleur"):
    valeur = discord.ui.TextInput(label="Couleur en hex", placeholder="Ex: #FF0000", max_length=7)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class FieldModal(discord.ui.Modal, title="↪️ Ajouter un field"):
    nom = discord.ui.TextInput(label="Nom du field", placeholder="Ex: Informations", max_length=256)
    valeur = discord.ui.TextInput(label="Valeur", placeholder="Contenu du field...", style=discord.TextStyle.long, max_length=1024)
    inline = discord.ui.TextInput(label="Inline ? (oui/non)", placeholder="oui", max_length=3, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class SupprimerFieldModal(discord.ui.Modal, title="↩️ Supprimer un field"):
    index = discord.ui.TextInput(label="Numéro du field (commence à 1)", placeholder="Ex: 1", max_length=2)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class CopierEmbedModal(discord.ui.Modal, title="📥 Copier un embed existant"):
    message_id = discord.ui.TextInput(label="ID du message à copier", placeholder="Ex: 1234567890123456789", max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()


# ─── Builder View ──────────────────────────────────────────────────────────────

class EmbedBuilderView(discord.ui.View):
    def __init__(self, ctx, salon):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.salon = salon
        self.embed = discord.Embed(
            title="Titre de l'embed",
            description="Description de l'embed...",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        self.fields = []
        select = discord.ui.Select(
            placeholder="Fais un choix",
            options=[
                discord.SelectOption(label="Modifier le titre", emoji="✏️", value="titre"),
                discord.SelectOption(label="Modifier la description", emoji="💬", value="description"),
                discord.SelectOption(label="Modifier l'auteur", emoji="🕵️", value="auteur"),
                discord.SelectOption(label="Modifier le footer", emoji="🔻", value="footer"),
                discord.SelectOption(label="Modifier le thumbnail", emoji="⬛", value="thumbnail"),
                discord.SelectOption(label="Modifier le timestamp", emoji="🕐", value="timestamp"),
                discord.SelectOption(label="Modifier l'image", emoji="🖼️", value="image"),
                discord.SelectOption(label="Modifier l'url", emoji="🌐", value="url"),
                discord.SelectOption(label="Modifier la couleur", emoji="🔴", value="couleur"),
                discord.SelectOption(label="Ajouter un field", emoji="↪️", value="add_field"),
                discord.SelectOption(label="Supprimer un field", emoji="↩️", value="del_field"),
                discord.SelectOption(label="Copier un embed existant", emoji="📥", value="copier"),
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)

        choix = interaction.data["values"][0]

        if choix == "titre":
            modal = TitreModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.embed.title = modal.valeur.value
            await modal.interaction.response.send_message("✅ Titre mis à jour !", ephemeral=True)

        elif choix == "description":
            modal = DescriptionModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.embed.description = modal.valeur.value
            await modal.interaction.response.send_message("✅ Description mise à jour !", ephemeral=True)

        elif choix == "auteur":
            modal = AuteurModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            icon = modal.icon_url.value or None
            self.embed.set_author(name=modal.nom.value, icon_url=icon)
            await modal.interaction.response.send_message("✅ Auteur mis à jour !", ephemeral=True)

        elif choix == "footer":
            modal = FooterModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            icon = modal.icon_url.value or None
            self.embed.set_footer(text=modal.texte.value, icon_url=icon)
            await modal.interaction.response.send_message("✅ Footer mis à jour !", ephemeral=True)

        elif choix == "thumbnail":
            modal = ThumbnailModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            url = modal.valeur.value or None
            self.embed.set_thumbnail(url=url)
            await modal.interaction.response.send_message("✅ Thumbnail mis à jour !", ephemeral=True)

        elif choix == "timestamp":
            self.embed.timestamp = datetime.utcnow()
            await interaction.response.send_message("✅ Timestamp mis à jour à maintenant !", ephemeral=True)

        elif choix == "image":
            modal = ImageModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            url = modal.valeur.value or None
            self.embed.set_image(url=url)
            await modal.interaction.response.send_message("✅ Image mise à jour !", ephemeral=True)

        elif choix == "url":
            modal = UrlModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.embed.url = modal.valeur.value or None
            await modal.interaction.response.send_message("✅ URL mise à jour !", ephemeral=True)

        elif choix == "couleur":
            modal = CouleurModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            try:
                couleur = int(modal.valeur.value.replace("#", ""), 16)
                self.embed.color = couleur
                await modal.interaction.response.send_message("✅ Couleur mise à jour !", ephemeral=True)
            except ValueError:
                await modal.interaction.response.send_message("❌ Couleur invalide ! Utilise le format #FF0000", ephemeral=True)

        elif choix == "add_field":
            modal = FieldModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            inline = modal.inline.value.lower() in ["oui", "yes", "o", "y"]
            self.embed.add_field(name=modal.nom.value, value=modal.valeur.value, inline=inline)
            await modal.interaction.response.send_message(f"✅ Field **{modal.nom.value}** ajouté !", ephemeral=True)

        elif choix == "del_field":
            if not self.embed.fields:
                return await interaction.response.send_message("❌ Aucun field à supprimer !", ephemeral=True)
            modal = SupprimerFieldModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            try:
                index = int(modal.index.value) - 1
                self.embed.remove_field(index)
                await modal.interaction.response.send_message("✅ Field supprimé !", ephemeral=True)
            except (ValueError, IndexError):
                await modal.interaction.response.send_message("❌ Numéro de field invalide !", ephemeral=True)

        elif choix == "copier":
            modal = CopierEmbedModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            try:
                msg = await self.ctx.channel.fetch_message(int(modal.message_id.value))
                if msg.embeds:
                    self.embed = msg.embeds[0].copy()
                    await modal.interaction.response.send_message("✅ Embed copié !", ephemeral=True)
                else:
                    await modal.interaction.response.send_message("❌ Ce message n'a pas d'embed !", ephemeral=True)
            except Exception:
                await modal.interaction.response.send_message("❌ Message introuvable !", ephemeral=True)

    @discord.ui.button(label="👁️ Prévisualiser", style=discord.ButtonStyle.secondary, row=1)
    async def previsualiser(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
        await interaction.response.send_message(embed=self.embed, ephemeral=True)

    @discord.ui.button(label="✅ Envoyer", style=discord.ButtonStyle.green, row=1)
    async def envoyer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
        await self.salon.send(embed=self.embed)
        await interaction.response.send_message(f"✅ Embed envoyé dans {self.salon.mention} !", ephemeral=True)
        self.stop()


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="embed")
    @commands.has_permissions(administrator=True)
    async def embed(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await ctx.message.delete()
        e = discord.Embed(
            title="✦ Créateur d'embed",
            description="Utilise le menu déroulant pour personnaliser ton embed, puis clique sur **Envoyer** !",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_footer(text=f"⬡ Embed builder • {ctx.author.name}")
        view = EmbedBuilderView(ctx, salon)
        await ctx.send(embed=e, view=view)


async def setup(bot):
    await bot.add_cog(Embed(bot))