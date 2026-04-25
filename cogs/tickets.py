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

def load_config(guild_id):
    if os.path.exists(TICKET_CONFIG_FILE):
        with open(TICKET_CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(guild_id), {"types": [], "staff_roles": [], "log_channel": None})
    return {"types": [], "staff_roles": [], "log_channel": None}

def save_config(guild_id, config):
    data = {}
    if os.path.exists(TICKET_CONFIG_FILE):
        with open(TICKET_CONFIG_FILE, "r") as f:
            data = json.load(f)
    data[str(guild_id)] = config
    with open(TICKET_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def get_log_channel(bot, guild):
    config = load_config(guild.id)
    if config.get("log_channel"):
        return guild.get_channel(config["log_channel"])
    return None

async def attendre(ctx, bot, msg):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        rep = await bot.wait_for("message", check=check, timeout=60)
        await rep.delete()
        await msg.delete()
        return rep
    except:
        await msg.delete()
        return None


# ─── Ticket Select dynamique ───────────────────────────────────────────────────

class TicketSelect(discord.ui.Select):
    def __init__(self, types):
        options = []
        for t in types:
            options.append(discord.SelectOption(
                label=t["nom"],
                value=t["nom"],
                description=t["description"][:100],
                emoji=t.get("emoji") or None
            ))
        super().__init__(
            placeholder="Veuillez faire un choix.",
            options=options,
            custom_id="ticket_select"
        )
        self.types = types

    async def callback(self, interaction: discord.Interaction):
        choix = self.values[0]
        t = next((x for x in self.types if x["nom"] == choix), None)
        if not t:
            return await interaction.response.send_message("Type de ticket introuvable.", ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        # 1 ticket max par membre
        existing = [
            ch for ch in guild.text_channels
            if ch.name.startswith(f"ticket-{member.name.lower()}")
        ]
        if existing:
            return await interaction.response.send_message(
                f"Tu as deja un ticket ouvert : {existing[0].mention}",
                ephemeral=True
            )

        # Categorie
        category = discord.utils.get(guild.categories, name=t["categorie"])
        if not category:
            return await interaction.response.send_message(
                f"La categorie **{t['categorie']}** est introuvable. Verifie les parametres.",
                ephemeral=True
            )

        # Permissions
        config = load_config(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role_id in config.get("staff_roles", []):
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        nom_salon = f"ticket-{member.name.lower()}-{t['nom'].lower().replace(' ', '-')}"[:100]
        ch = await guild.create_text_channel(nom_salon, overwrites=overwrites, category=category)

        e = discord.Embed(
            title="Support & Tickets",
            description="Le staff va vous repondre sous peu.\nPour fermer le ticket, cliquez sur le bouton ci-dessous.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="Membre", value=f"`{member}`", inline=True)
        e.add_field(name="ID", value=f"`{member.id}`", inline=True)
        e.add_field(name="Type", value=f"`{t['nom']}`", inline=True)
        e.set_footer(text="Systeme de tickets")
        await ch.send(content=member.mention, embed=e, view=CloseTicketView())

        log_ch = await get_log_channel(interaction.client, guild)
        if log_ch:
            log_e = discord.Embed(title="Ticket ouvert", color=VERT, timestamp=datetime.utcnow())
            log_e.set_thumbnail(url=member.display_avatar.url)
            log_e.add_field(name="Membre", value=f"`{member}`", inline=True)
            log_e.add_field(name="Type", value=f"`{t['nom']}`", inline=True)
            log_e.add_field(name="Salon", value=ch.mention, inline=True)
            log_e.set_footer(text="Logs Tickets")
            await log_ch.send(embed=log_e)

        await interaction.response.send_message(f"Ticket cree : {ch.mention}", ephemeral=True)


class TicketView(discord.ui.View):
    def __init__(self, types):
        super().__init__(timeout=None)
        if types:
            self.add_item(TicketSelect(types))


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_ch = await get_log_channel(interaction.client, interaction.guild)
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


# ─── Settings View ─────────────────────────────────────────────────────────────

class SettingsView(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bot = bot
        self.msg = None

        select = discord.ui.Select(
            placeholder="Que veux-tu configurer ?",
            options=[
                discord.SelectOption(label="Ajouter un type de ticket", value="ajouter", description="Creer un nouveau type de ticket"),
                discord.SelectOption(label="Supprimer un type de ticket", value="supprimer", description="Retirer un type de ticket existant"),
                discord.SelectOption(label="Modifier un type de ticket", value="modifier", description="Changer nom, description, emoji ou categorie"),
                discord.SelectOption(label="Ajouter un role staff", value="add_role", description="Les membres avec ce role verront les tickets"),
                discord.SelectOption(label="Retirer un role staff", value="del_role", description="Retirer un role staff"),
                discord.SelectOption(label="Definir le salon de logs", value="logs", description="Choisir le salon pour les logs de tickets"),
                discord.SelectOption(label="Voir la configuration actuelle", value="voir", description="Affiche tous les parametres"),
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def rafraichir(self):
        config = load_config(self.ctx.guild.id)
        e = self.build_embed(config)
        if self.msg:
            await self.msg.edit(embed=e, view=self)

    def build_embed(self, config):
        e = discord.Embed(
            title="Parametres des tickets",
            description="Utilise le menu pour tout configurer.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        types = config.get("types", [])
        if types:
            val = "\n".join([f"**{t['nom']}** — {t['description'][:40]}..." for t in types])
        else:
            val = "Aucun type configure"
        e.add_field(name=f"Types de tickets ({len(types)})", value=val, inline=False)

        roles = config.get("staff_roles", [])
        if roles:
            val_roles = "\n".join([f"<@&{r}>" for r in roles])
        else:
            val_roles = "Aucun role staff configure"
        e.add_field(name="Roles staff", value=val_roles, inline=False)

        log_id = config.get("log_channel")
        e.add_field(name="Salon de logs", value=f"<#{log_id}>" if log_id else "Non configure", inline=False)
        e.set_footer(text=f"Demande par {self.ctx.author.name}")
        return e

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Ce n'est pas ton menu !", ephemeral=True)

        await interaction.response.defer()
        choix = interaction.data["values"][0]
        config = load_config(self.ctx.guild.id)

        if choix == "ajouter":
            msg = await self.ctx.channel.send("Quel est le **nom** de ce type de ticket ?")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            nom = rep.content

            msg = await self.ctx.channel.send("Quelle est la **description** de ce type de ticket ?")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            description = rep.content

            msg = await self.ctx.channel.send("Quel **emoji** pour ce type ? (envoie `skip` pour ignorer)")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            emoji = None if rep.content.lower() == "skip" else rep.content

            msg = await self.ctx.channel.send("Quel est le **nom exact de la categorie** Discord pour ce type ?")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            categorie = rep.content

            config["types"].append({
                "nom": nom,
                "description": description,
                "emoji": emoji,
                "categorie": categorie
            })
            save_config(self.ctx.guild.id, config)
            await self.ctx.channel.send(f"Type **{nom}** ajoute !", delete_after=3)
            await self.rafraichir()

        elif choix == "supprimer":
            types = config.get("types", [])
            if not types:
                return await self.ctx.channel.send("Aucun type a supprimer !", delete_after=3)
            liste = "\n".join([f"`{i+1}` — {t['nom']}" for i, t in enumerate(types)])
            msg = await self.ctx.channel.send(f"Quel type supprimer ? (envoie le numero)\n{liste}")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            try:
                index = int(rep.content) - 1
                removed = config["types"].pop(index)
                save_config(self.ctx.guild.id, config)
                await self.ctx.channel.send(f"Type **{removed['nom']}** supprime !", delete_after=3)
                await self.rafraichir()
            except (ValueError, IndexError):
                await self.ctx.channel.send("Numero invalide !", delete_after=3)

        elif choix == "modifier":
            types = config.get("types", [])
            if not types:
                return await self.ctx.channel.send("Aucun type a modifier !", delete_after=3)
            liste = "\n".join([f"`{i+1}` — {t['nom']}" for i, t in enumerate(types)])
            msg = await self.ctx.channel.send(f"Quel type modifier ? (envoie le numero)\n{liste}")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            try:
                index = int(rep.content) - 1
                t = config["types"][index]
            except (ValueError, IndexError):
                return await self.ctx.channel.send("Numero invalide !", delete_after=3)

            msg = await self.ctx.channel.send(f"Nouveau **nom** ? (actuel : `{t['nom']}`) — envoie `skip` pour garder")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.content.lower() != "skip": t["nom"] = rep.content

            msg = await self.ctx.channel.send(f"Nouvelle **description** ? (actuel : `{t['description'][:50]}`) — envoie `skip` pour garder")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.content.lower() != "skip": t["description"] = rep.content

            msg = await self.ctx.channel.send(f"Nouvel **emoji** ? (actuel : `{t.get('emoji', 'aucun')}`) — envoie `skip` pour garder")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.content.lower() != "skip": t["emoji"] = rep.content

            msg = await self.ctx.channel.send(f"Nouvelle **categorie** ? (actuel : `{t['categorie']}`) — envoie `skip` pour garder")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.content.lower() != "skip": t["categorie"] = rep.content

            config["types"][index] = t
            save_config(self.ctx.guild.id, config)
            await self.ctx.channel.send(f"Type **{t['nom']}** modifie !", delete_after=3)
            await self.rafraichir()

        elif choix == "add_role":
            msg = await self.ctx.channel.send("Mentionne le **role staff** a ajouter")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.role_mentions:
                role = rep.role_mentions[0]
                if role.id not in config["staff_roles"]:
                    config["staff_roles"].append(role.id)
                    save_config(self.ctx.guild.id, config)
                    await self.ctx.channel.send(f"Role **{role.name}** ajoute !", delete_after=3)
                else:
                    await self.ctx.channel.send("Ce role est deja dans la liste !", delete_after=3)
                await self.rafraichir()
            else:
                await self.ctx.channel.send("Aucun role mentionne !", delete_after=3)

        elif choix == "del_role":
            roles = config.get("staff_roles", [])
            if not roles:
                return await self.ctx.channel.send("Aucun role a retirer !", delete_after=3)
            liste = "\n".join([f"`{i+1}` — <@&{r}>" for i, r in enumerate(roles)])
            msg = await self.ctx.channel.send(f"Quel role retirer ? (envoie le numero)\n{liste}")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            try:
                index = int(rep.content) - 1
                config["staff_roles"].pop(index)
                save_config(self.ctx.guild.id, config)
                await self.ctx.channel.send("Role retire !", delete_after=3)
                await self.rafraichir()
            except (ValueError, IndexError):
                await self.ctx.channel.send("Numero invalide !", delete_after=3)

        elif choix == "logs":
            msg = await self.ctx.channel.send("Mentionne le **salon de logs** pour les tickets")
            rep = await attendre(self.ctx, self.bot, msg)
            if not rep: return
            if rep.channel_mentions:
                ch = rep.channel_mentions[0]
                config["log_channel"] = ch.id
                save_config(self.ctx.guild.id, config)
                await self.ctx.channel.send(f"Salon de logs defini sur {ch.mention} !", delete_after=3)
                await self.rafraichir()
            else:
                await self.ctx.channel.send("Aucun salon mentionne !", delete_after=3)

        elif choix == "voir":
            await self.rafraichir()


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        await ctx.message.delete()
        config = load_config(ctx.guild.id)
        types = config.get("types", [])

        if not types:
            return await ctx.send("Aucun type de ticket configure ! Utilise `+ticket settings` pour configurer.")

        e = discord.Embed(
            title="Support & Tickets",
            description="Selectionnez le type de ticket dans le menu ci-dessous.\nNotre equipe te repondra dans les plus brefs delais.",
            color=get_color(),
            timestamp=datetime.utcnow()
        )
        if ctx.guild.icon:
            e.set_thumbnail(url=ctx.guild.icon.url)
        e.set_footer(text="Systeme de tickets")
        await ctx.send(embed=e, view=TicketView(types))

    @commands.group(name="ticket", invoke_without_command=False)
    async def ticket_group(self, ctx):
        pass

    @ticket_group.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def ticket_settings(self, ctx):
        await ctx.message.delete()
        config = load_config(ctx.guild.id)
        view = SettingsView(ctx, self.bot)
        e = view.build_embed(config)
        msg = await ctx.send(embed=e, view=view)
        view.msg = msg

    @commands.command(name="close")
    @commands.has_permissions(manage_channels=True)
    async def close(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.send(embed=discord.Embed(
                title="Erreur",
                description="Cette commande s'utilise uniquement dans un ticket !",
                color=ROUGE
            ))
        log_ch = await get_log_channel(self.bot, ctx.guild)
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
        await ctx.channel.delete()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(CloseTicketView())


async def setup(bot):
    await bot.add_cog(Tickets(bot))