import discord
from discord.ext import commands
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="banlist")
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        await ctx.message.delete()

        bans = [entry async for entry in ctx.guild.bans()]

        if not bans:
            e = discord.Embed(
                title="🔨 Liste des bannissements",
                description="✅ Aucun membre banni sur ce serveur.",
                color=0x2ECC71,
                timestamp=datetime.utcnow()
            )
            e.set_footer(text=f"Demandé par {ctx.author.name}")
            return await ctx.send(embed=e)

        # Découpe en pages de 10
        pages = [bans[i:i+10] for i in range(0, len(bans), 10)]
        page_actuelle = 0

        def build_embed(page):
            e = discord.Embed(
                title=f"🔨 Liste des bannissements — {len(bans)} banni(s)",
                color=0xE74C3C,
                timestamp=datetime.utcnow()
            )
            for entry in page:
                user = entry.user
                raison = entry.reason or "Aucune raison"
                e.add_field(
                    name=f"👤 {user.name}",
                    value=(
                        f"🆔 `{user.id}`\n"
                        f"📋 Raison : {raison}"
                    ),
                    inline=False
                )
            e.set_footer(text=f"Page {pages.index(page)+1}/{len(pages)} • Demandé par {ctx.author.name}")
            return e

        # Boutons de navigation
        class BanListView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.page = 0

            @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.secondary)
            async def precedent(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
                if self.page > 0:
                    self.page -= 1
                    await interaction.response.edit_message(embed=build_embed(pages[self.page]), view=self)
                else:
                    await interaction.response.defer()

            @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.secondary)
            async def suivant(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("❌ Ce n'est pas ton menu !", ephemeral=True)
                if self.page < len(pages) - 1:
                    self.page += 1
                    await interaction.response.edit_message(embed=build_embed(pages[self.page]), view=self)
                else:
                    await interaction.response.defer()

        view = BanListView() if len(pages) > 1 else None
        await ctx.send(embed=build_embed(pages[0]), view=view)

    @banlist.error
    async def banlist_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande !", delete_after=5)


async def setup(bot):
    await bot.add_cog(Moderation(bot))