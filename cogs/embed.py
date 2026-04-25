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

async def attendre_reponse(ctx, bot, message_bot):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        reponse = await bot.wait_for("message", check=check, timeout=60)
        await reponse.delete()
        await message_bot.delete()
        return reponse
    except:
        await message_bot.delete()
        return None

async def attendre_image(ctx, bot, message_bot):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        reponse = await bot.wait_for("message", check=check, timeout=60)
        await reponse.delete()
        await message_bot.delete()
        if reponse.attachments:
            return reponse.attachments[0].url
        return reponse.content
    except:
        await message_bot.delete()
        return None


class EmbedBuilderView(discord.ui.View):
    def __init__(self, ctx, bot, salon):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.bot = bot
        self.salon = salon
        self.msg_builder = None  # sera défini après l'envoi
        self.embed = discord.Embed(
            title="Titre de l'embed",
            description="Description de l'embed...",
            color=get_color(),
            timestamp=datetime.utcnow()
        )

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

    async def rafraichir(self):
        """Met à jour le message du builder avec l'embed en temps réel."""
        if self.msg_builder:
            await self.msg_builder.edit(embed=self.embed, view=self)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)

        await interaction.response.defer()
        choix = interaction.data["values"][0]

        if choix == "titre":
            msg = await self.ctx.channel.send("✏️ Envoyez le **titre** de l'embed")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                self.embed.title = reponse.content
                await self.rafraichir()

        elif choix == "description":
            msg = await self.ctx.channel.send("💬 Envoyez la **description** de l'embed")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                self.embed.description = reponse.content
                await self.rafraichir()

        elif choix == "auteur":
            msg = await self.ctx.channel.send("🕵️ Envoyez le **nom de l'auteur**")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                nom = reponse.content
                msg2 = await self.ctx.channel.send("🕵️ Envoyez l'**image de l'auteur** (image ou `skip`)")
                reponse2 = await attendre_image(self.ctx, self.bot, msg2)
                icon = reponse2 if reponse2 and reponse2 != "skip" else None
                self.embed.set_author(name=nom, icon_url=icon)
                await self.rafraichir()

        elif choix == "footer":
            msg = await self.ctx.channel.send("🔻 Envoyez le **texte du footer**")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                texte = reponse.content
                msg2 = await self.ctx.channel.send("🔻 Envoyez l'**image du footer** (image ou `skip`)")
                reponse2 = await attendre_image(self.ctx, self.bot, msg2)
                icon = reponse2 if reponse2 and reponse2 != "skip" else None
                self.embed.set_footer(text=texte, icon_url=icon)
                await self.rafraichir()

        elif choix == "thumbnail":
            msg = await self.ctx.channel.send("⬛ Envoyez l'**image du thumbnail** (image ou lien URL)")
            url = await attendre_image(self.ctx, self.bot, msg)
            if url and url != "skip":
                self.embed.set_thumbnail(url=url)
                await self.rafraichir()

        elif choix == "timestamp":
            self.embed.timestamp = datetime.utcnow()
            await self.rafraichir()

        elif choix == "image":
            msg = await self.ctx.channel.send("🖼️ Envoyez l'**image** de l'embed (image ou lien URL)")
            url = await attendre_image(self.ctx, self.bot, msg)
            if url and url != "skip":
                self.embed.set_image(url=url)
                await self.rafraichir()

        elif choix == "url":
            msg = await self.ctx.channel.send("🌐 Envoyez l'**URL** du titre")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                self.embed.url = reponse.content
                await self.rafraichir()

        elif choix == "couleur":
            msg = await self.ctx.channel.send("🔴 Envoyez la **couleur** en format hex (ex: `#FF0000`)")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                try:
                    couleur = int(reponse.content.replace("#", ""), 16)
                    self.embed.color = couleur
                    await self.rafraichir()
                except ValueError:
                    await self.ctx.channel.send("❌ Couleur invalide ! Utilise le format `#FF0000`", delete_after=5)

        elif choix == "add_field":
            msg = await self.ctx.channel.send("↪️ Envoyez le **nom du field**")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                nom = reponse.content
                msg2 = await self.ctx.channel.send(f"↪️ Envoyez la **valeur du field** `{nom}`")
                reponse2 = await attendre_reponse(self.ctx, self.bot, msg2)
                if reponse2:
                    self.embed.add_field(name=nom, value=reponse2.content, inline=False)
                    await self.rafraichir()

        elif choix == "del_field":
            if not self.embed.fields:
                return await self.ctx.channel.send("❌ Aucun field à supprimer !", delete_after=3)
            liste = "\n".join([f"`{i+1}` - {f.name}" for i, f in enumerate(self.embed.fields)])
            msg = await self.ctx.channel.send(f"↩️ Quel field supprimer ? (envoie le numéro)\n{liste}")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                try:
                    index = int(reponse.content) - 1
                    self.embed.remove_field(index)
                    await self.rafraichir()
                except (ValueError, IndexError):
                    await self.ctx.channel.send("❌ Numéro invalide !", delete_after=3)

        elif choix == "copier":
            msg = await self.ctx.channel.send("📥 Envoyez l'**ID du message** à copier")
            reponse = await attendre_reponse(self.ctx, self.bot, msg)
            if reponse:
                try:
                    message = await self.ctx.channel.fetch_message(int(reponse.content))
                    if message.embeds:
                        self.embed = message.embeds[0].copy()
                        await self.rafraichir()
                    else:
                        await self.ctx.channel.send("❌ Ce message n'a pas d'embed !", delete_after=3)
                except Exception:
                    await self.ctx.channel.send("❌ Message introuvable !", delete_after=3)

    @discord.ui.button(label="✅ Envoyer", style=discord.ButtonStyle.green, row=1)
    async def envoyer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
        await self.salon.send(embed=self.embed)
        await interaction.response.send_message(f"✅ Embed envoyé dans {self.salon.mention} !", ephemeral=True)
        self.stop()


class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="embed")
    @commands.has_permissions(administrator=True)
    async def embed(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await ctx.message.delete()
        view = EmbedBuilderView(ctx, self.bot, salon)
        msg_builder = await ctx.send(embed=view.embed, view=view)
        view.msg_builder = msg_builder


async def setup(bot):
    await bot.add_cog(Embed(bot))