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

class EmbedModal(discord.ui.Modal, title="✦ Créer un embed"):
    embed_titre = discord.ui.TextInput(
        label="Titre",
        placeholder="Titre de l'embed...",
        required=True,
        max_length=256
    )
    embed_description = discord.ui.TextInput(
        label="Description",
        placeholder="Description de l'embed...",
        required=True,
        style=discord.TextStyle.long,
        max_length=4000
    )
    embed_image = discord.ui.TextInput(
        label="URL de l'image (optionnel)",
        placeholder="https://...",
        required=False
    )
    embed_thumbnail = discord.ui.TextInput(
        label="URL du thumbnail (optionnel)",
        placeholder="https://...",
        required=False
    )

    def __init__(self, salon, couleur, categories):
        super().__init__()
        self.salon = salon
        self.couleur = couleur
        self.categories = categories

    async def on_submit(self, interaction: discord.Interaction):
        e = discord.Embed(
            title=self.embed_titre.value,
            description=self.embed_description.value,
            color=self.couleur,
            timestamp=datetime.utcnow()
        )
        if self.embed_image.value:
            e.set_image(url=self.embed_image.value)
        if self.embed_thumbnail.value:
            e.set_thumbnail(url=self.embed_thumbnail.value)

        if self.categories:
            view = CategoriesView(self.categories)
            await self.salon.send(embed=e, view=view)
        else:
            await self.salon.send(embed=e)

        await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)


class CategorieModal(discord.ui.Modal, title="✦ Ajouter une catégorie"):
    nom = discord.ui.TextInput(
        label="Nom de la catégorie",
        placeholder="Ex: Support, Partenariat...",
        required=True,
        max_length=100
    )
    emoji = discord.ui.TextInput(
        label="Emoji",
        placeholder="Ex: 🎫",
        required=False,
        max_length=10
    )
    contenu = discord.ui.TextInput(
        label="Contenu (une option par ligne)",
        placeholder="option 1\noption 2\noption 3",
        style=discord.TextStyle.long,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()


class CategoriesView(discord.ui.View):
    def __init__(self, categories):
        super().__init__(timeout=None)
        options = []
        for cat in categories:
            emoji = cat.get("emoji") or None
            options.append(discord.SelectOption(
                label=cat["nom"],
                description=cat["contenu"].split("\n")[0][:100],
                emoji=emoji
            ))
        select = discord.ui.Select(
            placeholder="Fais un choix",
            options=options,
            custom_id="embed_select"
        )
        select.callback = self.select_callback
        self.add_item(select)
        self.categories = categories

    async def select_callback(self, interaction: discord.Interaction):
        choix = interaction.data["values"][0]
        cat = next((c for c in self.categories if c["nom"] == choix), None)
        if not cat:
            return
        e = discord.Embed(
            title=f"{cat.get('emoji', '')} {cat['nom']}",
            description="\n".join([f"╰ {ligne}" for ligne in cat["contenu"].split("\n")]),
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_footer(text="⬡ Système de tickets")
        await interaction.response.send_message(embed=e, ephemeral=True)


class EmbedBuilderView(discord.ui.View):
    def __init__(self, ctx, salon):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.salon = salon
        self.couleur = get_color()
        self.categories = []

    @discord.ui.button(label="🎨 Couleur", style=discord.ButtonStyle.secondary)
    async def choisir_couleur(self, interaction: discord.Interaction, button: discord.ui.Button):
        couleurs = {
            "violet": 0x9B59B6, "bleu": 0x3498DB, "rouge": 0xE74C3C,
            "or": 0xF1C40F, "vert": 0x2ECC71, "rose": 0xFF69B4,
            "orange": 0xE67E22, "blanc": 0xFFFFFF, "noir": 0x2C2F33
        }
        options = [discord.SelectOption(label=nom.capitalize()) for nom in couleurs]
        view = discord.ui.View(timeout=60)
        select = discord.ui.Select(placeholder="Choisis une couleur", options=options)

        async def color_callback(inter):
            self.couleur = couleurs[inter.data["values"][0].lower()]
            await inter.response.send_message(f"✅ Couleur **{inter.data['values'][0]}** sélectionnée !", ephemeral=True)

        select.callback = color_callback
        view.add_item(select)
        await interaction.response.send_message("Choisis une couleur :", view=view, ephemeral=True)

    @discord.ui.button(label="➕ Ajouter catégorie", style=discord.ButtonStyle.secondary)
    async def ajouter_categorie(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CategorieModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.categories.append({
            "nom": modal.nom.value,
            "emoji": modal.emoji.value,
            "contenu": modal.contenu.value
        })
        await modal.interaction.response.send_message(f"✅ Catégorie **{modal.nom.value}** ajoutée !", ephemeral=True)

    @discord.ui.button(label="✅ Envoyer", style=discord.ButtonStyle.green)
    async def envoyer(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmbedModal(self.salon, self.couleur, self.categories)
        await interaction.response.send_modal(modal)


class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="embed")
    @commands.has_permissions(administrator=True)
    async def embed(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await ctx.message.delete()
        e = discord.Embed(
            title="✦  Créateur d'embed",
            description="Utilise les boutons pour personnaliser ton embed !",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.add_field(name="🎨 Couleur", value="╰ Choisis la couleur de l'embed", inline=False)
        e.add_field(name="➕ Ajouter catégorie", value="╰ Ajoute un menu déroulant avec des options", inline=False)
        e.add_field(name="✅ Envoyer", value="╰ Remplis le titre, description et envoie !", inline=False)
        e.set_footer(text=f"⬡ Embed builder • {ctx.author.name}")
        view = EmbedBuilderView(ctx, salon)
        await ctx.send(embed=e, view=view)


async def setup(bot):
    await bot.add_cog(Embed(bot))
